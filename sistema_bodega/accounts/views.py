# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import ProductoForm, TransaccionForm, SalidaProductoForm, ActaEntregaForm
from .models import Producto, Transaccion, ActaEntrega, Funcionario
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from datetime import datetime
import os

@login_required
def home(request):
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
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto registrado con éxito.')
            return redirect('home')
        else:
            messages.error(request, 'Error al registrar el producto. Verifica los datos.')
    else:
        form = ProductoForm()
    return render(request, 'accounts/registrar_producto.html', {'form': form})

@login_required
def listar_productos(request):
    productos = Producto.objects.all()
    query_codigo = request.GET.get('codigo_barra', '')
    query_descripcion = request.GET.get('descripcion', '')

    if query_codigo:
        productos = productos.filter(codigo_barra=query_codigo)
    if query_descripcion:
        productos = productos.filter(descripcion__icontains=query_descripcion)

    print(f"Productos filtrados: {productos}")
    print(f"Filtro código: {query_codigo}, Filtro descripción: {query_descripcion}")

    context = {
        'productos': productos,
        'query_codigo': query_codigo,
        'query_descripcion': query_descripcion,
    }
    return render(request, 'accounts/listar_productos.html', context)

@login_required
def agregar_stock_detalle(request, codigo_barra):
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
            transaccion.save()

            producto.stock += form.cleaned_data['cantidad']
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
    # Lista de productos a retirar (almacenada en la sesión)
    productos_salida = request.session.get('productos_salida', [])

    # Obtener todos los productos disponibles
    productos = Producto.objects.all()
    query_codigo = request.GET.get('codigo_barra', '')
    query_descripcion = request.GET.get('descripcion', '')

    if query_codigo:
        productos = productos.filter(codigo_barra=query_codigo)
    if query_descripcion:
        productos = productos.filter(descripcion__icontains=query_descripcion)

    # Si se envía un formulario para agregar un producto a la salida
    if request.method == 'POST' and 'agregar_producto' in request.POST:
        form = SalidaProductoForm(request.POST)
        if form.is_valid():
            codigo_barra = request.POST.get('codigo_barra')
            try:
                producto = Producto.objects.get(codigo_barra=codigo_barra)
                # Verificar si el producto ya está en la lista de salida
                if any(item['codigo_barra'] == codigo_barra for item in productos_salida):
                    messages.error(request, 'Este producto ya está en la lista de salida.')
                elif producto.stock == 0:
                    messages.error(request, 'No se puede retirar este producto porque no tiene stock.')
                else:
                    productos_salida.append({
                        'codigo_barra': producto.codigo_barra,
                        'descripcion': producto.descripcion,
                        'stock': producto.stock,
                        'numero_siscom': form.cleaned_data['numero_siscom'],
                        'cantidad': form.cleaned_data['cantidad'],
                        'observacion': form.cleaned_data['observacion'],
                    })
                    request.session['productos_salida'] = productos_salida
                    messages.success(request, 'Producto agregado a la lista de salida.')
            except Producto.DoesNotExist:
                messages.error(request, 'Producto no encontrado.')
        else:
            messages.error(request, 'Error al agregar el producto. Verifica los datos.')
        return redirect('salida-productos')

    # Si se elimina un producto de la lista de salida
    if request.method == 'POST' and 'eliminar_producto' in request.POST:
        codigo_barra = request.POST.get('codigo_barra')
        productos_salida = [item for item in productos_salida if item['codigo_barra'] != codigo_barra]
        request.session['productos_salida'] = productos_salida
        messages.success(request, 'Producto eliminado de la lista de salida.')
        return redirect('salida-productos')

    # Si se presiona "Siguiente"
    if request.method == 'POST' and 'siguiente' in request.POST:
        if not productos_salida:
            messages.error(request, 'Debes agregar al menos un producto para continuar.')
            return redirect('salida-productos')
        return redirect('salida-productos-seleccion')

    form = SalidaProductoForm()
    context = {
        'productos': productos,
        'query_codigo': query_codigo,
        'query_descripcion': query_descripcion,
        'productos_salida': productos_salida,
        'form': form,
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
            # Crear transacciones de salida y actualizar el stock
            for item in productos_salida:
                producto = Producto.objects.get(codigo_barra=item['codigo_barra'])
                transaccion = Transaccion(
                    producto=producto,
                    tipo='salida',
                    cantidad=item['cantidad'],
                    observacion=item['observacion'],
                )
                transaccion.save()
                producto.stock -= item['cantidad']
                producto.save()

            # Generar el número correlativo del acta
            ultimo_acta = ActaEntrega.objects.order_by('-numero_acta').first()
            numero_acta = 1 if not ultimo_acta else ultimo_acta.numero_acta + 1

            # Crear el acta de entrega
            acta = form.save(commit=False)
            acta.numero_acta = numero_acta
            acta.departamento = form.cleaned_data['departamento']
            acta.funcionario = form.cleaned_data['funcionario']
            acta.jefe_subdepartamento = form.cleaned_data['jefe_subdepartamento']
            acta.responsable = 'Administrador' if request.user.username == 'admin' else 'Gersonns Matus'
            acta.save()

            # Guardar los productos en el acta (usamos el primer producto como referencia, pero guardamos todos en el PDF)
            acta.producto = Producto.objects.get(codigo_barra=productos_salida[0]['codigo_barra'])
            acta.cantidad = productos_salida[0]['cantidad']
            acta.save()

            # Generar el PDF
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="acta_entrega_{numero_acta}.pdf"'

            # Crear el PDF
            doc = SimpleDocTemplate(response, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = []

            # Encabezado
            logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'images', 'seremi_logo.png')
            logo = Image(logo_path, width=2*cm, height=2*cm)
            elements.append(logo)

            elements.append(Spacer(1, 0.5*cm))
            title = Paragraph(f"ACTA DE ENTREGA MATERIALES O INSUMOS", styles['Title'])
            elements.append(title)

            elements.append(Spacer(1, 0.2*cm))
            numero = Paragraph(f"N° {numero_acta}", styles['Normal'])
            elements.append(numero)

            elements.append(Spacer(1, 0.5*cm))
            fecha = Paragraph(f"En Temuco con fecha {datetime.now().strftime('%d-%m-%Y')} se procede a realizar la entrega de los siguientes artículos a:", styles['Normal'])
            elements.append(fecha)

            elements.append(Spacer(1, 0.5*cm))
            funcionario_info = Paragraph(f"Funcionario: {acta.funcionario}", styles['Normal'])
            elements.append(funcionario_info)

            elements.append(Spacer(1, 0.2*cm))
            departamento_info = Paragraph(f"Sección: {acta.departamento}", styles['Normal'])
            elements.append(departamento_info)

            # Tabla de productos
            elements.append(Spacer(1, 1*cm))
            data = [['Descripción', 'Nro. SISCOM', 'Cantidad Entregada', 'Observación']]
            for item in productos_salida:
                data.append([
                    item['descripcion'],
                    item['numero_siscom'],
                    str(item['cantidad']),
                    item['observacion'] or '-',
                ])

            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(table)

            # Firmas (en la última página)
            elements.append(Spacer(1, 2*cm))
            firma_encargado = Paragraph(f"{'Administrador' if request.user.username == 'admin' else 'Gersonns Matus'}<br/>ENCARGADO BODEGA", styles['Normal'])
            firma_receptor = Paragraph(f"{acta.jefe_subdepartamento}<br/>JEFE SUBDEPTO. ADMINISTRACIÓN INTERNA", styles['Normal'])
            firma_table = Table([[firma_encargado, firma_receptor]], colWidths=[200, 200])
            firma_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
            ]))
            elements.append(firma_table)

            # Construir el PDF
            doc.build(elements)

            # Limpiar la sesión
            request.session['productos_salida'] = []
            messages.success(request, 'Acta generada exitosamente.')
            return response
        else:
            messages.error(request, 'Error al generar el acta. Verifica los datos.')
    else:
        form = ActaEntregaForm()

    return render(request, 'accounts/salida_productos_seleccion.html', {
        'form': form,
        'productos_salida': productos_salida,
    })

@login_required
def funcionarios_por_departamento(request):
    departamento = request.GET.get('departamento', '')
    funcionarios = Funcionario.objects.filter(departamento=departamento, es_jefe=False)
    data = {
        'funcionarios': [{'nombre': f.nombre} for f in funcionarios]
    }
    return JsonResponse(data)