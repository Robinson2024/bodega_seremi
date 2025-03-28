from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import ProductoForm, TransaccionForm, ActaEntregaForm
from .models import Producto, Transaccion, ActaEntrega, Funcionario  # Corregido: Import directo desde .models
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm, inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from datetime import datetime
import os
import urllib.parse  # Para codificar el nombre del archivo
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger  # Importar Paginator
import openpyxl  # Para exportar a Excel
from django.utils.text import slugify  # Para generar nombres de archivo seguros
import pytz


@login_required
def home(request):
    # Limpiar la sesión si existe productos_salida
    if 'productos_salida' in request.session:
        del request.session['productos_salida']
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
        else:
            messages.error(request, 'Credenciales inválidas')
            return self.render_to_response(self.get_context_data())

    def get_success_url(self):
        return '/'
    
@login_required
def registrar_producto(request):
    # Limpiar la sesión si existe productos_salida
    if 'productos_salida' in request.session:
        del request.session['productos_salida']
        
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            # Guardar el producto
            producto = form.save()

            # Obtener el stock inicial del producto recién creado
            stock_inicial = producto.stock

            # Si el stock inicial es mayor a 0, registrar una transacción de entrada
            if stock_inicial > 0:
                transaccion = Transaccion(
                    producto=producto,
                    tipo='entrada',
                    cantidad=stock_inicial,
                    fecha=datetime.now(pytz.UTC),  # Fecha actual en UTC
                    rut_proveedor=producto.rut_proveedor if producto.rut_proveedor else '',
                    guia_despacho=producto.guia_despacho if producto.guia_despacho else '',
                    numero_factura=producto.numero_factura if producto.numero_factura else '',
                    orden_compra=producto.orden_compra if producto.orden_compra else '',
                    observacion='Stock inicial al registrar el producto'
                )
                transaccion.save()

            messages.success(request, 'Producto registrado con éxito.')
            return redirect('home')
        else:
            messages.error(request, 'Error al registrar el producto. Verifica los datos.')
    else:
        form = ProductoForm()
    return render(request, 'accounts/registrar_producto.html', {'form': form})

@login_required
def listar_productos(request):
    # Limpiar la sesión si existe productos_salida
    if 'productos_salida' in request.session:
        del request.session['productos_salida']
        
    # Determinar si la solicitud es GET o POST para obtener los parámetros
    if request.method == 'POST':
        # Para la exportación a Excel, los parámetros vienen en request.POST
        query_codigo = request.POST.get('codigo_barra', '')
        query_descripcion = request.POST.get('descripcion', '')
        query_categoria = request.POST.get('categoria', '')
    else:
        # Para la visualización de la tabla, los parámetros vienen en request.GET
        query_codigo = request.GET.get('codigo_barra', '')
        query_descripcion = request.GET.get('descripcion', '')
        query_categoria = request.GET.get('categoria', '')

    # Obtener todos los productos y aplicar filtros
    productos = Producto.objects.all().order_by('codigo_barra')

    # Filtrar por código de barra
    if query_codigo:
        productos = productos.filter(codigo_barra=query_codigo)

    # Filtrar por descripción
    if query_descripcion:
        productos = productos.filter(descripcion__icontains=query_descripcion)

    # Filtrar por categoría
    if query_categoria and query_categoria != 'Todas':
        productos = productos.filter(categoria=query_categoria)

    # Manejar la exportación a Excel
    if request.method == 'POST' and 'exportar_excel' in request.POST:
        # Crear un libro de Excel
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Productos"

        # Definir los encabezados
        headers = ['Código de Barra', 'Nombre del Producto', 'Categoría', 'Stock Actual']
        ws.append(headers)

        # Estilo para los encabezados
        for col in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col)
            cell.font = openpyxl.styles.Font(bold=True)
            cell.fill = openpyxl.styles.PatternFill(start_color="D3D3D3", end_color="D3D3D3", fill_type="solid")
            cell.alignment = openpyxl.styles.Alignment(horizontal='center')

        # Agregar los datos de los productos (ya filtrados)
        for idx, producto in enumerate(productos, start=2):
            ws.append([
                producto.codigo_barra,
                producto.descripcion,
                producto.categoria if producto.categoria else "Otros",
                producto.stock,
            ])

        # Ajustar el ancho de las columnas
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2)
            ws.column_dimensions[column].width = adjusted_width

        # Generar el nombre del archivo
        categoria_name = query_categoria if query_categoria and query_categoria != 'Todas' else 'Todas'
        fecha = datetime.now().strftime('%Y-%m-%d')
        filename = f"Productos_{slugify(categoria_name)}_{fecha}.xlsx"
        encoded_filename = urllib.parse.quote(filename)

        # Preparar la respuesta
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{encoded_filename}"'
        wb.save(response)
        return response

    # Implementar paginación: 20 productos por página
    paginator = Paginator(productos, 20)  # 20 productos por página
    page = request.GET.get('page')  # Obtener el número de página de los parámetros de la URL

    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        # Si la página no es un entero, mostrar la primera página
        page_obj = paginator.page(1)
    except EmptyPage:
        # Si la página está fuera de rango, mostrar la última página
        page_obj = paginator.page(paginator.num_pages)

    # Obtener las categorías disponibles para el filtro
    categorias = [('', 'Todas')] + Producto.CATEGORIAS

    context = {
        'page_obj': page_obj,
        'query_codigo': query_codigo,
        'query_descripcion': query_descripcion,
        'query_categoria': query_categoria,
        'categorias': categorias,
    }
    return render(request, 'accounts/listar_productos.html', context)

