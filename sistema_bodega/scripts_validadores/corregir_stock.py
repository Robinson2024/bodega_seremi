#!/usr/bin/env python
"""
Script para corregir inconsistencias de stock en el sistema de lotes.
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
django.setup()

from accounts.models import Producto, LoteProducto

def corregir_inconsistencias():
    """Corrige inconsistencias de stock entre productos y lotes."""
    print("🔧 Corrigiendo inconsistencias de stock...")
    
    productos_con_vencimiento = Producto.objects.filter(tiene_vencimiento=True, stock__gt=0)
    productos_corregidos = 0
    
    for producto in productos_con_vencimiento:
        stock_lotes = sum(lote.stock for lote in producto.lotes.all())
        
        if stock_lotes != producto.stock:
            print(f"⚠️  Inconsistencia en {producto.descripcion}:")
            print(f"   Stock producto: {producto.stock}")
            print(f"   Stock lotes: {stock_lotes}")
            
            # Actualizar stock del producto usando el método del modelo
            producto.actualizar_stock_total()
            producto.refresh_from_db()
            
            print(f"   ✅ Corregido: Stock actualizado a {producto.stock}")
            productos_corregidos += 1
    
    print(f"\n📊 Productos corregidos: {productos_corregidos}")

if __name__ == "__main__":
    corregir_inconsistencias()
