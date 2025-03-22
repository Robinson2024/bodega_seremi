from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('registrar-producto/', views.registrar_producto, name='registrar-producto'),
    path('listar-productos/', views.listar_productos, name='listar-productos'),
    path('agregar-stock/', views.agregar_stock, name='agregar-stock'),  # Apunta a la vista agregar_stock
    path('agregar-stock/<str:codigo_barra>/', views.agregar_stock_detalle, name='agregar-stock-detalle'),  # Apunta a agregar_stock_detalle
    path('salida-productos/', views.salida_productos, name='salida-productos'),
    path('salida-productos/seleccion/', views.salida_productos_seleccion, name='salida-productos-seleccion'),
    path('funcionarios-por-departamento/', views.funcionarios_por_departamento, name='funcionarios-por-departamento'),
    path('listar-actas/', views.listar_actas, name='listar-actas'),
    path('ver-acta-pdf/<int:numero_acta>/<str:disposition>/', views.ver_acta_pdf, name='ver-acta-pdf'),
]