@login_required
def listar_actas(request):
    # Limpiar la sesión si existe productos_salida
    if 'productos_salida' in request.session:
        del request.session['productos_salida']
        
    # Obtener todas las actas, ordenadas por número de acta descendente
    actas = ActaEntrega.objects.all().order_by('-numero_acta')

    # Obtener parámetros de búsqueda
    query_numero_acta = request.GET.get('numero_acta', '')
    query_responsable = request.GET.get('responsable', '')

    # Filtrar por número de acta si se proporciona
    if query_numero_acta:
        try:
            numero_acta = int(query_numero_acta)
            actas = actas.filter(numero_acta__startswith=numero_acta)  # Filtrar actas que comiencen con el número
        except ValueError:
            messages.error(request, 'El número de acta debe ser un valor numérico.')

    # Filtrar por responsable si se proporciona, respetando tildes
    if query_responsable:
        actas = actas.filter(responsable__icontains=query_responsable)

    # Agrupar actas por número de acta para mostrar solo una entrada por acta
    actas_dict = {}
    for acta in actas:
        if acta.numero_acta not in actas_dict:
            actas_dict[acta.numero_acta] = acta

    actas = list(actas_dict.values())
    actas.sort(key=lambda x: x.numero_acta, reverse=True)

    # Implementar paginación: 20 actas por página
    paginator = Paginator(actas, 20)  # 20 actas por página
    page = request.GET.get('page')  # Obtener el número de página de los parámetros de la URL

    try:
        actas_paginadas = paginator.page(page)
    except PageNotAnInteger:
        # Si la página no es un entero, mostrar la primera página
        actas_paginadas = paginator.page(1)
    except EmptyPage:
        # Si la página está fuera de rango, mostrar la última página
        actas_paginadas = paginator.page(paginator.num_pages)

    context = {
        'actas': actas_paginadas,  # Pasar las actas paginadas en lugar de todas las actas
        'query_numero_acta': query_numero_acta,
        'query_responsable': query_responsable,
    }
    return render(request, 'accounts/listar_actas.html', context)

@login_required
def agregar_stock(request):
    # Limpiar la sesión si existe productos_salida
    if 'productos_salida' in request.session:
        del request.session['productos_salida']
    
    # Obtener todos los productos para mostrarlos en una lista
    productos = Producto.objects.all().order_by('codigo_barra')  # Agregar orden por codigo_barra
    query_codigo = request.GET.get('codigo_barra', '')
    query_descripcion = request.GET.get('descripcion', '')

    if query_codigo:
        productos = productos.filter(codigo_barra=query_codigo)
    if query_descripcion:
        productos = productos.filter(descripcion__icontains=query_descripcion)

    # Implementar paginación: 20 productos por página
    paginator = Paginator(productos, 20)  # 20 productos por página
    page = request.GET.get('page')  # Obtener el número de página de los parámetros de la URL

    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        # Si la página no es un entero, mostrar la primera página
        page_obj = paginator.page(1)
    except EmptyPage:
        # Si la página está fuera de rango, mostrar la última página
        page_obj = paginator.page(paginator.num_pages)

    context = {
        'page_obj': page_obj,  # Pasar el objeto paginado en lugar de 'productos'
        'query_codigo': query_codigo,
        'query_descripcion': query_descripcion,
    }
    return render(request, 'accounts/agregar_stock.html', context)

@login_required
def agregar_stock_detalle(request, codigo_barra):
    # Limpiar la sesión si existe productos_salida
    if 'productos_salida' in request.session:
        del request.session['productos_salida']
        
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
            # Asignar los valores del formulario a la transacción
            transaccion.rut_proveedor = form.cleaned_data['rut_proveedor'] or ''
            transaccion.guia_despacho = form.cleaned_data['guia_despacho'] or ''
            transaccion.numero_factura = form.cleaned_data['numero_factura'] or ''
            transaccion.orden_compra = form.cleaned_data['orden_compra'] or ''
            # No asignamos observacion, ya que el campo no está en el formulario
            # transaccion.observacion = ''  # Opcional: asignar un valor vacío si es necesario
            transaccion.save()

            producto.stock += form.cleaned_data['cantidad']
            producto.rut_proveedor = form.cleaned_data['rut_proveedor'] or ''
            producto.guia_despacho = form.cleaned_data['guia_despacho'] or ''
            producto.numero_factura = form.cleaned_data['numero_factura'] or ''
            producto.orden_compra = form.cleaned_data['orden_compra'] or ''
            producto.save()

            messages.success(request, f'Stock agregado exitosamente. Nueva cantidad: {producto.stock}')
            return redirect('agregar-stock')
        else:
            messages.error(request, 'Error al agregar stock. Verifica los datos.')
    else:
        form = TransaccionForm()

    return render(request, 'accounts/agregar_stock_detalle.html', {
        'producto': producto,
        'form': form,
    })

