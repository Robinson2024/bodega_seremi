from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('registrar-producto/', views.registrar_producto, name='registrar-producto'),
    path('listar-productos/', views.listar_productos, name='listar-productos'),
    path('agregar-stock/', views.agregar_stock, name='agregar-stock'),
    path('agregar-stock/<str:codigo_barra>/', views.agregar_stock_detalle, name='agregar-stock-detalle'),
    path('salida-productos/', views.salida_productos, name='salida-productos'),
    path('salida-productos/seleccion/', views.salida_productos_seleccion, name='salida-productos-seleccion'),
    path('funcionarios-por-departamento/', views.funcionarios_por_departamento, name='funcionarios-por-departamento'),
    path('listar-actas/', views.listar_actas, name='listar-actas'),
    path('ver-acta-pdf/<int:numero_acta>/<str:disposition>/', views.ver_acta_pdf, name='ver-acta-pdf'),
    path('bincard/buscar/', views.bincard_buscar, name='bincard-buscar'),
    path('bincard/historial/<str:codigo_barra>/', views.bincard_historial, name='bincard-historial'),
    path('bincard/buscar-codigos/', views.buscar_codigos_barra, name='buscar-codigos-barra'),
    path('agregar-departamento/', views.agregar_departamento, name='agregar-departamento'),
    path('modificar-departamento/', views.modificar_departamento, name='modificar-departamento'),
    path('eliminar-departamento/', views.eliminar_departamento, name='eliminar-departamento'),
    path('listar-usuarios/', views.listar_usuarios, name='listar-usuarios'),
    path('agregar-usuario/', views.agregar_usuario, name='agregar-usuario'),
    path('editar-usuario/<str:rut>/', views.editar_usuario, name='editar-usuario'),
    path('deshabilitar-usuario/<str:rut>/', views.deshabilitar_usuario, name='deshabilitar-usuario'),
    path('verify-password/', views.verify_password, name='verify_password'),
]

# Servir archivos estáticos en modo de desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])