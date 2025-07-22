#!/usr/bin/env python
"""
DIAGNÓSTICO ESPECÍFICO - REGISTRO DE PRODUCTOS
Identifica problemas específicos en el registro de productos

Autor: Sistema Bodega SEREMI
Fecha: 22 de julio de 2025
"""

import os
import sys
import django
import random
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from accounts.models import Producto

User = get_user_model()

def diagnosticar_registro_productos():
    """Diagnóstico completo del registro de productos"""
    print("🔍 DIAGNÓSTICO DE REGISTRO DE PRODUCTOS")
    print("="*50)
    
    client = Client()
    
    try:
        # 1. Crear usuario admin de prueba
        print("\n1. Creando usuario admin...")
        try:
            User.objects.filter(username='diag_admin').delete()
            admin_user = User.objects.create_user(
                username='diag_admin',
                password='admin123',
                email='diag@test.com',
                is_staff=True,
                is_superuser=True,
                rut='99999999-9',
                nombre='Diagnóstico Admin'
            )
            print("✅ Usuario admin creado")
        except Exception as e:
            print(f"❌ Error creando usuario: {e}")
            return False
        
        # 2. Hacer login
        print("\n2. Realizando login...")
        login_result = client.login(username='diag_admin', password='admin123')
        if login_result:
            print("✅ Login exitoso")
        else:
            print("❌ Login falló")
            return False
        
        # 3. Acceder a la página de registro
        print("\n3. Accediendo a página de registro...")
        try:
            response = client.get(reverse('registrar-producto'))
            print(f"✅ Página accesible. Status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"⚠️  Status code inesperado: {response.status_code}")
                if hasattr(response, 'content'):
                    print(f"Contenido: {response.content.decode()[:500]}...")
        except Exception as e:
            print(f"❌ Error accediendo a página: {e}")
            return False
        
        # 4. Probar registro de producto
        print("\n4. Probando registro de producto...")
        codigo_barra = f'DIAG{random.randint(1000, 9999)}'
        
        datos_producto = {
            'codigo_barra': codigo_barra,
            'descripcion': 'Producto Diagnóstico - Test de registro de productos del sistema',
            'stock': 0,
            'rut_proveedor': '12345678-9',
            'tiene_vencimiento': True
        }
        
        print(f"Datos a enviar: {datos_producto}")
        
        try:
            response = client.post(
                reverse('registrar-producto'),
                datos_producto,
                follow=True
            )
            print(f"✅ Formulario enviado. Status: {response.status_code}")
            
            # Mostrar información de respuesta
            if hasattr(response, 'redirect_chain'):
                print(f"Redirects: {response.redirect_chain}")
            
            # Mostrar contenido si hay errores
            if response.status_code != 200:
                print(f"Contenido respuesta: {response.content.decode()[:1000]}...")
            
        except Exception as e:
            print(f"❌ Error enviando formulario: {e}")
            return False
        
        # 5. Verificar si el producto se creó
        print("\n5. Verificando producto en base de datos...")
        try:
            # Buscar por código de barra
            producto = Producto.objects.filter(codigo_barra=codigo_barra).first()
            
            if producto:
                print("✅ Producto encontrado en BD!")
                print(f"   ID: {producto.id}")
                print(f"   Código: {producto.codigo_barra}")
                print(f"   Descripción: {producto.descripcion}")
                print(f"   Stock: {producto.stock}")
                print(f"   RUT Proveedor: {producto.rut_proveedor}")
                print(f"   Tiene vencimiento: {producto.tiene_vencimiento}")
                return True
            else:
                print("❌ Producto NO encontrado en BD")
                
                # Mostrar productos recientes para debug
                productos_recientes = Producto.objects.all().order_by('-id')[:5]
                print(f"\nÚltimos 5 productos en BD:")
                for p in productos_recientes:
                    print(f"   {p.id}: {p.codigo_barra} - {p.descripcion[:50]}")
                
                return False
                
        except Exception as e:
            print(f"❌ Error verificando en BD: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Limpiar datos de prueba
        try:
            User.objects.filter(username='diag_admin').delete()
            Producto.objects.filter(codigo_barra__startswith='DIAG').delete()
            print("\n🧹 Datos de prueba eliminados")
        except:
            pass

def verificar_formulario_registro():
    """Verifica la estructura del formulario de registro"""
    print("\n🔍 VERIFICANDO FORMULARIO DE REGISTRO")
    print("="*50)
    
    client = Client()
    
    try:
        # Crear usuario y hacer login
        User.objects.filter(username='form_test').delete()
        admin_user = User.objects.create_user(
            username='form_test',
            password='admin123',
            email='form@test.com',
            is_staff=True,
            is_superuser=True,
            rut='88888888-8',
            nombre='Form Test'
        )
        
        client.login(username='form_test', password='admin123')
        
        # Obtener formulario
        response = client.get(reverse('registrar-producto'))
        
        if response.status_code == 200:
            content = response.content.decode()
            
            # Buscar campos del formulario
            campos_esperados = [
                'codigo_barra',
                'descripcion', 
                'stock',
                'rut_proveedor',
                'tiene_vencimiento'
            ]
            
            print("Campos encontrados en formulario:")
            for campo in campos_esperados:
                if f'name="{campo}"' in content or f"name='{campo}'" in content:
                    print(f"✅ {campo}")
                else:
                    print(f"❌ {campo} - NO ENCONTRADO")
            
            # Buscar action del formulario
            if 'action=' in content:
                import re
                actions = re.findall(r'action="([^"]*)"', content)
                print(f"\nActions encontradas: {actions}")
            
            # Buscar método del formulario
            if 'method=' in content:
                import re
                methods = re.findall(r'method="([^"]*)"', content)
                print(f"Métodos encontrados: {methods}")
                
        else:
            print(f"❌ Error accediendo al formulario: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error verificando formulario: {e}")
    finally:
        try:
            User.objects.filter(username='form_test').delete()
        except:
            pass

def main():
    """Función principal"""
    print("DIAGNÓSTICO ESPECÍFICO - REGISTRO DE PRODUCTOS")
    print("Fecha:", datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    print("="*60)
    
    # Ejecutar diagnósticos
    resultado_registro = diagnosticar_registro_productos()
    verificar_formulario_registro()
    
    print("\n" + "="*60)
    print("RESUMEN DEL DIAGNÓSTICO")
    print("="*60)
    
    if resultado_registro:
        print("✅ REGISTRO DE PRODUCTOS: FUNCIONANDO")
    else:
        print("❌ REGISTRO DE PRODUCTOS: CON PROBLEMAS")
    
    print("\n🏁 Diagnóstico completado")

if __name__ == "__main__":
    main()