@login_required
def salida_productos(request):
    productos_salida = request.session.get('productos_salida', [])
    productos = Producto.objects.all().order_by('codigo_barra')  # Agregar orden por codigo_barra
    query_codigo = request.GET.get('codigo_barra', '')
    query_descripcion = request.GET.get('descripcion', '')

    if query_codigo:
        productos = productos.filter(codigo_barra=query_codigo)
    if query_descripcion:
        productos = productos.filter(descripcion__icontains=query_descripcion)

    # Implementar paginación: 20 productos por página
    paginator = Paginator(productos, 20)  # 20 productos por página
    page = request.GET.get('page')  # Obtener el número de página de los parámetros de la URL

    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        # Si la página no es un entero, mostrar la primera página
        page_obj = paginator.page(1)
    except EmptyPage:
        # Si la página está fuera de rango, mostrar la última página
        page_obj = paginator.page(paginator.num_pages)

    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        action = request.POST.get('action')
        if action == 'update_data':
            codigo_barra = request.POST.get('codigo_barra')
            numero_siscom = request.POST.get('numero_siscom', '')
            cantidad = request.POST.get('cantidad', '')
            observacion = request.POST.get('observacion', '')

            for item in productos_salida:
                if item['codigo_barra'] == codigo_barra:
                    item['numero_siscom'] = numero_siscom
                    item['cantidad'] = cantidad
                    item['observacion'] = observacion  # Los saltos de línea ya vienen como \n
                    break

            request.session['productos_salida'] = productos_salida
            request.session.modified = True
            return JsonResponse({'success': True})

    if request.method == 'POST' and 'agregar_producto' in request.POST:
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

    if request.method == 'POST' and 'eliminar_producto' in request.POST:
        codigo_barra = request.POST.get('codigo_barra')
        productos_salida = [item for item in productos_salida if item['codigo_barra'] != codigo_barra]
        request.session['productos_salida'] = productos_salida
        request.session.modified = True
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return redirect('salida-productos')

    if request.method == 'POST' and 'siguiente' in request.POST:
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

    context = {
        'page_obj': page_obj,  # Pasar el objeto paginado en lugar de 'productos'
        'query_codigo': query_codigo,
        'query_descripcion': query_descripcion,
        'productos_salida': productos_salida,
    }
    return render(request, 'accounts/salida_productos.html', context)

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
                # Depuración: Mostrar los productos que se están procesando
                print(f"Productos en productos_salida: {productos_salida}")

                # Validar el saldo de cada producto antes de procesar la salida
                for item in productos_salida:
                    try:
                        print(f"Validando producto: {item['codigo_barra']}")
                        producto = Producto.objects.get(codigo_barra=item['codigo_barra'])
                        # Calcular el saldo actual basado en transacciones y actas existentes
                        transacciones = Transaccion.objects.filter(producto=producto).order_by('fecha')
                        actas = ActaEntrega.objects.filter(producto=producto).order_by('fecha')
                        saldo = 0
                        for t in transacciones:
                            saldo += t.cantidad if t.tipo == 'entrada' else -t.cantidad
                        for a in actas:
                            saldo -= a.cantidad

                        # Verificar si la cantidad es válida
                        if not item['cantidad']:
                            messages.error(request, f'La cantidad para el producto {item["codigo_barra"]} no puede estar vacía.')
                            return redirect('salida-productos-seleccion')

                        try:
                            cantidad = int(item['cantidad'])
                        except ValueError:
                            messages.error(request, f'La cantidad para el producto {item["codigo_barra"]} debe ser un número entero.')
                            return redirect('salida-productos-seleccion')

                        # Verificar si la salida causará un saldo negativo
                        if saldo - cantidad < 0:
                            messages.error(request, f'No hay suficiente stock para el producto {producto.descripcion} (Código: {producto.codigo_barra}). Saldo actual: {saldo}, Cantidad solicitada: {cantidad}.')
                            return redirect('salida-productos-seleccion')

                    except Producto.DoesNotExist:
                        messages.error(request, f'Producto con código {item["codigo_barra"]} no encontrado.')
                        return redirect('salida-productos-seleccion')
                    except Exception as e:
                        messages.error(request, f'Error al validar el saldo del producto {item["codigo_barra"]}: {str(e)}')
                        return redirect('salida-productos-seleccion')

                # Generar el número del acta
                ultimo_acta = ActaEntrega.objects.order_by('-numero_acta').first()
                numero_acta = 1 if not ultimo_acta else ultimo_acta.numero_acta + 1
                print(f"Número de acta generado: {numero_acta}")

                # Guardar el acta para cada producto y actualizar el stock
                for item in productos_salida:
                    try:
                        print(f"Creando acta para el producto: {item['codigo_barra']}")
                        producto = Producto.objects.get(codigo_barra=item['codigo_barra'])
                        cantidad = int(item['cantidad'])

                        # Crear el acta
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
                        print(f"Acta creada para el producto {item['codigo_barra']}: Número {acta.numero_acta}, Cantidad: {acta.cantidad}")

                        # Actualizar el stock del producto
                        producto.stock -= cantidad
                        producto.save()
                        print(f"Stock actualizado para el producto {item['codigo_barra']}: Nuevo stock: {producto.stock}")

                    except Producto.DoesNotExist:
                        messages.error(request, f'Producto con código {item["codigo_barra"]} no encontrado.')
                        return redirect('salida-productos-seleccion')
                    except Exception as e:
                        messages.error(request, f'Error al crear el acta para el producto {item["codigo_barra"]}: {str(e)}')
                        return redirect('salida-productos-seleccion')

                # Generar el PDF después de completar todas las operaciones de base de datos
                try:
                    print("Generando el PDF...")
                    response = HttpResponse(content_type='application/pdf')
                    filename = f"Acta_Entrega_Nro_{numero_acta}.pdf"
                    encoded_filename = urllib.parse.quote(filename)
                    response['Content-Disposition'] = f'attachment; filename="{encoded_filename}"'
                    response['Content-Type'] = 'application/pdf; charset=utf-8'

                    # Configurar el documento PDF con márgenes
                    doc = SimpleDocTemplate(
                        response,
                        pagesize=letter,
                        leftMargin=0.75*inch,
                        rightMargin=0.75*inch,
                        topMargin=0.5*inch,
                        bottomMargin=0.5*inch
                    )
                    styles = getSampleStyleSheet()

                    # Definir estilos personalizados (todos en negrita)
                    styles.add(ParagraphStyle(
                        name='TitleCustom',
                        fontName='Helvetica-Bold',
                        fontSize=14,
        alignment=1,
                        spaceAfter=10,
                        leading=16
                    ))
                    styles.add(ParagraphStyle(
                        name='NormalBold',
                        fontName='Helvetica-Bold',
                        fontSize=10,
                        spaceAfter=4,
                        leading=12
                    ))
                    styles.add(ParagraphStyle(
                        name='NormalCustom',
                        fontName='Helvetica-Bold',
                        fontSize=10,
                        spaceAfter=4,
                        leading=12
                    ))
                    styles.add(ParagraphStyle(
                        name='ActaNumber',
                        fontName='Helvetica-Bold',
                        fontSize=20,
                        alignment=1,
                        textColor=colors.black,
                        spaceAfter=0,
                        leading=24
                    ))
                    styles.add(ParagraphStyle(
                        name='Signature',
                        fontName='Times-Roman',
                        fontSize=10,
                        alignment=1,
                        spaceBefore=10,
                        spaceAfter=4,
                        leading=12
                    ))
                    styles.add(ParagraphStyle(
                        name='SignatureTitle',
                        fontName='Times-Bold',
                        fontSize=10,
                        alignment=1,
                        spaceBefore=4,
                        spaceAfter=4,
                        leading=12
                    ))
                    styles.add(ParagraphStyle(
                        name='SignatureCargo',
                        fontName='Times-Italic',
                        fontSize=9,
                        alignment=1,
                        spaceBefore=2,
                        spaceAfter=2,
                        leading=11
                    ))
                    styles.add(ParagraphStyle(
                        name='TableCell',
                        fontName='Helvetica-Bold',
                        fontSize=9,
                        leading=11,
                        wordWrap='CJK',
                    ))

                    elements = []

                    # --- Encabezado ---
                    logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'images', 'seremi_logo.png')
                    logo = None
                    if os.path.exists(logo_path):
                        logo = Image(logo_path, width=3*cm, height=3*cm)
                        logo.hAlign = 'LEFT'
                    else:
                        logo = Paragraph("Logo no encontrado", styles['NormalCustom'])

                    acta_number = Paragraph(f"N° {numero_acta}", styles['ActaNumber'])
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

                    header_table = Table([
                        [logo, acta_number_table]
                    ], colWidths=[3*inch, 4.5*inch])
                    header_table.setStyle(TableStyle([
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                    ]))
                    elements.append(header_table)

                    elements.append(Spacer(1, 0.2*cm))
                    title = Paragraph("ACTA DE ENTREGA MATERIALES O INSUMOS", styles['TitleCustom'])
                    elements.append(title)

                    elements.append(Spacer(1, 0.3*cm))
                    fecha = Paragraph(
                        f"En Temuco con fecha {datetime.now().strftime('%d-%m-%Y')} se procede a realizar la entrega de los siguientes artículos a:",
                        styles['NormalCustom']
                    )
                    elements.append(fecha)

                    elements.append(Spacer(1, 0.2*cm))
                    departamento_info = Paragraph(
                        f"Sección: {form.cleaned_data['departamento']}",
                        styles['NormalCustom']
                    )
                    elements.append(departamento_info)

                    elements.append(Spacer(1, 0.1*cm))
                    responsable_info = Paragraph(
                        f"Responsable: {form.cleaned_data['responsable']}",
                        styles['NormalCustom']
                    )
                    elements.append(responsable_info)

                    elements.append(Spacer(1, 0.5*cm))
                    elements.append(Paragraph("Datos de Productos", styles['NormalBold']))
                    elements.append(Spacer(1, 0.2*cm))

                    # Preparar los datos de la tabla
                    data = [['Descripción', 'Nro. SISCOM', 'Cantidad', 'Observación']]
                    for item in productos_salida:
                        # Reemplazar \n por <br/> para que ReportLab respete los saltos de línea
                        observacion_text = (item['observacion'] or '-').replace('\n', '<br/>')
                        observacion = Paragraph(observacion_text, styles['TableCell'])
                        data.append([
                            item['descripcion'],
                            item['numero_siscom'],
                            str(item['cantidad']),
                            observacion,
                        ])

                    # Ajustar los anchos de las columnas
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
                    elements.append(table)

                    elements.append(Spacer(1, 4*inch))

                    # Usamos la primera acta para obtener generador y responsable
                    acta = ActaEntrega.objects.filter(numero_acta=numero_acta).first()
                    if not acta:
                        messages.error(request, 'Error: No se pudo encontrar el acta recién creada.')
                        return redirect('salida-productos-seleccion')

                    firma_encargado = Paragraph(
                        f"{acta.generador}",
                        styles['Signature']
                    )
                    firma_encargado_title = Paragraph(
                        "ENCARGADO BODEGA",
                        styles['SignatureTitle']
                    )
                    firma_encargado_line = Paragraph(
                        "_____________________________",
                        styles['Signature']
                    )

                    firma_receptor = Paragraph(
                        f"Sr./Sra. {acta.responsable}",
                        styles['Signature']
                    )
                    firma_receptor_title = Paragraph(
                        "RECEPCIONA CONFORME",
                        styles['SignatureTitle']
                    )

                    responsable_lower = acta.responsable.lower()
                    if 'secretaria' in responsable_lower:
                        cargo = "SECRETARIA DEL DEPARTAMENTO"
                    elif 'jefe' in responsable_lower or 'jefatura' in responsable_lower:
                        cargo = "JEFE DEL DEPARTAMENTO"
                    else:
                        cargo = "RESPONSABLE DEL DEPARTAMENTO"

                    firma_receptor_cargo = Paragraph(
                        cargo,
                        styles['SignatureCargo']
                    )
                    firma_receptor_line = Paragraph(
                        "_____________________________",
                        styles['Signature']
                    )

                    firma_table = Table([
                        [firma_encargado, firma_receptor],
                        [firma_encargado_title, firma_receptor_title],
                        ['', firma_receptor_cargo],
                        [firma_encargado_line, firma_receptor_line]
                    ], colWidths=[3*inch, 3*inch])
                    firma_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('FONTNAME', (0, 0), (-1, -1), 'Times-Roman'),
                        ('FONTSIZE', (0, 0), (-1, -1), 10),
                        ('LEADING', (0, 0), (-1, -1), 12),
                    ]))
                    elements.append(firma_table)

                    doc.build(elements)
                    print("PDF generado exitosamente.")

                    # Limpiar la sesión
                    if 'productos_salida' in request.session:
                        del request.session['productos_salida']
                    
                    return response

                except Exception as e:
                    messages.error(request, f'Error al generar el PDF: {str(e)}')
                    return redirect('salida-productos-seleccion')

            except Exception as e:
                messages.error(request, f'Error al procesar el acta: {str(e)}')
                return redirect('salida-productos-seleccion')
        else:
            messages.error(request, 'Error al generar el acta. Verifica los datos.')
            print(f"Errores del formulario: {form.errors}")
    else:
        form = ActaEntregaForm()

    return render(request, 'accounts/salida_productos_seleccion.html', {
        'form': form,
        'productos_salida': productos_salida,
    })

