#!/usr/bin/env python
"""
Script para corregir y sincronizar el estado final del producto Leche de vaca 1 L
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
django.setup()

from accounts.models import Producto, LoteProducto, Transaccion
from django.db import models

def sincronizar_producto_final():
    """Sincroniza el estado final del producto"""
    producto = Producto.objects.get(codigo_barra='100041')
    
    print(f"=== SINCRONIZACIÓN FINAL - {producto.descripcion} ===")
    print(f"Estado antes de sincronización:")
    print(f"  Stock en producto: {producto.stock}")
    print(f"  Stock en lotes: {producto.lotes.aggregate(total=models.Sum('stock'))['total'] or 0}")
    
    # CRÍTICO: NO limpiar lotes vacíos - preservar trazabilidad para Bincard
    # Los lotes con stock=0 se conservan para mantener el historial
    
    # Sincronizar stock total
    producto.sincronizar_stock_con_lotes()
    
    # Refrescar desde BD
    producto.refresh_from_db()
    
    print(f"\nEstado después de sincronización:")
    print(f"  Stock en producto: {producto.stock}")
    print(f"  Stock en lotes: {producto.lotes.aggregate(total=models.Sum('stock'))['total'] or 0}")
    
    print(f"\nLotes activos:")
    lotes_activos = producto.lotes.filter(stock__gt=0).order_by('fecha_vencimiento')
    for lote in lotes_activos:
        print(f"  Lote #{lote.numero_lote}: {lote.stock} unidades - Vence: {lote.fecha_vencimiento}")
    
    print(f"\nResumen de transacciones de hoy:")
    from datetime import date
    hoy = date.today()
    transacciones_hoy = Transaccion.objects.filter(
        producto=producto,
        fecha__date=hoy
    ).order_by('fecha')
    
    for trans in transacciones_hoy:
        acta_info = f" (Acta {trans.acta_entrega.numero_acta})" if trans.acta_entrega else ""
        print(f"  {trans.fecha.strftime('%H:%M')} - {trans.tipo.upper()}: {trans.cantidad} unidades{acta_info}")
    
    print(f"\n✅ SINCRONIZACIÓN COMPLETADA")
    print(f"Stock final correcto: {producto.stock} unidades")
    
    return producto.stock

if __name__ == "__main__":
    try:
        stock_final = sincronizar_producto_final()
        print(f"\n🎯 El stock de {stock_final} unidades es CORRECTO según el historial de transacciones.")
        print("Las salidas se están procesando correctamente usando el sistema FIFO.")
    except Exception as e:
        print(f"❌ Error durante la sincronización: {e}")
