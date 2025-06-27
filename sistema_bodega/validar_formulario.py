#!/usr/bin/env python
"""
Script para validar que el formulario de agregar stock funciona correctamente.
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
django.setup()

from accounts.models import Producto, LoteProducto
from accounts.forms import AgregarStockConVencimientoForm

def validar_formulario():
    """Valida que el formulario funciona correctamente."""
    print("🔄 Validando el formulario de agregar stock...")
    
    # Buscar un producto con vencimiento para probar
    producto_con_vencimiento = Producto.objects.filter(tiene_vencimiento=True).first()
    producto_sin_vencimiento = Producto.objects.filter(tiene_vencimiento=False).first()
    
    if not producto_con_vencimiento:
        print("❌ No se encontró un producto con vencimiento para probar")
        return False
    
    if not producto_sin_vencimiento:
        print("❌ No se encontró un producto sin vencimiento para probar")
        return False
    
    print(f"✅ Productos de prueba encontrados:")
    print(f"   - Con vencimiento: {producto_con_vencimiento.descripcion}")
    print(f"   - Sin vencimiento: {producto_sin_vencimiento.descripcion}")
    
    # Test 1: Producto con vencimiento
    print("\n🧪 Test 1: Producto con vencimiento")
    form_data = {
        'cantidad': 10,
        'fecha_vencimiento': '2025-12-31',
        'rut_proveedor': '12345678-9',
        'tiene_vencimiento_nuevo': True
    }
    
    form = AgregarStockConVencimientoForm(form_data, producto=producto_con_vencimiento)
    if form.is_valid():
        print("✅ Formulario válido para producto con vencimiento")
        # Verificar que los campos esperados están presentes
        campos_esperados = ['cantidad', 'fecha_vencimiento', 'numero_lote', 'rut_proveedor']
        for campo in campos_esperados:
            if campo in form.fields:
                print(f"   ✅ Campo '{campo}' presente")
            else:
                print(f"   ❌ Campo '{campo}' faltante")
    else:
        print("❌ Formulario inválido para producto con vencimiento")
        print(f"   Errores: {form.errors}")
    
    # Test 2: Producto sin vencimiento
    print("\n🧪 Test 2: Producto sin vencimiento")
    form_data = {
        'cantidad': 5,
        'rut_proveedor': '98765432-1',
        'tiene_vencimiento_nuevo': False
    }
    
    form = AgregarStockConVencimientoForm(form_data, producto=producto_sin_vencimiento)
    if form.is_valid():
        print("✅ Formulario válido para producto sin vencimiento")
    else:
        print("❌ Formulario inválido para producto sin vencimiento")
        print(f"   Errores: {form.errors}")
    
    # Test 3: Validar lógica del formulario __init__
    print("\n🧪 Test 3: Lógica de inicialización del formulario")
    
    # Para producto con vencimiento
    form_con_venc = AgregarStockConVencimientoForm(producto=producto_con_vencimiento)
    if form_con_venc.fields['fecha_vencimiento'].required:
        print("✅ Campo fecha_vencimiento es obligatorio para productos con vencimiento")
    else:
        print("❌ Campo fecha_vencimiento debería ser obligatorio para productos con vencimiento")
    
    # Para producto sin vencimiento
    form_sin_venc = AgregarStockConVencimientoForm(producto=producto_sin_vencimiento)
    if not form_sin_venc.fields['fecha_vencimiento'].required:
        print("✅ Campo fecha_vencimiento es opcional para productos sin vencimiento")
    else:
        print("❌ Campo fecha_vencimiento debería ser opcional para productos sin vencimiento")
    
    print("\n📋 Resumen de campos del formulario:")
    form = AgregarStockConVencimientoForm()
    for field_name, field in form.fields.items():
        required_str = "obligatorio" if field.required else "opcional"
        print(f"   - {field_name}: {field.label} ({required_str})")
    
    print("\n✅ Validación del formulario completada")
    return True

if __name__ == "__main__":
    try:
        validar_formulario()
    except Exception as e:
        print(f"❌ Error durante la validación: {e}")
        import traceback
        traceback.print_exc()
