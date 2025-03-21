from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='/accounts/login/'), name='logout'),
    path('registrar-producto/', views.registrar_producto, name='registrar_producto'),
    path('agregar-stock/', views.listar_productos, name='agregar-stock'),
    path('agregar-stock/<str:codigo_barra>/', views.agregar_stock_detalle, name='agregar-stock-detalle'),
    path('salida-productos/', views.salida_productos, name='salida-productos'),
    path('salida-productos/seleccion/', views.salida_productos_seleccion, name='salida-productos-seleccion'),
    path('funcionarios-por-departamento/', views.funcionarios_por_departamento, name='funcionarios-por-departamento'),
]