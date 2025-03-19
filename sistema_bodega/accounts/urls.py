from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='/accounts/login/'), name='logout'),  # Redirige al login después de cerrar sesión
    path('registrar-producto/', views.registrar_producto, name='registrar_producto'),
    path('agregar-stock/', views.listar_productos, name='agregar-stock'),
    path('agregar-stock/<str:codigo_barra>/', views.agregar_stock_detalle, name='agregar-stock-detalle'),

]

