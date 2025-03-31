from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from datetime import datetime
import os
import urllib.parse
import openpyxl
from django.utils.text import slugify
import pytz
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm, inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from .forms import ProductoForm, TransaccionForm, ActaEntregaForm
from .models import Producto, Transaccion, ActaEntrega, Funcionario

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
    acta = actas.first()
    productos_salida = [
        {
            'codigo_barra': item.producto.codigo_barra,
            'descripcion': item.producto.descripcion,
            'numero_siscom': item.numero_siscom or '',
            'cantidad': item.cantidad,
            'observacion': item.observacion or '',
        } for item in actas
    ]

    response = HttpResponse(content_type='application/pdf')
    filename = f"Acta_Entrega_Nro_{acta.numero_acta}.pdf"
    encoded_filename = urllib.parse.quote(filename)
    response['Content-Disposition'] = f'{disposition}; filename="{encoded_filename}"'
    response['Content-Type'] = 'application/pdf; charset=utf-8'

    doc = SimpleDocTemplate(response, pagesize=letter, leftMargin=0.75*inch, rightMargin=0.75*inch,
                        topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()

    estilos = {
        'TitleCustom': ParagraphStyle(name='TitleCustom', fontName='Helvetica-Bold', fontSize=14, alignment=1, spaceAfter=10, leading=16),
        'NormalBold': ParagraphStyle(name='NormalBold', fontName='Helvetica-Bold', fontSize=10, spaceAfter=4, leading=12),
        'NormalCustom': ParagraphStyle(name='NormalCustom', fontName='Helvetica-Bold', fontSize=10, spaceAfter=4, leading=12),
        'ActaNumber': ParagraphStyle(name='ActaNumber', fontName='Helvetica-Bold', fontSize=20, alignment=1, textColor=colors.black, spaceAfter=0, leading=24),
        'Signature': ParagraphStyle(name='Signature', fontName='Times-Roman', fontSize=10, alignment=1, spaceBefore=10, spaceAfter=4, leading=12),
        'SignatureTitle': ParagraphStyle(name='SignatureTitle', fontName='Times-Bold', fontSize=10, alignment=1, spaceBefore=4, spaceAfter=4, leading=12),
        'SignatureCargo': ParagraphStyle(name='SignatureCargo', fontName='Times-Italic', fontSize=9, alignment=1, spaceBefore=2, spaceAfter=2, leading=11),
        'TableCell': ParagraphStyle(name='TableCell', fontName='Helvetica-Bold', fontSize=9, leading=11, wordWrap='CJK'),
    }
    for name, style in estilos.items():
        styles.add(style)

    elements = []
    logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'images', 'seremi_logo.png')
    logo = Image(logo_path, width=3*cm, height=3*cm) if os.path.exists(logo_path) else Paragraph("Logo no encontrado", styles['NormalCustom'])
    logo.hAlign = 'LEFT'

    acta_number = Paragraph(f"N° {acta.numero_acta}", styles['ActaNumber'])
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
    
    elements.extend([
        header_table,
        Spacer(1, 0.2*cm),
        Paragraph("ACTA DE ENTREGA MATERIALES O INSUMOS", styles['TitleCustom']),
        Spacer(1, 0.3*cm),
        Paragraph(f"En Temuco con fecha {acta.fecha.strftime('%d-%m-%Y')} se procede a realizar la entrega de los siguientes artículos a:", styles['NormalCustom']),
        Spacer(1, 0.2*cm),
        Paragraph(f"Sección: {acta.departamento}", styles['NormalCustom']),
        Spacer(1, 0.1*cm),
        Paragraph(f"Responsable: {acta.responsable}", styles['NormalCustom']),
        Spacer(1, 0.5*cm),
        Paragraph("Datos de Productos", styles['NormalBold']),
        Spacer(1, 0.2*cm)
    ])

    data = [['Descripción', 'Nro. SISCOM', 'Cantidad', 'Observación']]
    for item in productos_salida:
        observacion_text = (item['observacion'] or '-').replace('\n', '<br/>')
        data.append([item['descripcion'], item['numero_siscom'], str(item['cantidad']), Paragraph(observacion_text, styles['TableCell'])])

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
    
    responsable_lower = acta.responsable.lower()
    cargo = "SECRETARIA DEL DEPARTAMENTO" if 'secretaria' in responsable_lower else "JEFE DEL DEPARTAMENTO" if 'jefe' in responsable_lower or 'jefatura' in responsable_lower else "RESPONSABLE DEL DEPARTAMENTO"

    firma_table = Table([
        [Paragraph(f"{acta.generador}", styles['Signature']), Paragraph(f"Sr./Sra. {acta.responsable}", styles['Signature'])],
        [Paragraph("ENCARGADO BODEGA", styles['SignatureTitle']), Paragraph("RECEPCIONA CONFORME", styles['SignatureTitle'])],
        ['', Paragraph(cargo, styles['SignatureCargo'])],
        [Paragraph("_____________________________", styles['Signature']), Paragraph("_____________________________", styles['Signature'])],
    ], colWidths=[3*inch, 3*inch])
    firma_table.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('FONTNAME', (0, 0), (-1, -1), 'Times-Roman'), ('FONTSIZE', (0, 0), (-1, -1), 10), ('LEADING', (0, 0), (-1, -1), 12)]))

    elements.extend([table, Spacer(1, 4*inch), firma_table])
    doc.build(elements)
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
            # Si el campo es 'fecha' y el valor es un datetime, formatearlo como cadena
            if campo == 'fecha' and isinstance(valor, datetime):
                valor = valor.strftime('%d-%m-%Y %H:%M')
            fila.append(valor)
        ws.append(fila)

    # Ajustar el ancho de las columnas
    for col in ws.columns:
        max_length = max(len(str(cell.value)) for cell in col if cell.value)
        column_letter = col[0].column_letter
        # Establecer un ancho fijo para la columna "Fecha" (la primera columna)
        if column_letter == 'A':  # La columna "Fecha" es la primera (A)
            ws.column_dimensions[column_letter].width = 20  # Ancho fijo para la fecha
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
    limpiar_sesion_productos_salida(request)
    return render(request, 'accounts/home.html')

