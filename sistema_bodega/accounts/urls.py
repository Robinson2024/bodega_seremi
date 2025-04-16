from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Rutas de Autenticación
    path('', views.home, name='home'),  # Página principal (redirecciona según autenticación)
    path('login/', views.CustomLoginView.as_view(), name='login'),  # Vista de inicio de sesión personalizada
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),  # Cierre de sesión con redirección a login
    path('verify-password/', views.verify_password, name='verify_password'),  # Verificación de contraseña

    # Rutas de Gestión de Productos
    path('registrar-producto/', views.registrar_producto, name='registrar-producto'),  # Registrar un nuevo producto
    path('listar-productos/', views.listar_productos, name='listar-productos'),  # Listar todos los productos
    path('agregar-stock/', views.agregar_stock, name='agregar-stock'),  # Vista para agregar stock (selección de producto)
    path('agregar-stock/<str:codigo_barra>/', views.agregar_stock_detalle, name='agregar-stock-detalle'),  # Detalle para agregar stock a un producto específico

    # Rutas de Salida de Productos
    path('salida-productos/', views.salida_productos, name='salida-productos'),  # Vista principal de salida de productos
    path('salida-productos/seleccion/', views.salida_productos_seleccion, name='salida-productos-seleccion'),  # Selección de departamento y responsable para salida
    path('funcionarios-por-departamento/', views.funcionarios_por_departamento, name='funcionarios-por-departamento'),  # Obtener funcionarios por departamento (usado en salida)

    # Rutas de Actas
    path('listar-actas/', views.listar_actas, name='listar-actas'),  # Listar todas las actas de entrega
    path('ver-acta-pdf/<int:numero_acta>/<str:disposition>/', views.ver_acta_pdf, name='ver-acta-pdf'),  # Generar y visualizar PDF de un acta

    # Rutas de Bincard (Historial de Productos)
    path('bincard/buscar/', views.bincard_buscar, name='bincard-buscar'),  # Buscar productos para ver historial
    path('bincard/historial/<str:codigo_barra>/', views.bincard_historial, name='bincard-historial'),  # Ver historial de transacciones de un producto
    path('bincard/buscar-codigos/', views.buscar_codigos_barra, name='buscar-codigos-barra'),  # Búsqueda de códigos de barra (autocompletado)

    # Rutas de Gestión de Departamentos
    path('agregar-departamento/', views.agregar_departamento, name='agregar-departamento'),  # Agregar un nuevo departamento
    path('modificar-departamento/', views.modificar_departamento, name='modificar-departamento'),  # Modificar un departamento existente
    path('eliminar-departamento/', views.eliminar_departamento, name='eliminar-departamento'),  # Eliminar un departamento

    # Rutas de Gestión de Usuarios
    path('listar-usuarios/', views.listar_usuarios, name='listar-usuarios'),  # Listar todos los usuarios
    path('agregar-usuario/', views.agregar_usuario, name='agregar-usuario'),  # Agregar un nuevo usuario
    path('editar-usuario/<str:rut>/', views.editar_usuario, name='editar-usuario'),  # Editar un usuario por RUT
    path('deshabilitar-usuario/<str:rut>/', views.deshabilitar_usuario, name='deshabilitar-usuario'),  # Deshabilitar un usuario por RUT
]

# Servir archivos estáticos en modo de desarrollo
# Esto permite que Django sirva archivos estáticos (CSS, JS, imágenes) cuando DEBUG=True
# Aunque django.contrib.staticfiles lo hace automáticamente, es buena práctica incluirlo explícitamente
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])