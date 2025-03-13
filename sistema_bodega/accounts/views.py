from django.shortcuts import render
from django.contrib.auth.views import LoginView

def home(request):
    return render(request, 'accounts/home.html')

class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'  # Usa tu template existente