class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'

    def post(self, request, *args, **kwargs):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
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
def listar_actas(request):
    limpiar_sesion_productos_salida(request)
    actas = ActaEntrega.objects.all().order_by('-numero_acta')
    query_numero_acta = request.GET.get('numero_acta', '')
    query_responsable = request.GET.get('responsable', '')

    if query_numero_acta:
        try:
            actas = actas.filter(numero_acta__startswith=int(query_numero_acta))
        except ValueError:
            messages.error(request, 'El número de acta debe ser un valor numérico.')
    if query_responsable:
        actas = actas.filter(responsable__icontains=query_responsable)

    actas_dict = {acta.numero_acta: acta for acta in actas}
    actas_lista = sorted(actas_dict.values(), key=lambda x: x.numero_acta, reverse=True)
    page_obj = paginar_resultados(request, actas_lista)

    return render(request, 'accounts/listar_actas.html', {
        'actas': page_obj,
        'query_numero_acta': query_numero_acta,
        'query_responsable': query_responsable,
    })

@login_required
def agregar_stock(request):
    limpiar_sesion_productos_salida(request)
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

    return render(request, 'accounts/agregar_stock_detalle.html', {'producto': producto, 'form': form})

@login_required
def salida_productos(request):
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
    productos_salida = request.session.get('productos_salida', [])
    if not productos_salida:
        messages.error(request, 'No hay productos seleccionados para la salida.')
        return redirect('salida-productos')

    if request.method == 'POST':
        form = ActaEntregaForm(request.POST)
        if form.is_valid():
            try:
                for item in productos_salida:
                    producto = Producto.objects.get(codigo_barra=item['codigo_barra'])
                    transacciones = Transaccion.objects.filter(producto=producto).order_by('fecha')
                    actas = ActaEntrega.objects.filter(producto=producto).order_by('fecha')
                    saldo = sum(t.cantidad if t.tipo == 'entrada' else -t.cantidad for t in transacciones) - sum(a.cantidad for a in actas)
                    cantidad = int(item['cantidad'] or 0)
                    if saldo - cantidad < 0:
                        messages.error(request, f'No hay suficiente stock para {producto.descripcion} (Código: {producto.codigo_barra}). Saldo: {saldo}, Solicitado: {cantidad}.')
                        return redirect('salida-productos-seleccion')

                ultimo_acta = ActaEntrega.objects.order_by('-numero_acta').first()
                numero_acta = 1 if not ultimo_acta else ultimo_acta.numero_acta + 1

                for item in productos_salida:
                    producto = Producto.objects.get(codigo_barra=item['codigo_barra'])
                    cantidad = int(item['cantidad'])
                    acta = ActaEntrega(
                        numero_acta=numero_acta,
                        departamento=form.cleaned_data['departamento'],
                        responsable=form.cleaned_data['responsable'],
                        generador='Administrador' if request.user.username == 'admin' else 'Gersonns Matus',
                        producto=producto,
                        cantidad=cantidad,
                        numero_siscom=item['numero_siscom'] or '',
                        observacion=item['observacion'] or '',
                    )
                    acta.save()
                    producto.stock -= cantidad
                    producto.save()

                actas = ActaEntrega.objects.filter(numero_acta=numero_acta)
                response = generar_pdf_acta(actas)
                limpiar_sesion_productos_salida(request)
                return response

            except Exception as e:
                messages.error(request, f'Error al procesar el acta: {str(e)}')
                return redirect('salida-productos-seleccion')
        messages.error(request, 'Error al generar el acta. Verifica los datos.')
    else:
        form = ActaEntregaForm()

    return render(request, 'accounts/salida_productos_seleccion.html', {'form': form, 'productos_salida': productos_salida})

