# sistema_bodega/urls.py
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

def redirect_to_accounts(request):
    return redirect('/accounts/')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('', redirect_to_accounts),
]