@login_required
def funcionarios_por_departamento(request):
    departamento = request.GET.get('departamento', '')
    if not departamento:
        return JsonResponse({'error': 'Departamento no especificado'}, status=400)

    # Generamos las opciones de responsable dinámicamente (igual que en el frontend y el formulario)
    responsables = [
        {'nombre': 'Jefatura ' + departamento},
        {'nombre': 'Jefatura ' + departamento + '(s)'},
        {'nombre': 'Secretaria ' + departamento},
        {'nombre': 'Secretaria ' + departamento + '(s)'},
    ]

    # Ajustes específicos para el Departamento de Salud Pública
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
    # Obtener todas las actas con el número de acta especificado
    actas = ActaEntrega.objects.filter(numero_acta=numero_acta)
    if not actas.exists():
        return HttpResponse("Acta no encontrada.", status=404)

    # Obtener la información del acta (usamos la primera para los datos generales)
    acta = actas.first()

    # Preparar los datos de los productos
    productos_salida = []
    for item in actas:
        productos_salida.append({
            'codigo_barra': item.producto.codigo_barra,
            'descripcion': item.producto.descripcion,
            'numero_siscom': item.numero_siscom or '',  # Usar el campo del modelo ActaEntrega
            'cantidad': item.cantidad,
            'observacion': item.observacion or '',  # Usar el campo del modelo ActaEntrega
        })

    # Generar el PDF
    response = HttpResponse(content_type='application/pdf')
    filename = f"Acta_Entrega_Nro_{numero_acta}.pdf"
    encoded_filename = urllib.parse.quote(filename)
    if disposition == 'inline':
        response['Content-Disposition'] = f'inline; filename="{encoded_filename}"'
    else:
        response['Content-Disposition'] = f'attachment; filename="{encoded_filename}"'
    response['Content-Type'] = 'application/pdf; charset=utf-8'

    # Configurar el documento PDF con márgenes
    doc = SimpleDocTemplate(
        response,
        pagesize=letter,
        leftMargin=0.75*inch,
        rightMargin=0.75*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )
    styles = getSampleStyleSheet()

    # Definir estilos personalizados (todos en negrita)
    styles.add(ParagraphStyle(
        name='TitleCustom',
        fontName='Helvetica-Bold',
        fontSize=14,
        alignment=1,
        spaceAfter=10,
        leading=16
    ))
    styles.add(ParagraphStyle(
        name='NormalBold',
        fontName='Helvetica-Bold',
        fontSize=10,
        spaceAfter=4,
        leading=12
    ))
    styles.add(ParagraphStyle(
        name='NormalCustom',
        fontName='Helvetica-Bold',
        fontSize=10,
        spaceAfter=4,
        leading=12
    ))
    styles.add(ParagraphStyle(
        name='ActaNumber',
        fontName='Helvetica-Bold',
        fontSize=20,
        alignment=1,
        textColor=colors.black,
        spaceAfter=0,
        leading=24
    ))
    styles.add(ParagraphStyle(
        name='Signature',
        fontName='Times-Roman',
        fontSize=10,
        alignment=1,
        spaceBefore=10,
        spaceAfter=4,
        leading=12
    ))
    styles.add(ParagraphStyle(
        name='SignatureTitle',
        fontName='Times-Bold',
        fontSize=10,
        alignment=1,
        spaceBefore=4,
        spaceAfter=4,
        leading=12
    ))
    styles.add(ParagraphStyle(
        name='SignatureCargo',
        fontName='Times-Italic',
        fontSize=9,
        alignment=1,
        spaceBefore=2,
        spaceAfter=2,
        leading=11
    ))
    styles.add(ParagraphStyle(
        name='TableCell',
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        wordWrap='CJK',
    ))

    elements = []

    # --- Encabezado ---
    logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'images', 'seremi_logo.png')
    logo = None
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=3*cm, height=3*cm)
        logo.hAlign = 'LEFT'
    else:
        logo = Paragraph("Logo no encontrado", styles['NormalCustom'])

    acta_number = Paragraph(f"N° {numero_acta}", styles['ActaNumber'])
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

    header_table = Table([
        [logo, acta_number_table]
    ], colWidths=[3*inch, 4.5*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    elements.append(header_table)

    elements.append(Spacer(1, 0.2*cm))
    title = Paragraph("ACTA DE ENTREGA MATERIALES O INSUMOS", styles['TitleCustom'])
    elements.append(title)

    elements.append(Spacer(1, 0.3*cm))
    fecha = Paragraph(
        f"En Temuco con fecha {acta.fecha.strftime('%d-%m-%Y')} se procede a realizar la entrega de los siguientes artículos a:",
        styles['NormalCustom']
    )
    elements.append(fecha)

    elements.append(Spacer(1, 0.2*cm))
    departamento_info = Paragraph(
        f"Sección: {acta.departamento}",
        styles['NormalCustom']
    )
    elements.append(departamento_info)

    elements.append(Spacer(1, 0.1*cm))
    responsable_info = Paragraph(
        f"Responsable: {acta.responsable}",
        styles['NormalCustom']
    )
    elements.append(responsable_info)

    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph("Datos de Productos", styles['NormalBold']))
    elements.append(Spacer(1, 0.2*cm))

    # Preparar los datos de la tabla
    data = [['Descripción', 'Nro. SISCOM', 'Cantidad', 'Observación']]
    for item in productos_salida:
        # Reemplazar \n por <br/> para que ReportLab respete los saltos de línea
        observacion_text = (item['observacion'] or '-').replace('\n', '<br/>')
        observacion = Paragraph(observacion_text, styles['TableCell'])
        data.append([
            item['descripcion'],
            item['numero_siscom'],
            str(item['cantidad']),
            observacion,
        ])

    # Ajustar los anchos de las columnas
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
    elements.append(table)

    elements.append(Spacer(1, 4*inch))

    firma_encargado = Paragraph(
        f"{acta.generador}",
        styles['Signature']
    )
    firma_encargado_title = Paragraph(
        "ENCARGADO BODEGA",
        styles['SignatureTitle']
    )
    firma_encargado_line = Paragraph(
        "_____________________________",
        styles['Signature']
    )

    firma_receptor = Paragraph(
        f"Sr./Sra. {acta.responsable}",
        styles['Signature']
    )
    firma_receptor_title = Paragraph(
        "RECEPCIONA CONFORME",
        styles['SignatureTitle']
    )

    responsable_lower = acta.responsable.lower()
    if 'secretaria' in responsable_lower:
        cargo = "SECRETARIA DEL DEPARTAMENTO"
    elif 'jefe' in responsable_lower or 'jefatura' in responsable_lower:
        cargo = "JEFE DEL DEPARTAMENTO"
    else:
        cargo = "RESPONSABLE DEL DEPARTAMENTO"

    firma_receptor_cargo = Paragraph(
        cargo,
        styles['SignatureCargo']
    )
    firma_receptor_line = Paragraph(
        "_____________________________",
        styles['Signature']
    )

    firma_table = Table([
        [firma_encargado, firma_receptor],
        [firma_encargado_title, firma_receptor_title],
        ['', firma_receptor_cargo],
        [firma_encargado_line, firma_receptor_line]
    ], colWidths=[3*inch, 3*inch])
    firma_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), 'Times-Roman'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('LEADING', (0, 0), (-1, -1), 12),
    ]))
    elements.append(firma_table)

    doc.build(elements)
    return response

