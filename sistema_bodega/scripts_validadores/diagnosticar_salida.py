#!/usr/bin/env python
"""
Script para diagnosticar el problema de visualización de stock en salida de productos.
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
django.setup()

from accounts.models import Producto, LoteProducto

def diagnosticar_vista_salida():
    """Simula lo que ve la vista de salida de productos."""
    print("🔍 DIAGNÓSTICO DE VISTA SALIDA DE PRODUCTOS")
    print("=" * 60)
    
    # Productos críticos mencionados por el usuario
    productos_criticos = ['100037', '100000', '100036']
    
    print("\n📦 PRODUCTOS EN VISTA DE SALIDA:")
    print("-" * 60)
    
    for codigo in productos_criticos:
        try:
            producto = Producto.objects.get(codigo_barra=codigo)
            
            print(f"\n🔹 {producto.descripcion} ({codigo})")
            print(f"   Stock mostrado en vista: {producto.stock}")
            print(f"   Tiene vencimiento: {producto.tiene_vencimiento}")
            
            if producto.tiene_vencimiento:
                lotes = producto.lotes.all()
                stock_lotes = sum(lote.stock for lote in lotes)
                print(f"   Stock real en lotes: {stock_lotes}")
                print(f"   Sincronización: {'✅ OK' if stock_lotes == producto.stock else '❌ ERROR'}")
                
                # Mostrar lotes
                print("   Lotes:")
                for lote in lotes.order_by('fecha_vencimiento'):
                    print(f"     - Lote #{lote.numero_lote}: {lote.stock} unidades (Vence: {lote.fecha_vencimiento})")
            else:
                print("   Stock directo (sin lotes)")
                
            # Simular lo que ve el usuario en la interfaz
            disponible_para_salida = producto.stock > 0
            print(f"   Disponible para salida: {'✅ SÍ' if disponible_para_salida else '❌ NO'}")
            
        except Producto.DoesNotExist:
            print(f"❌ Producto {codigo} no encontrado")
    
    print(f"\n" + "=" * 60)
    print("📊 RESUMEN DEL DIAGNÓSTICO")
    print("=" * 60)
    
    # Estadísticas generales
    total_productos = Producto.objects.count()
    productos_con_stock = Producto.objects.filter(stock__gt=0).count()
    productos_con_vencimiento = Producto.objects.filter(tiene_vencimiento=True).count()
    
    print(f"Total productos: {total_productos}")
    print(f"Productos con stock: {productos_con_stock}")
    print(f"Productos con vencimiento: {productos_con_vencimiento}")
    
    # Verificar problemas de sincronización
    problemas_sync = 0
    for producto in Producto.objects.filter(tiene_vencimiento=True):
        stock_lotes = producto.lotes.aggregate(total=models.Sum('stock'))['total'] or 0
        if stock_lotes != producto.stock:
            problemas_sync += 1
    
    print(f"Problemas de sincronización: {problemas_sync}")
    
    if problemas_sync == 0:
        print("✅ Todos los productos están sincronizados")
    else:
        print(f"⚠️  {problemas_sync} productos con problemas de sincronización")

if __name__ == "__main__":
    try:
        from django.db import models
        diagnosticar_vista_salida()
    except Exception as e:
        print(f"❌ Error durante el diagnóstico: {e}")
        import traceback
        traceback.print_exc()
