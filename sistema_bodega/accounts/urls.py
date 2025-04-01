from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

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
]