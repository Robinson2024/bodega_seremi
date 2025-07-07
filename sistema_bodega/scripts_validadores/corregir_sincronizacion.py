#!/usr/bin/env python
"""
Script para corregir la desincronización de stock entre productos y lotes.
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
django.setup()

from accounts.models import Producto, LoteProducto

def corregir_sincronizacion_stock():
    """Corrige la sincronización de stock entre productos y sus lotes."""
    print("🔧 CORRECCIÓN DE SINCRONIZACIÓN DE STOCK")
    print("=" * 60)
    
    productos_con_vencimiento = Producto.objects.filter(tiene_vencimiento=True)
    problemas_encontrados = 0
    productos_corregidos = 0
    
    print(f"\n📊 Analizando {productos_con_vencimiento.count()} productos con vencimiento...")
    
    for producto in productos_con_vencimiento:
        # Calcular stock real en lotes
        stock_lotes = producto.lotes.aggregate(total=models.Sum('stock'))['total'] or 0
        stock_producto = producto.stock
        
        if stock_lotes != stock_producto:
            problemas_encontrados += 1
            print(f"\n❌ PROBLEMA ENCONTRADO:")
            print(f"   Producto: {producto.descripcion} ({producto.codigo_barra})")
            print(f"   Stock en producto: {stock_producto}")
            print(f"   Stock real en lotes: {stock_lotes}")
            print(f"   Diferencia: {stock_producto - stock_lotes}")
            
            # Mostrar detalle de lotes
            lotes = producto.lotes.all()
            print(f"   Lotes ({lotes.count()}):")
            for lote in lotes:
                print(f"     - Lote #{lote.numero_lote}: {lote.stock} unidades (Vence: {lote.fecha_vencimiento})")
            
            # Corregir el stock del producto
            stock_anterior = producto.stock
            producto.stock = stock_lotes
            producto.save()
            productos_corregidos += 1
            
            print(f"   ✅ CORREGIDO: {stock_anterior} → {stock_lotes}")
        else:
            print(f"✅ {producto.descripcion}: Stock sincronizado ({stock_producto} unidades)")
    
    print(f"\n" + "=" * 60)
    print(f"📊 RESUMEN DE CORRECCIÓN:")
    print(f"   - Productos analizados: {productos_con_vencimiento.count()}")
    print(f"   - Problemas encontrados: {problemas_encontrados}")
    print(f"   - Productos corregidos: {productos_corregidos}")
    
    if problemas_encontrados == 0:
        print("   🎉 ¡Todos los productos están sincronizados!")
    else:
        print(f"   ✅ Sincronización completada exitosamente")
    
    print("=" * 60)

def verificar_productos_criticos():
    """Verifica productos específicos mencionados por el usuario."""
    print("\n🔍 VERIFICACIÓN DE PRODUCTOS CRÍTICOS")
    print("=" * 40)
    
    # Verificar productos específicos
    productos_criticos = [
        '100037',  # Agua de baño 5 Litros
        '100000',  # Alcohol gel 1 litro
        '100036',  # Jabón líquido 1 litro
    ]
    
    for codigo in productos_criticos:
        try:
            producto = Producto.objects.get(codigo_barra=codigo)
            if producto.tiene_vencimiento:
                stock_lotes = producto.lotes.aggregate(total=models.Sum('stock'))['total'] or 0
                print(f"\n📦 {producto.descripcion}:")
                print(f"   Stock producto: {producto.stock}")
                print(f"   Stock lotes: {stock_lotes}")
                print(f"   Estado: {'✅ Sincronizado' if stock_lotes == producto.stock else '❌ Desincronizado'}")
            else:
                print(f"\n📦 {producto.descripcion}: Sin vencimiento (OK)")
        except Producto.DoesNotExist:
            print(f"\n❌ Producto {codigo} no encontrado")

if __name__ == "__main__":
    try:
        from django.db import models
        corregir_sincronizacion_stock()
        verificar_productos_criticos()
    except Exception as e:
        print(f"❌ Error durante la corrección: {e}")
        import traceback
        traceback.print_exc()