@login_required
def funcionarios_por_departamento(request):
    departamento = request.GET.get('departamento', '')
    if not departamento:
        return JsonResponse({'error': 'Departamento no especificado'}, status=400)

    responsables = [
        {'nombre': f'Jefatura {departamento}'},
        {'nombre': f'Jefatura {departamento}(s)'},
        {'nombre': f'Secretaria {departamento}'},
        {'nombre': f'Secretaria {departamento}(s)'},
    ]
    if departamento == 'Departamento de Salud Pública':
        responsables = [
            {'nombre': 'Jefe Salud Pública'},
            {'nombre': 'Jefe Salud Pública(s)'},
            {'nombre': 'Secretaria Subrogante Salud Pública'},
            {'nombre': 'Secretaria Subrogante Salud Pública(s)'},
        ]
    return JsonResponse({'funcionarios': responsables})

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

    transacciones = Transaccion.objects.filter(producto=producto).order_by('fecha')
    actas = ActaEntrega.objects.filter(producto=producto).order_by('fecha')
    movimientos = []
    saldo = 0

    for transaccion in transacciones:
        entrada = transaccion.cantidad if transaccion.tipo == 'entrada' else 0
        salida = transaccion.cantidad if transaccion.tipo == 'salida' else 0
        saldo += entrada - salida
        if saldo < 0:
            messages.error(request, f'Error: El saldo no puede ser negativo en la fecha {transaccion.fecha}. Contacte al administrador.')
            return redirect('bincard-buscar')
        
        # Determinar el valor de "Guía o Factura"
        if transaccion.guia_despacho:
            guia_o_factura = f"Guía: {transaccion.guia_despacho}"
        elif transaccion.numero_factura:
            guia_o_factura = f"Factura: {transaccion.numero_factura}"
        else:
            guia_o_factura = "-"

        movimientos.append({
            'fecha': transaccion.fecha,  # Ya no necesitamos .replace(tzinfo=None)
            'guia_o_factura': guia_o_factura,
            'numero_acta': None,
            'rut_proveedor': transaccion.rut_proveedor,
            'departamento': None,
            'entrada': entrada,
            'salida': salida,
            'saldo': saldo,
        })

    for acta in actas:
        saldo -= acta.cantidad
        if saldo < 0:
            messages.error(request, f'Error: El saldo no puede ser negativo en la fecha {acta.fecha}. Contacte al administrador.')
            return redirect('bincard-buscar')
        
        # Para las actas, no hay guía ni factura
        guia_o_factura = "-"

        movimientos.append({
            'fecha': acta.fecha,  # Ya no necesitamos .replace(tzinfo=None)
            'guia_o_factura': guia_o_factura,
            'numero_acta': acta.numero_acta,
            'rut_proveedor': None,
            'departamento': acta.departamento,
            'entrada': 0,
            'salida': acta.cantidad,
            'saldo': saldo,
        })

    movimientos.sort(key=lambda x: x['fecha'])
    total_entradas = sum(m['entrada'] for m in movimientos)
    total_salidas = sum(m['salida'] for m in movimientos)

    if saldo != producto.stock:
        messages.warning(request, f'Advertencia: El saldo calculado ({saldo}) no coincide con el stock actual del producto ({producto.stock}). Contacte al administrador.')

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