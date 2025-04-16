from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.contrib.auth.views import LoginView
from django.contrib.auth import authenticate, login
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from datetime import datetime
import os
import urllib.parse
import openpyxl
import pytz
from django.utils.text import slugify
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm, inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from .forms import ProductoForm, TransaccionForm, ActaEntregaForm, DepartamentoForm, ModificarDepartamentoForm, EliminarDepartamentoForm, CustomUserCreationForm, CustomUserEditForm, SearchUserForm
from .models import Producto, Transaccion, ActaEntrega, Funcionario, Departamento, Responsable, CustomUser
from django.utils.safestring import mark_safe
import json
from django.http import JsonResponse

# Funciones auxiliares
def limpiar_sesion_productos_salida(request):
    """Limpia la variable de sesión productos_salida si existe"""
    if 'productos_salida' in request.session:
        del request.session['productos_salida']

def paginar_resultados(request, objetos, items_por_pagina=20):
    """Aplica paginación a una lista de objetos"""
    paginator = Paginator(objetos, items_por_pagina)
    page = request.GET.get('page')
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    return page_obj

def generar_pdf_acta(actas, disposition='attachment'):
    """Genera un PDF para un acta de entrega"""
    try:
        print("Generando PDF para las actas...")
        acta = actas.first()
        if not acta:
            raise ValueError("No se encontraron actas para generar el PDF.")

        productos_salida = [
            {
                'codigo_barra': item.producto.codigo_barra,
                'descripcion': item.producto.descripcion,
                'numero_siscom': item.numero_siscom or '',
                'cantidad': item.cantidad,
                'observacion': item.observacion or '',
            } for item in actas
        ]
        print(f"Productos para el PDF: {productos_salida}")

        response = HttpResponse(content_type='application/pdf')
        filename = f"Acta_Entrega_Nro_{acta.numero_acta}.pdf"
        encoded_filename = urllib.parse.quote(filename)
        response['Content-Disposition'] = f'{disposition}; filename="{encoded_filename}"'
        response['Content-Type'] = 'application/pdf; charset=utf-8'

        doc = SimpleDocTemplate(response, pagesize=letter, leftMargin=0.75*inch, rightMargin=0.75*inch,
                            topMargin=0.5*inch, bottomMargin=0.5*inch)
        styles = getSampleStyleSheet()

        # Definir estilos personalizados en un diccionario separado
        custom_styles = {
            'TitleCustom': ParagraphStyle(name='TitleCustom', fontName='Helvetica-Bold', fontSize=14, alignment=1, spaceAfter=10, leading=16),
            'NormalBold': ParagraphStyle(name='NormalBold', fontName='Helvetica-Bold', fontSize=10, spaceAfter=4, leading=12),
            'NormalCustom': ParagraphStyle(name='NormalCustom', fontName='Helvetica-Bold', fontSize=10, spaceAfter=4, leading=12),
            'ActaNumber': ParagraphStyle(name='ActaNumber', fontName='Helvetica-Bold', fontSize=20, alignment=1, textColor=colors.black, spaceAfter=0, leading=24),
            'Signature': ParagraphStyle(name='Signature', fontName='Times-Roman', fontSize=10, alignment=1, spaceBefore=10, spaceAfter=4, leading=12),
            'SignatureTitle': ParagraphStyle(name='SignatureTitle', fontName='Times-Bold', fontSize=10, alignment=1, spaceBefore=4, spaceAfter=4, leading=12),
            'SignatureCargo': ParagraphStyle(name='SignatureCargo', fontName='Times-Italic', fontSize=9, alignment=1, spaceBefore=2, spaceAfter=2, leading=11),
            'TableCell': ParagraphStyle(name='TableCell', fontName='Helvetica-Bold', fontSize=9, leading=11, wordWrap='CJK'),
        }

        elements = []
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'images', 'seremi_logo.png')
        print(f"Ruta del logo: {logo_path}")
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=3*cm, height=3*cm)
            print("Logo cargado correctamente.")
        else:
            print("Logo no encontrado, usando texto alternativo.")
            logo = Paragraph("Logo no encontrado", custom_styles['NormalCustom'])
        logo.hAlign = 'LEFT'

        acta_number = Paragraph(f"N° {acta.numero_acta}", custom_styles['ActaNumber'])
        acta_number_table = Table([[acta_number]], colWidths=[1.5*inch], rowHeights=[0.5*inch])
        acta_number_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 20),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ]))

        header_table = Table([[logo, acta_number_table]], colWidths=[3*inch, 4.5*inch])
        header_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('ALIGN', (0, 0), (0, 0), 'LEFT'), ('ALIGN', (1, 0), (1, 0), 'RIGHT')]))

        # Asegurarse de que los textos estén codificados correctamente
        departamento_text = acta.departamento.encode('utf-8').decode('utf-8')
        # Usar el nombre del responsable desde el modelo Responsable
        responsable_text = acta.responsable.nombre.encode('utf-8').decode('utf-8') if acta.responsable else 'No especificado'
        # Usar solo el nombre del generador (sin RUT)
        generador_text = acta.generador.nombre.encode('utf-8').decode('utf-8') if acta.generador else 'No especificado'
        fecha_text = acta.fecha.strftime('%d-%m-%Y')
        print(f"Textos para el PDF - Departamento: {departamento_text}, Responsable: {responsable_text}, Generador: {generador_text}, Fecha: {fecha_text}")

        elements.extend([
            header_table,
            Spacer(1, 0.2*cm),
            Paragraph("ACTA DE ENTREGA MATERIALES O INSUMOS", custom_styles['TitleCustom']),
            Spacer(1, 0.3*cm),
            Paragraph(f"En Temuco con fecha {fecha_text} se procede a realizar la entrega de los siguientes artículos a:", custom_styles['NormalCustom']),
            Spacer(1, 0.2*cm),
            Paragraph(f"Sección: {departamento_text}", custom_styles['NormalCustom']),
            Spacer(1, 0.1*cm),
            Paragraph(f"Responsable: {responsable_text}", custom_styles['NormalCustom']),
            Spacer(1, 0.5*cm),
            Paragraph("Datos de Productos", custom_styles['NormalBold']),
            Spacer(1, 0.2*cm)
        ])

        data = [['Descripción', 'Nro. SISCOM', 'Cantidad', 'Observación']]
        for item in productos_salida:
            descripcion_text = item['descripcion'].encode('utf-8').decode('utf-8')
            numero_siscom_text = item['numero_siscom'].encode('utf-8').decode('utf-8')
            observacion_text = (item['observacion'] or '-').replace('\n', '<br/>').encode('utf-8').decode('utf-8')
            data.append([descripcion_text, numero_siscom_text, str(item['cantidad']), Paragraph(observacion_text, custom_styles['TableCell'])])
            print(f"Fila de la tabla: {descripcion_text}, {numero_siscom_text}, {item['cantidad']}, {observacion_text}")

        table = Table(data, colWidths=[1.8*inch, 2.0*inch, 0.8*inch, 2.4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 1), (-1, -1), 'TOP'),
        ]))

        responsable_lower = responsable_text.lower()
        cargo = "SECRETARIA DEL DEPARTAMENTO" if 'secretaria' in responsable_lower else "JEFE DEL DEPARTAMENTO" if 'jefe' in responsable_lower or 'jefatura' in responsable_lower else "RESPONSABLE DEL DEPARTAMENTO"

        firma_table = Table([
            [Paragraph(f"{generador_text}", custom_styles['Signature']), Paragraph(f"Sr./Sra. {responsable_text}", custom_styles['Signature'])],
            [Paragraph("ENCARGADO BODEGA", custom_styles['SignatureTitle']), Paragraph("RECEPCIONA CONFORME", custom_styles['SignatureTitle'])],
            ['', Paragraph(cargo, custom_styles['SignatureCargo'])],
            [Paragraph("_____________________________", custom_styles['Signature']), Paragraph("_____________________________", custom_styles['Signature'])],
        ], colWidths=[3*inch, 3*inch])
        firma_table.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('FONTNAME', (0, 0), (-1, -1), 'Times-Roman'), ('FONTSIZE', (0, 0), (-1, -1), 10), ('LEADING', (0, 0), (-1, -1), 12)]))

        elements.extend([table, Spacer(1, 4*inch), firma_table])
        print("Construyendo el PDF...")
        doc.build(elements)
        print("PDF generado correctamente.")
        return response
    except Exception as e:
        print(f"Error al generar el PDF: {str(e)}")
        response = HttpResponse(f"Error al generar el PDF: {str(e)}", content_type='text/plain')
        response.status_code = 500
        return response
    
