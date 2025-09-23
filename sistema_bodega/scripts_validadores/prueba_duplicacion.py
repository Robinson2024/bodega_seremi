#!/usr/bin/env python
"""
Prueba específica para verificar la duplicación de stock
Simula la creación de un producto como lo haría el formulario
"""

import os
import sys
import django
from datetime import date, timedelta

# Configurar Django
sys.path.append('c:\\Users\\Robinson Bravo\\Desktop\\bodega_seremi\\sistema_bodega')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
django.setup()

from accounts.models import Producto, LoteProducto
from accounts.forms import ProductoForm

def probar_duplicacion():
    print("=" * 60)
    print("   PRUEBA DE DUPLICACIÓN DE STOCK")
    print("=" * 60)
    print()
    
    # Datos de prueba
    datos_producto = {
        'descripcion': 'Producto Prueba Duplicación',
        'stock': 500,  # Usuario ingresa 500
        'tiene_vencimiento': True,
        'fecha_vencimiento': date.today() + timedelta(days=30),
        'categoria': None
    }
    
    print("🧪 SIMULANDO CREACIÓN DE PRODUCTO:")
    print(f"   • Descripción: {datos_producto['descripcion']}")
    print(f"   • Stock ingresado: {datos_producto['stock']}")
    print(f"   • Fecha vencimiento: {datos_producto['fecha_vencimiento']}")
    print()
    
    # Crear formulario y simular guardado
    form = ProductoForm(data=datos_producto)
    
    if form.is_valid():
        print("✅ Formulario válido")
        
        # Guardar producto
        producto = form.save()
        
        print(f"📦 RESULTADO DESPUÉS DEL GUARDADO:")
        print(f"   • Código: {producto.codigo_barra}")
        print(f"   • Stock en producto: {producto.stock}")
        
        # Verificar lotes
        lotes = producto.lotes.all()
        total_stock_lotes = sum(lote.stock for lote in lotes)
        
        print(f"   • Cantidad de lotes: {lotes.count()}")
        print(f"   • Stock total en lotes: {total_stock_lotes}")
        
        for lote in lotes:
            print(f"     - Lote {lote.numero_lote}: {lote.stock} unidades")
        
        print()
        
        # Verificar resultado
        if producto.stock == 500 and total_stock_lotes == 500:
            print("✅ ¡ÉXITO! No hay duplicación:")
            print("   • Stock producto = Stock lotes = 500")
            print("   • El problema de duplicación está SOLUCIONADO")
        elif producto.stock == 1000 or total_stock_lotes == 1000:
            print("❌ PROBLEMA PERSISTE:")
            print(f"   • Se duplicó el stock: esperado=500, obtenido={producto.stock}")
            print("   • Se requiere corrección adicional")
        else:
            print("⚠️  RESULTADO INESPERADO:")
            print(f"   • Stock producto: {producto.stock}")
            print(f"   • Stock lotes: {total_stock_lotes}")
        
        # Limpiar (eliminar producto de prueba)
        producto.delete()
        print(f"\n🧹 Producto de prueba eliminado")
        
    else:
        print("❌ Error en formulario:")
        for field, errors in form.errors.items():
            print(f"   • {field}: {errors}")
    
    print()
    print("=" * 60)
    print("         PRUEBA COMPLETADA")
    print("=" * 60)

if __name__ == "__main__":
    probar_duplicacion()
