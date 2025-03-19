# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import ProductoForm, TransaccionForm  # Añadimos TransaccionForm
from .models import Producto, Transaccion

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
    
# formulario forms.py para el submenú "Registrar Producto" del botón "Agregar".
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

# Vista para listar productos y filtrar
@login_required
def listar_productos(request):
    productos = Producto.objects.all()
    query_codigo = request.GET.get('codigo_barra', '')
    query_descripcion = request.GET.get('descripcion', '')

    if query_codigo:
        productos = productos.filter(codigo_barra=query_codigo)
    if query_descripcion:
        productos = productos.filter(descripcion__icontains=query_descripcion)

    # Depuración: Imprimir los productos filtrados (para verificar en la terminal)
    print(f"Productos filtrados: {productos}")
    print(f"Filtro código: {query_codigo}, Filtro descripción: {query_descripcion}")

    context = {
        'productos': productos,
        'query_codigo': query_codigo,
        'query_descripcion': query_descripcion,
    }
    return render(request, 'accounts/listar_productos.html', context)

# Vista para el formulario de agregar stock
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
            # Crear transacción
            transaccion = form.save(commit=False)
            transaccion.producto = producto
            transaccion.tipo = 'entrada'
            transaccion.save()

            # Actualizar stock del producto
            producto.stock += form.cleaned_data['cantidad']
            producto.save()

            # Almacenar el mensaje de éxito y redirigir
            messages.success(request, f'Stock agregado exitosamente. Nueva cantidad: {producto.stock}')
            return redirect('agregar-stock')
        else:
            messages.error(request, 'Error al agregar stock. Verifica los datos.')
    else:
        form = TransaccionForm()

    # Método GET o error en POST: Mostrar el formulario
    return render(request, 'accounts/agregar_stock_detalle.html', {
        'producto': producto,
        'form': form,
    })