@login_required
def bincard_buscar(request):
    # Limpiar la sesión si existe productos_salida
    if 'productos_salida' in request.session:
        del request.session['productos_salida']
    
    if request.method == 'POST':
        codigo_barra = request.POST.get('codigo_barra', '').strip()
        
        # Validar que se haya ingresado un código de barra
        if not codigo_barra:
            messages.error(request, 'Por favor, ingrese un código de barra.')
            return render(request, 'accounts/bincard_buscar.html')
        
        # Validar que el código de barra sea numérico
        if not codigo_barra.isdigit():
            messages.error(request, 'El código de barra debe contener solo números.')
            return render(request, 'accounts/bincard_buscar.html')
        
        # Verificar si el producto existe
        try:
            producto = Producto.objects.get(codigo_barra=codigo_barra)
            # Redirigir a la vista de historial con el código de barra
            return redirect('bincard-historial', codigo_barra=codigo_barra)
        except Producto.DoesNotExist:
            messages.error(
                request,
                f'No se encontró un producto con el código de barra {codigo_barra}. '
                f'Puedes <a href="/accounts/registrar-producto/">registrar un nuevo producto</a>.'
            )
            return render(request, 'accounts/bincard_buscar.html')
    
    return render(request, 'accounts/bincard_buscar.html')