def exportar_excel(request, datos, nombre_base, columnas, campos):
    """Genera y devuelve un archivo Excel"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = nombre_base
    ws.append(columnas)

    for col in range(1, len(columnas) + 1):
        cell = ws.cell(row=1, column=col)
        cell.font = openpyxl.styles.Font(bold=True)
        cell.fill = openpyxl.styles.PatternFill(start_color="D3D3D3", end_color="D3D3D3", fill_type="solid")
        cell.alignment = openpyxl.styles.Alignment(horizontal='center')

    for idx, item in enumerate(datos, start=2):
        fila = []
        for campo in campos:
            valor = getattr(item, campo) if hasattr(item, campo) else item.get(campo, '-')
            if campo == 'fecha' and isinstance(valor, datetime):
                valor = valor.strftime('%d-%m-%Y %H:%M')
            fila.append(valor)
        ws.append(fila)

    for col in ws.columns:
        max_length = max(len(str(cell.value)) for cell in col if cell.value)
        column_letter = col[0].column_letter
        if column_letter == 'A':
            ws.column_dimensions[column_letter].width = 20
        else:
            ws.column_dimensions[column_letter].width = max_length + 2

    fecha = datetime.now().strftime('%Y-%m-%d')
    filename = f"{nombre_base}_{fecha}.xlsx"
    encoded_filename = urllib.parse.quote(filename)
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{encoded_filename}"'
    wb.save(response)
    return response

# Vistas
@login_required
def home(request):
    # Limpiar la sesión de productos de salida
    limpiar_sesion_productos_salida(request)

    # Calcular métricas para el gráfico de dona
    # Total de productos con stock mayor a 0
    total_productos = Producto.objects.filter(stock__gt=0).count()
    
    if total_productos > 0:
        # Productos con stock bajo (1-10)
        stock_bajo = Producto.objects.filter(stock__gte=1, stock__lte=10).count()
        # Productos con stock medio (11-50)
        stock_medio = Producto.objects.filter(stock__gt=10, stock__lte=50).count()
        # Productos con stock alto (>50)
        stock_alto = Producto.objects.filter(stock__gt=50).count()

        # Calcular porcentajes (evitando división por cero)
        porcentaje_bajo = (stock_bajo / total_productos * 100) if total_productos > 0 else 0
        porcentaje_medio = (stock_medio / total_productos * 100) if total_productos > 0 else 0
        porcentaje_alto = (stock_alto / total_productos * 100) if total_productos > 0 else 0

        # Redondear los porcentajes a 2 decimales
        porcentaje_bajo = round(porcentaje_bajo, 2)
        porcentaje_medio = round(porcentaje_medio, 2)
        porcentaje_alto = round(porcentaje_alto, 2)

        # Ajustar los porcentajes para que sumen exactamente 100%
        suma_porcentajes = porcentaje_bajo + porcentaje_medio + porcentaje_alto
        if suma_porcentajes != 100.0:
            # Ajustar el porcentaje más grande para compensar el error de redondeo
            if porcentaje_bajo >= porcentaje_medio and porcentaje_bajo >= porcentaje_alto:
                porcentaje_bajo = porcentaje_bajo + (100.0 - suma_porcentajes)
            elif porcentaje_medio >= porcentaje_bajo and porcentaje_medio >= porcentaje_alto:
                porcentaje_medio = porcentaje_medio + (100.0 - suma_porcentajes)
            else:
                porcentaje_alto = porcentaje_alto + (100.0 - suma_porcentajes)
    else:
        stock_bajo = stock_medio = stock_alto = 0
        porcentaje_bajo = porcentaje_medio = porcentaje_alto = 0

    # Preparar los datos para el gráfico de dona en formato JSON
    chart_data = {
        'totalProductos': total_productos,
        'porcentajes': [porcentaje_bajo, porcentaje_medio, porcentaje_alto]
    }

    # Preparar el contexto para la plantilla
    context = {
        'total_productos': total_productos,
        'stock_bajo': stock_bajo,
        'stock_medio': stock_medio,
        'stock_alto': stock_alto,
        'porcentaje_bajo': porcentaje_bajo,
        'porcentaje_medio': porcentaje_medio,
        'porcentaje_alto': porcentaje_alto,
        'chart_data_json': mark_safe(json.dumps(chart_data))  # Usar mark_safe para asegurar que el JSON sea seguro para JavaScript
    }
    return render(request, 'accounts/home.html', context)

class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'

    def post(self, request, *args, **kwargs):
        rut = request.POST.get('username')  # Cambiamos 'username' a 'rut' en el formulario
        password = request.POST.get('password')
        user = authenticate(request, rut=rut, password=password)  # Usamos 'rut' para autenticar
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(self.get_success_url())
        messages.error(request, 'Credenciales inválidas')
        return self.render_to_response(self.get_context_data())

    def get_success_url(self):
        return '/'

@login_required
def registrar_producto(request):
    limpiar_sesion_productos_salida(request)
    if not request.user.has_perm('accounts.can_edit'):
        messages.error(request, 'No tienes permiso para registrar productos.')
        return redirect('home')
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save()
            if producto.stock > 0:
                Transaccion(
                    producto=producto,
                    tipo='entrada',
                    cantidad=producto.stock,
                    fecha=datetime.now(pytz.UTC),
                    rut_proveedor=producto.rut_proveedor or '',
                    guia_despacho=producto.guia_despacho or '',
                    numero_factura=producto.numero_factura or '',
                    orden_compra=producto.orden_compra or '',
                    observacion='Stock inicial al registrar el producto'
                ).save()
            messages.success(request, 'Producto registrado con éxito.')
            return redirect('home')
        messages.error(request, 'Error al registrar el producto. Verifica los datos.')
    else:
        form = ProductoForm()
    return render(request, 'accounts/registrar_producto.html', {'form': form})

@login_required
def listar_productos(request):
    limpiar_sesion_productos_salida(request)
    params = request.POST if request.method == 'POST' else request.GET
    query_codigo = params.get('codigo_barra', '')
    query_descripcion = params.get('descripcion', '')
    query_categoria = params.get('categoria', '')

    productos = Producto.objects.all().order_by('codigo_barra')
    if query_codigo:
        productos = productos.filter(codigo_barra=query_codigo)
    if query_descripcion:
        productos = productos.filter(descripcion__icontains=query_descripcion)
    if query_categoria and query_categoria != 'Todas':
        productos = productos.filter(categoria=query_categoria)

    if request.method == 'POST' and 'exportar_excel' in request.POST:
        columnas = ['Código de Barra', 'Nombre del Producto', 'Categoría', 'Stock Actual']
        campos = ['codigo_barra', 'descripcion', 'categoria', 'stock']
        return exportar_excel(request, productos, "Productos", columnas, campos)

    page_obj = paginar_resultados(request, productos)
    context = {
        'page_obj': page_obj,
        'query_codigo': query_codigo,
        'query_descripcion': query_descripcion,
        'query_categoria': query_categoria,
        'categorias': [('', 'Todas')] + Producto.CATEGORIAS,
    }
    return render(request, 'accounts/listar_productos.html', context)

@login_required
def agregar_stock(request):
    limpiar_sesion_productos_salida(request)
    if not request.user.has_perm('accounts.can_edit'):
        messages.error(request, 'No tienes permiso para agregar stock.')
        return redirect('home')
    productos = Producto.objects.all().order_by('codigo_barra')
    query_codigo = request.GET.get('codigo_barra', '')
    query_descripcion = request.GET.get('descripcion', '')

    if query_codigo:
        productos = productos.filter(codigo_barra=query_codigo)
    if query_descripcion:
        productos = productos.filter(descripcion__icontains=query_descripcion)

    page_obj = paginar_resultados(request, productos)
    return render(request, 'accounts/agregar_stock.html', {
        'page_obj': page_obj,
        'query_codigo': query_codigo,
        'query_descripcion': query_descripcion,
    })

@login_required
def agregar_stock_detalle(request, codigo_barra):
    limpiar_sesion_productos_salida(request)
    if not request.user.has_perm('accounts.can_edit'):
        messages.error(request, 'No tienes permiso para agregar stock.')
        return redirect('home')
    try:
        producto = Producto.objects.get(codigo_barra=codigo_barra)
    except Producto.DoesNotExist:
        messages.error(request, 'Producto no encontrado.')
        return redirect('agregar-stock')

    if request.method == 'POST':
        form = TransaccionForm(request.POST)
        if form.is_valid():
            transaccion = form.save(commit=False)
            transaccion.producto = producto
            transaccion.tipo = 'entrada'
            transaccion.rut_proveedor = form.cleaned_data['rut_proveedor'] or ''
            transaccion.guia_despacho = form.cleaned_data['guia_despacho'] or ''
            transaccion.numero_factura = form.cleaned_data['numero_factura'] or ''
            transaccion.orden_compra = form.cleaned_data['orden_compra'] or ''
            transaccion.save()

            producto.stock += form.cleaned_data['cantidad']
            producto.rut_proveedor = form.cleaned_data['rut_proveedor'] or ''
            producto.guia_despacho = form.cleaned_data['guia_despacho'] or ''
            producto.numero_factura = form.cleaned_data['numero_factura'] or ''
            producto.orden_compra = form.cleaned_data['orden_compra'] or ''
            producto.save()

            messages.success(request, f'Stock agregado exitosamente. Nueva cantidad: {producto.stock}')
            return redirect('agregar-stock')
        messages.error(request, 'Error al agregar stock. Verifica los datos.')
    else:
        form = TransaccionForm()
    return render(request, 'accounts/agregar_stock_detalle.html', {'form': form, 'producto': producto})

@login_required
def salida_productos(request):
    if not request.user.has_perm('accounts.can_edit'):
        messages.error(request, 'No tienes permiso para realizar salidas de productos.')
        return redirect('home')
    productos_salida = request.session.get('productos_salida', [])
    productos = Producto.objects.all().order_by('codigo_barra')
    query_codigo = request.GET.get('codigo_barra', '')
    query_descripcion = request.GET.get('descripcion', '')

    if query_codigo:
        productos = productos.filter(codigo_barra=query_codigo)
    if query_descripcion:
        productos = productos.filter(descripcion__icontains=query_descripcion)

    page_obj = paginar_resultados(request, productos)

    if request.method == 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.POST.get('action') == 'update_data':
            codigo_barra = request.POST.get('codigo_barra')
            for item in productos_salida:
                if item['codigo_barra'] == codigo_barra:
                    item.update({
                        'numero_siscom': request.POST.get('numero_siscom', ''),
                        'cantidad': request.POST.get('cantidad', ''),
                        'observacion': request.POST.get('observacion', '')
                    })
                    break
            request.session['productos_salida'] = productos_salida
            request.session.modified = True
            return JsonResponse({'success': True})

        elif 'agregar_producto' in request.POST:
            codigo_barra = request.POST.get('codigo_barra')
            try:
                producto = Producto.objects.get(codigo_barra=codigo_barra)
                if any(item['codigo_barra'] == codigo_barra for item in productos_salida):
                    messages.error(request, 'Este producto ya está en la lista de salida.')
                elif producto.stock == 0:
                    messages.error(request, 'No se puede retirar este producto porque no tiene stock.')
                else:
                    productos_salida.append({
                        'codigo_barra': producto.codigo_barra,
                        'descripcion': producto.descripcion,
                        'stock': producto.stock,
                        'numero_siscom': '',
                        'cantidad': '',
                        'observacion': '',
                    })
                    request.session['productos_salida'] = productos_salida
                    request.session.modified = True
                    messages.success(request, 'Producto agregado a la lista de salida.')
            except Producto.DoesNotExist:
                messages.error(request, 'Producto no encontrado.')
            return redirect('salida-productos')

        elif 'eliminar_producto' in request.POST:
            codigo_barra = request.POST.get('codigo_barra')
            productos_salida = [item for item in productos_salida if item['codigo_barra'] != codigo_barra]
            request.session['productos_salida'] = productos_salida
            request.session.modified = True
            return JsonResponse({'success': True}) if request.headers.get('X-Requested-With') == 'XMLHttpRequest' else redirect('salida-productos')

        elif 'siguiente' in request.POST:
            if not productos_salida:
                messages.error(request, 'Debes agregar al menos un producto para continuar.')
                return redirect('salida-productos')
            for item in productos_salida:
                if not item['numero_siscom'] or not item['numero_siscom'].isdigit():
                    messages.error(request, f"El Número de SISCOM para el producto {item['codigo_barra']} debe ser un número entero.")
                    return redirect('salida-productos')
                try:
                    cantidad = int(item['cantidad'])
                    if cantidad <= 0:
                        messages.error(request, f"La cantidad para el producto {item['codigo_barra']} debe ser un número positivo.")
                        return redirect('salida-productos')
                    if cantidad > item['stock']:
                        messages.error(request, f"La cantidad a retirar ({cantidad}) para el producto {item['codigo_barra']} no puede superar el stock actual ({item['stock']}).")
                        return redirect('salida-productos')
                    item['cantidad'] = cantidad
                except ValueError:
                    messages.error(request, f"La cantidad para el producto {item['codigo_barra']} debe ser un número entero.")
                    return redirect('salida-productos')
            request.session['productos_salida'] = productos_salida
            request.session.modified = True
            return redirect('salida-productos-seleccion')

    return render(request, 'accounts/salida_productos.html', {
        'page_obj': page_obj,
        'query_codigo': query_codigo,
        'query_descripcion': query_descripcion,
        'productos_salida': productos_salida,
    })

@login_required
def salida_productos_seleccion(request):
    if not request.user.has_perm('accounts.can_edit'):
        messages.error(request, 'No tienes permiso para realizar salidas de productos.')
        return redirect('home')
    productos_salida = request.session.get('productos_salida', [])
    if not productos_salida:
        messages.error(request, 'No hay productos seleccionados para la salida.')
        return redirect('salida-productos')

    if request.method == 'POST':
        form = ActaEntregaForm(request.POST)
        print(f"Formulario recibido: {request.POST}")
        if form.is_valid():
            print("Formulario válido. Procesando la salida...")
            print(f"Datos limpiados - Departamento: {form.cleaned_data['departamento']}, Responsable: {form.cleaned_data['responsable']}")
            try:
                # Validar el stock disponible para cada producto calculando el saldo real
                for item in productos_salida:
                    print(f"Validando stock para el producto: {item}")
                    producto = Producto.objects.get(codigo_barra=item['codigo_barra'])
                    cantidad = int(item['cantidad'] or 0)

                    # Calcular el saldo real basado en transacciones y actas
                    transacciones = Transaccion.objects.filter(producto=producto).order_by('fecha')
                    actas = ActaEntrega.objects.filter(producto=producto).order_by('fecha')

                    # Crear una lista de eventos combinada (entradas y salidas)
                    eventos = []
                    for transaccion in transacciones.filter(tipo='entrada'):
                        eventos.append({
                            'tipo': 'entrada',
                            'fecha': transaccion.fecha,
                            'entrada': transaccion.cantidad,
                            'salida': 0,
                        })
                    for transaccion in transacciones.filter(tipo='salida'):
                        if transaccion.acta_entrega:
                            eventos.append({
                                'tipo': 'salida',
                                'fecha': transaccion.fecha,
                                'entrada': 0,
                                'salida': transaccion.cantidad,
                            })
                    eventos.sort(key=lambda x: x['fecha'])

                    # Calcular el saldo
                    saldo = 0
                    for evento in eventos:
                        if evento['tipo'] == 'entrada':
                            saldo += evento['entrada']
                        else:
                            saldo -= evento['salida']

                    # Si el saldo calculado no coincide con el stock actual, corregirlo
                    if saldo != producto.stock:
                        messages.warning(request, f'El stock del producto {producto.descripcion} (Código: {producto.codigo_barra}) estaba desincronizado. Stock actual: {producto.stock}, Saldo calculado: {saldo}.')
                        producto.stock = saldo
                        producto.save()
                        messages.info(request, f'El stock del producto {producto.descripcion} ha sido corregido a {saldo}.')

                    print(f"Producto: {producto.descripcion}, Stock actual (corregido): {producto.stock}, Cantidad solicitada: {cantidad}")
                    if producto.stock - cantidad < 0:
                        messages.error(request, f'No hay suficiente stock para {producto.descripcion} (Código: {producto.codigo_barra}). Stock actual: {producto.stock}, Solicitado: {cantidad}.')
                        return redirect('salida-productos-seleccion')

                # Generar un nuevo número de acta
                ultimo_acta = ActaEntrega.objects.order_by('-numero_acta').first()
                numero_acta = 1 if not ultimo_acta else ultimo_acta.numero_acta + 1
                print(f"Nuevo número de acta: {numero_acta}")

                # Obtener el objeto Responsable del formulario
                responsable = form.cleaned_data['responsable']

                # Crear las actas y transacciones
                for item in productos_salida:
                    print(f"Creando acta para el producto: {item}")
                    producto = Producto.objects.get(codigo_barra=item['codigo_barra'])
                    cantidad = int(item['cantidad'])
                    acta = ActaEntrega(
                        numero_acta=numero_acta,
                        departamento=form.cleaned_data['departamento'],
                        responsable=responsable,  # Asignamos el objeto Responsable
                        generador=request.user,  # Asignamos el usuario autenticado
                        producto=producto,
                        cantidad=cantidad,
                        numero_siscom=item['numero_siscom'],  # Tomamos el valor de productos_salida
                        observacion=item['observacion'],  # Tomamos el valor de productos_salida
                    )
                    acta.save()
                    print(f"Acta creada: N°{acta.numero_acta}, Producto: {producto.descripcion}, Cantidad: {cantidad}")

                    # Crear una transacción de salida asociada al acta con fecha explícita
                    Transaccion.objects.create(
                        producto=producto,
                        tipo='salida',
                        cantidad=cantidad,
                        acta_entrega=acta,
                        fecha=datetime.now(pytz.UTC),  # Aseguramos que la transacción tenga una fecha
                        observacion=f"Salida asociada al Acta N°{numero_acta}"
                    )
                    print(f"Transacción creada: Tipo: salida, Cantidad: {cantidad}")

                    # Actualizar el stock del producto
                    producto.stock -= cantidad
                    producto.save()
                    print(f"Stock actualizado: {producto.descripcion}, Nuevo stock: {producto.stock}")

                # Generar el PDF del acta
                actas = ActaEntrega.objects.filter(numero_acta=numero_acta)
                print(f"Actas para el PDF: {list(actas)}")

                response = generar_pdf_acta(actas)
                limpiar_sesion_productos_salida(request)
                messages.success(request, f'Acta de entrega N°{numero_acta} generada correctamente.')
                return response

            except Exception as e:
                print(f"Error al procesar el acta: {str(e)}")
                messages.error(request, f'Error al procesar el acta: {str(e)}')
                return redirect('salida-productos-seleccion')
        else:
            print("Formulario no válido.")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error en el campo '{form.fields[field].label}': {error}")
            messages.error(request, 'Error al generar el acta. Por favor, verifica los datos e intenta de nuevo.')
    else:
        form = ActaEntregaForm()

    return render(request, 'accounts/salida_productos_seleccion.html', {'form': form, 'productos_salida': productos_salida})

@login_required
def listar_actas(request):
    """Vista para listar las actas de entrega."""
    limpiar_sesion_productos_salida(request)
    actas = ActaEntrega.objects.all().order_by('-numero_acta')
    query_numero_acta = request.GET.get('numero_acta', '')
    query_responsable = request.GET.get('responsable', '')

    # Aplicar filtros
    if query_numero_acta:
        try:
            actas = actas.filter(numero_acta__startswith=int(query_numero_acta))
        except ValueError:
            messages.error(request, 'El número de acta debe ser un valor numérico.')
    if query_responsable:
        actas = actas.filter(responsable__nombre__icontains=query_responsable)

    # Eliminar duplicados por número de acta y ordenar
    actas_dict = {acta.numero_acta: acta for acta in actas}
    actas_lista = sorted(actas_dict.values(), key=lambda x: x.numero_acta, reverse=True)

    # Paginar las actas (20 por página)
    page_obj = paginar_resultados(request, actas_lista, items_por_pagina=20)

    # Renderizar la página completa
    return render(request, 'accounts/listar_actas.html', {
        'actas': page_obj,
        'query_numero_acta': query_numero_acta,
        'query_responsable': query_responsable,
    })

@login_required
def ver_acta_pdf(request, numero_acta, disposition):
    actas = ActaEntrega.objects.filter(numero_acta=numero_acta)
    if not actas.exists():
        return HttpResponse("Acta no encontrada.", status=404)
    return generar_pdf_acta(actas, disposition)

@login_required
def bincard_buscar(request):
    limpiar_sesion_productos_salida(request)
    if request.method == 'POST':
        codigo_barra = request.POST.get('codigo_barra', '').strip()
        if not codigo_barra:
            messages.error(request, 'Por favor, ingrese un código de barra.')
        elif not codigo_barra.isdigit():
            messages.error(request, 'El código de barra debe contener solo números.')
        else:
            try:
                Producto.objects.get(codigo_barra=codigo_barra)
                return redirect('bincard-historial', codigo_barra=codigo_barra)
            except Producto.DoesNotExist:
                messages.error(request, f'No se encontró un producto con el código de barra {codigo_barra}. '
                                f'Puedes <a href="/accounts/registrar-producto/">registrar un nuevo producto</a>.')
        return render(request, 'accounts/bincard_buscar.html')
    return render(request, 'accounts/bincard_buscar.html')

@login_required
def buscar_codigos_barra(request):
    term = request.GET.get('term', '').strip()
    if not term:
        return JsonResponse([], safe=False)
    productos = Producto.objects.filter(codigo_barra__startswith=term).order_by('codigo_barra')[:10]
    codigos = [{'label': f"{p.codigo_barra} - {p.descripcion}", 'value': p.codigo_barra} for p in productos]
    return JsonResponse(codigos, safe=False)

@login_required
def bincard_historial(request, codigo_barra):
    limpiar_sesion_productos_salida(request)
    if not codigo_barra.isdigit():
        messages.error(request, 'El código de barra debe contener solo números.')
        return redirect('bincard-buscar')

    try:
        producto = Producto.objects.get(codigo_barra=codigo_barra)
    except Producto.DoesNotExist:
        messages.error(request, 'Producto no encontrado.')
        return redirect('bincard-buscar')

    # Obtener transacciones y actas
    transacciones = Transaccion.objects.filter(producto=producto).order_by('fecha')
    actas = ActaEntrega.objects.filter(producto=producto).order_by('fecha')

    # Crear una lista de eventos combinada (entradas y salidas)
    eventos = []
    # Agregar transacciones de entrada
    for transaccion in transacciones.filter(tipo='entrada'):
        guia_o_factura = transaccion.guia_despacho or transaccion.numero_factura or "-"
        if transaccion.guia_despacho:
            guia_o_factura = f"Guía: {transaccion.guia_despacho}"
        elif transaccion.numero_factura:
            guia_o_factura = f"Factura: {transaccion.numero_factura}"

        eventos.append({
            'tipo': 'entrada',
            'fecha': transaccion.fecha or datetime.now(pytz.UTC),  # Usar fecha actual si es NULL
            'guia_o_factura': guia_o_factura,
            'numero_acta': None,
            'rut_proveedor': transaccion.rut_proveedor or '-',
            'departamento': None,
            'entrada': transaccion.cantidad,
            'salida': 0,
        })

    # Agregar transacciones de salida (vinculadas a actas)
    for transaccion in transacciones.filter(tipo='salida'):
        if transaccion.acta_entrega:  # Solo incluir transacciones asociadas a un acta
            eventos.append({
                'tipo': 'salida',
                'fecha': transaccion.fecha or transaccion.acta_entrega.fecha or datetime.now(pytz.UTC),  # Usar fecha de la transacción, o del acta, o actual
                'guia_o_factura': "-",
                'numero_acta': transaccion.acta_entrega.numero_acta,
                'rut_proveedor': None,
                'departamento': transaccion.acta_entrega.departamento,
                'entrada': 0,
                'salida': transaccion.cantidad,
            })

    # Ordenar eventos por fecha
    eventos.sort(key=lambda x: x['fecha'] or datetime.now(pytz.UTC))  # Asegurarse de que eventos sin fecha se ordenen al final

    # Calcular el saldo de forma incremental
    saldo = 0
    movimientos = []
    for evento in eventos:
        if evento['tipo'] == 'entrada':
            saldo += evento['entrada']
        else:  # tipo == 'salida'
            saldo -= evento['salida']

        if saldo < 0:
            messages.error(request, f'Error: El saldo no puede ser negativo en la fecha {evento["fecha"]}. Contacte al administrador.')
            return redirect('bincard-buscar')

        evento['saldo'] = saldo
        movimientos.append(evento)

    total_entradas = sum(m['entrada'] for m in movimientos)
    total_salidas = sum(m['salida'] for m in movimientos)

    # Verificar si el saldo calculado coincide con el stock actual
    if saldo != producto.stock:
        messages.warning(request, f'Advertencia: El saldo calculado ({saldo}) no coincide con el stock actual del producto ({producto.stock}).')
        # Corregir el stock del producto
        producto.stock = saldo
        producto.save()
        messages.info(request, f'El stock del producto ha sido corregido a {saldo} para que coincida con el saldo calculado.')

    # Exportar a Excel si se solicita
    if request.method == 'POST' and 'exportar_excel' in request.POST:
        columnas = ['Fecha', 'Guía o Factura', 'N° Acta', 'Proveedor (RUT)', 'Programa/Departamento', 'Entrada', 'Salida', 'Saldo']
        campos = ['fecha', 'guia_o_factura', 'numero_acta', 'rut_proveedor', 'departamento', 'entrada', 'salida', 'saldo']
        return exportar_excel(request, movimientos, f"Bincard_{producto.codigo_barra}", columnas, campos)

    page_obj = paginar_resultados(request, movimientos)
    return render(request, 'accounts/bincard_historial.html', {
        'producto': producto,
        'page_obj': page_obj,
        'total_entradas': total_entradas,
        'total_salidas': total_salidas,
    })

@login_required
def agregar_departamento(request):
    limpiar_sesion_productos_salida(request)
    if not request.user.has_perm('accounts.can_manage_departments'):
        messages.error(request, 'No tienes permiso para agregar departamentos.')
        return redirect('home')
    if request.method == 'POST':
        form = DepartamentoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Departamento agregado con éxito.')
            return redirect('home')
        messages.error(request, 'Error al agregar el departamento. Verifica los datos.')
    else:
        form = DepartamentoForm()
    return render(request, 'accounts/agregar_departamento.html', {'form': form})

@login_required
def modificar_departamento(request):
    limpiar_sesion_productos_salida(request)
    if not request.user.has_perm('accounts.can_manage_departments'):
        messages.error(request, 'No tienes permiso para modificar departamentos.')
        return redirect('home')
    if request.method == 'POST':
        form = ModificarDepartamentoForm(request.POST)
        if form.is_valid():
            departamento_nombre = form.cleaned_data['departamento']
            nuevo_nombre = form.cleaned_data['nuevo_nombre']
            jefatura = form.cleaned_data['jefatura']
            jefatura_subrogante = form.cleaned_data['jefatura_subrogante']
            secretaria = form.cleaned_data['secretaria']
            secretaria_subrogante = form.cleaned_data['secretaria_subrogante']

            departamento = Departamento.objects.get(nombre=departamento_nombre, activo=True)
            departamento.nombre = nuevo_nombre
            departamento.save()

            # Actualizar los responsables asociados al departamento
            responsables = Responsable.objects.filter(departamento=departamento)
            
            if not jefatura:
                responsables.filter(tipo='Jefatura').update(nombre=f"Jefatura {nuevo_nombre}")
            else:
                responsables.filter(tipo='Jefatura').update(nombre=jefatura)

            if not jefatura_subrogante:
                responsables.filter(tipo='Jefatura Subrogante').update(nombre=f"Jefatura {nuevo_nombre}(s)")
            else:
                responsables.filter(tipo='Jefatura Subrogante').update(nombre=jefatura_subrogante)

            if not secretaria:
                responsables.filter(tipo='Secretaria').update(nombre=f"Secretaria {nuevo_nombre}")
            else:
                responsables.filter(tipo='Secretaria').update(nombre=secretaria)

            if not secretaria_subrogante:
                responsables.filter(tipo='Secretaria Subrogante').update(nombre=f"Secretaria {nuevo_nombre}(s)")
            else:
                responsables.filter(tipo='Secretaria Subrogante').update(nombre=secretaria_subrogante)

            messages.success(request, 'Departamento modificado con éxito.')
            return redirect('home')
        messages.error(request, 'Error al modificar el departamento. Verifica los datos.')
    else:
        form = ModificarDepartamentoForm()
        departamentos = Departamento.objects.filter(activo=True)
        # Crear un diccionario con los responsables de cada departamento
        responsables_por_departamento = {}
        for dept in departamentos:
            responsables = dept.responsables.all()
            responsables_dict = {r.tipo: r.nombre for r in responsables}
            responsables_por_departamento[dept.nombre] = responsables_dict
        # Convertir el diccionario a JSON y marcarlo como seguro
        responsables_json = mark_safe(json.dumps(responsables_por_departamento))
        print("Departamentos disponibles en la vista modificar_departamento:", list(departamentos))
        print("Opciones del campo departamento:", form.fields['departamento'].choices)
        print("Responsables por departamento:", responsables_por_departamento)
    return render(request, 'accounts/modificar_departamento.html', {
        'form': form,
        'responsables_json': responsables_json  # Pasamos el JSON en lugar del diccionario
    })

@login_required
def eliminar_departamento(request):
    limpiar_sesion_productos_salida(request)
    if not request.user.has_perm('accounts.can_manage_departments'):
        messages.error(request, 'No tienes permiso para deshabilitar departamentos.')
        return redirect('home')
    if request.method == 'POST':
        form = EliminarDepartamentoForm(request.POST)
        if form.is_valid():
            departamento_nombre = form.cleaned_data['departamento']
            departamento = Departamento.objects.get(nombre=departamento_nombre, activo=True)
            departamento.activo = False  # Deshabilitar en lugar de eliminar
            departamento.save()
            messages.success(request, 'Departamento deshabilitado con éxito.')
            return redirect('home')
        messages.error(request, 'Error al deshabilitar el departamento. Verifica los datos.')
    else:
        form = EliminarDepartamentoForm()
        departamentos = Departamento.objects.filter(activo=True)
        print("Departamentos disponibles en la vista eliminar_departamento:", list(departamentos))
        print("Opciones del campo departamento en la vista:", form.fields['departamento'].choices)
    return render(request, 'accounts/eliminar_departamento.html', {'form': form})

@login_required
def funcionarios_por_departamento(request):
    departamento = request.GET.get('departamento', '')
    if not departamento:
        return JsonResponse({'error': 'Departamento no especificado'}, status=400)

    try:
        departamento_obj = Departamento.objects.get(nombre=departamento)
        responsables = departamento_obj.responsables.all()
        responsables_list = [{'id': r.id, 'nombre': r.nombre} for r in responsables]  # Incluimos el ID
        print(f"Responsables encontrados para {departamento}: {responsables_list}")
        return JsonResponse({'funcionarios': responsables_list})
    except Departamento.DoesNotExist:
        return JsonResponse({'error': 'Departamento no encontrado'}, status=404)

# Vistas para gestión de usuarios
@login_required
@permission_required('accounts.can_access_admin', raise_exception=True)
@permission_required('accounts.can_manage_users', raise_exception=True)
def listar_usuarios(request):
    """Vista para listar usuarios con búsqueda y paginación"""
    limpiar_sesion_productos_salida(request)
    
    usuarios = CustomUser.objects.all().order_by('rut')
    form = SearchUserForm(request.GET or None)

    query_rut = request.GET.get('rut', '')
    query_nombre = request.GET.get('nombre', '')
    query_rol = request.GET.get('rol', '')

    # Depuración: Verificar si el formulario es válido y qué contiene cleaned_data
    print(f"Formulario válido: {form.is_valid()}")
    if form.is_valid():
        print(f"Datos limpiados: {form.cleaned_data}")
        query_rut = form.cleaned_data['rut']
        query_nombre = form.cleaned_data['nombre']
        query_rol = form.cleaned_data['rol']  # Este valor debería ser el nombre del grupo (como "Administrador") o None

        if query_rut:
            usuarios = usuarios.filter(rut__icontains=query_rut)
        if query_nombre:
            usuarios = usuarios.filter(nombre__icontains=query_nombre)
        if query_rol:  # query_rol será el nombre del grupo (como "Administrador") o None
            print(f"Filtrando por rol: {query_rol}")
            usuarios = usuarios.filter(groups__name=query_rol)
    else:
        print(f"Errores del formulario: {form.errors}")

    page_obj = paginar_resultados(request, usuarios)

    context = {
        'page_obj': page_obj,
        'form': form,
        'query_rut': query_rut,
        'query_nombre': query_nombre,
        'query_rol': query_rol,
    }
    return render(request, 'accounts/listar_usuarios.html', context)

@login_required
@permission_required('accounts.can_access_admin', raise_exception=True)
@permission_required('accounts.can_manage_users', raise_exception=True)
def agregar_usuario(request):
    """Vista para agregar un nuevo usuario"""
    limpiar_sesion_productos_salida(request)
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            messages.success(request, f'Usuario {usuario.rut} creado con éxito.')
            return redirect('listar-usuarios')
        messages.error(request, 'Error al crear el usuario. Verifica los datos.')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/agregar_usuario.html', {'form': form})

@login_required
@permission_required('accounts.can_access_admin', raise_exception=True)
@permission_required('accounts.can_manage_users', raise_exception=True)
def editar_usuario(request, rut):
    """Vista para editar un usuario existente"""
    limpiar_sesion_productos_salida(request)
    
    usuario = get_object_or_404(CustomUser, rut=rut)
    
    if request.method == 'POST':
        form = CustomUserEditForm(request.POST, instance=usuario)
        if form.is_valid():
            # Guardar los datos del formulario
            usuario = form.save()
            # Verificar si se proporcionó una nueva contraseña
            password = form.cleaned_data.get('password')
            if password:  # Solo cambiamos la contraseña si se proporcionó una
                usuario.set_password(password)
                usuario.save()
                messages.info(request, 'La contraseña ha sido actualizada.')
            messages.success(request, f'Usuario {usuario.rut} actualizado con éxito.')
            return redirect('listar-usuarios')
        messages.error(request, 'Error al actualizar el usuario. Verifica los datos.')
    else:
        form = CustomUserEditForm(instance=usuario)
    
    return render(request, 'accounts/editar_usuario.html', {'form': form, 'usuario': usuario})

@login_required
@permission_required('accounts.can_access_admin', raise_exception=True)
@permission_required('accounts.can_manage_users', raise_exception=True)
def deshabilitar_usuario(request, rut):
    """Vista para deshabilitar o habilitar un usuario"""
    limpiar_sesion_productos_salida(request)
    
    usuario = get_object_or_404(CustomUser, rut=rut)
    
    if request.method == 'POST':
        if usuario.is_active:
            usuario.is_active = False
            usuario.save()
            messages.success(request, f'Usuario {usuario.rut} deshabilitado con éxito.')
        else:
            usuario.is_active = True
            usuario.save()
            messages.success(request, f'Usuario {usuario.rut} habilitado con éxito.')
        return redirect('listar-usuarios')
    
    return render(request, 'accounts/deshabilitar_usuario.html', {'usuario': usuario})

@login_required
@permission_required('accounts.can_access_admin', raise_exception=True)
def verify_password(request):
    """Vista para verificar la contraseña del administrador antes de acceder al panel de administración"""
    # Verificar si el usuario tiene permisos para acceder al panel de admin
    if not request.user.is_staff or not request.user.is_superuser:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'No tienes permisos suficientes para acceder al panel de administración.'}, status=403)
        messages.error(request, 'No tienes permisos suficientes para acceder al panel de administración. Contacta a un administrador.')
        return redirect('home')

    if request.method == 'POST':
        password = request.POST.get('password')
        user = request.user

        # Verificar si la contraseña proporcionada es correcta
        if user.check_password(password):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            messages.success(request, 'Contraseña verificada correctamente. Redirigiendo al panel de administración...')
            return redirect('/admin/')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Contraseña incorrecta. Por favor, intenta de nuevo.'})
            messages.error(request, 'Contraseña incorrecta. Por favor, intenta de nuevo.')
            return render(request, 'accounts/verify_password.html')

    # Si es un GET, renderizar el formulario de verificación
    return render(request, 'accounts/verify_password.html')