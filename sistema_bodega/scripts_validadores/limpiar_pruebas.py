#!/usr/bin/env python
"""
Script para limpiar datos de prueba y restaurar estado correcto
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
django.setup()

from accounts.models import Producto, LoteProducto, Transaccion
from django.db import models

def limpiar_y_restaurar():
    """Limpia datos de prueba y restaura estado correcto"""
    producto = Producto.objects.get(codigo_barra='100041')
    
    print("=== LIMPIEZA Y RESTAURACIÓN ===")
    
    # Eliminar transacciones de prueba
    transacciones_prueba = Transaccion.objects.filter(
        producto=producto,
        observacion__icontains='prueba'
    )
    count_trans = transacciones_prueba.count()
    if count_trans > 0:
        print(f"Eliminando {count_trans} transacciones de prueba")
        transacciones_prueba.delete()
    
    # Eliminar lote #2 si existe (es de prueba)
    lote_prueba = producto.lotes.filter(numero_lote=2).first()
    if lote_prueba:
        print(f"Eliminando lote de prueba #{lote_prueba.numero_lote}")
        lote_prueba.delete()
    
    # Restaurar stock correcto del lote #1
    lote_principal = producto.lotes.filter(numero_lote=1).first()
    if lote_principal:
        lote_principal.stock = 500
        lote_principal.save()
        print(f"Lote #1 restaurado a 500 unidades")
    
    # Restaurar stock del producto
    producto.stock = 500
    producto.save()
    
    print(f"\n=== ESTADO FINAL ===")
    print(f"Stock del producto: {producto.stock}")
    
    stock_lotes = producto.lotes.aggregate(total=models.Sum('stock'))['total'] or 0
    print(f"Stock en lotes: {stock_lotes}")
    
    print("Lotes activos:")
    for lote in producto.lotes.filter(stock__gt=0):
        print(f"  Lote #{lote.numero_lote}: {lote.stock} unidades - Vence: {lote.fecha_vencimiento}")
    
    print("\n✅ RESTAURACIÓN COMPLETADA")
    return True

if __name__ == "__main__":
    limpiar_y_restaurar()