@login_required
def buscar_codigos_barra(request):
    """
    Vista auxiliar para devolver sugerencias de códigos de barra para el autocompletado.
    """
    term = request.GET.get('term', '').strip()
    if not term:
        return JsonResponse([], safe=False)
    
    # Buscar productos cuyos códigos de barra comiencen con el término ingresado
    productos = Producto.objects.filter(codigo_barra__startswith=term).order_by('codigo_barra')[:10]
    codigos = [{'label': f"{producto.codigo_barra} - {producto.descripcion}", 'value': producto.codigo_barra} for producto in productos]
    return JsonResponse(codigos, safe=False)

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse
from datetime import datetime
import openpyxl
import urllib.parse
from accounts.models import Producto, Transaccion, ActaEntrega

@login_required
def bincard_historial(request, codigo_barra):
    # Limpiar la sesión si existe productos_salida
    if 'productos_salida' in request.session:
        del request.session['productos_salida']
    
    # Validar que el código de barra sea numérico
    if not codigo_barra.isdigit():
        messages.error(request, 'El código de barra debe contener solo números.')
        return redirect('bincard-buscar')
    
    # Buscar el producto
    try:
        producto = Producto.objects.get(codigo_barra=codigo_barra)
    except Producto.DoesNotExist:
        messages.error(request, 'Producto no encontrado.')
        return redirect('bincard-buscar')
    
    # Obtener transacciones y actas relacionadas con el producto
    transacciones = Transaccion.objects.filter(producto=producto).order_by('fecha')
    actas = ActaEntrega.objects.filter(producto=producto).order_by('fecha')
    
    # Combinar transacciones y actas en una lista de movimientos
    movimientos = []
    saldo = 0  # Saldo inicial
    
    # Procesar transacciones (entradas y salidas)
    for transaccion in transacciones:
        entrada = transaccion.cantidad if transaccion.tipo == 'entrada' else 0
        salida = transaccion.cantidad if transaccion.tipo == 'salida' else 0
        saldo += entrada - salida
        
        # Verificar saldo negativo
        if saldo < 0:
            messages.error(request, f'Error: El saldo no puede ser negativo en la fecha {transaccion.fecha}. Contacte al administrador.')
            return redirect('bincard-buscar')
        
        movimientos.append({
            'fecha': transaccion.fecha,
            'numero_acta': None,
            'rut_proveedor': transaccion.rut_proveedor,
            'departamento': None,
            'entrada': entrada,
            'salida': salida,
            'saldo': saldo,
        })
    
    # Procesar actas (solo salidas)
    for acta in actas:
        saldo -= acta.cantidad
        
        # Verificar saldo negativo
        if saldo < 0:
            messages.error(request, f'Error: El saldo no puede ser negativo en la fecha {acta.fecha}. Contacte al administrador.')
            return redirect('bincard-buscar')
        
        movimientos.append({
            'fecha': acta.fecha,
            'numero_acta': acta.numero_acta,
            'rut_proveedor': None,
            'departamento': acta.departamento,
            'entrada': 0,
            'salida': acta.cantidad,
            'saldo': saldo,
        })
    
    # Ordenar movimientos por fecha
    movimientos.sort(key=lambda x: x['fecha'])
    
    # Calcular totales
    total_entradas = sum(m['entrada'] for m in movimientos)
    total_salidas = sum(m['salida'] for m in movimientos)
    
    # Verificar que el saldo calculado coincida con el stock actual del producto
    if saldo != producto.stock:
        messages.warning(request, f'Advertencia: El saldo calculado ({saldo}) no coincide con el stock actual del producto ({producto.stock}). Contacte al administrador.')
    
    # Manejar la exportación a Excel
    if request.method == 'POST' and 'exportar_excel' in request.POST:
        # Crear un libro de Excel
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"Bincard_{producto.codigo_barra}"
        
        # Definir los encabezados
        headers = ['Fecha', 'N° Acta', 'Proveedor (RUT)', 'Programa/Departamento', 'Entrada', 'Salida', 'Saldo']
        ws.append(headers)
        
        # Estilo para los encabezados
        for col in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col)
            cell.font = openpyxl.styles.Font(bold=True)
            cell.fill = openpyxl.styles.PatternFill(start_color="D3D3D3", end_color="D3D3D3", fill_type="solid")
            cell.alignment = openpyxl.styles.Alignment(horizontal='center')
        
        # Agregar los datos de los movimientos
        for idx, movimiento in enumerate(movimientos, start=2):
            ws.append([
                movimiento['fecha'].strftime('%d-%m-%Y %H:%M'),
                movimiento['numero_acta'] if movimiento['numero_acta'] else '-',
                movimiento['rut_proveedor'] if movimiento['rut_proveedor'] else '-',
                movimiento['departamento'] if movimiento['departamento'] else '-',
                movimiento['entrada'],
                movimiento['salida'],
                movimiento['saldo'],
            ])
        
        # Agregar la fila de totales
        total_row = len(movimientos) + 2
        ws.append(['Total', '', '', '', total_entradas, total_salidas, producto.stock])
        for col in range(1, 8):
            cell = ws.cell(row=total_row, column=col)
            cell.font = openpyxl.styles.Font(bold=True)
            cell.fill = openpyxl.styles.PatternFill(start_color="E7F3FF", end_color="E7F3FF", fill_type="solid")
            cell.alignment = openpyxl.styles.Alignment(horizontal='center')
        
        # Ajustar el ancho de las columnas
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2)
            ws.column_dimensions[column].width = adjusted_width
        
        # Generar el nombre del archivo
        fecha = datetime.now().strftime('%Y-%m-%d')
        filename = f"Bincard_{producto.codigo_barra}_{fecha}.xlsx"
        encoded_filename = urllib.parse.quote(filename)
        
        # Preparar la respuesta
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{encoded_filename}"'
        wb.save(response)
        return response
    
    # Implementar paginación: 20 movimientos por página
    paginator = Paginator(movimientos, 20)
    page = request.GET.get('page')
    
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    context = {
        'producto': producto,
        'page_obj': page_obj,
        'total_entradas': total_entradas,
        'total_salidas': total_salidas,
    }
    return render(request, 'accounts/bincard_historial.html', context)