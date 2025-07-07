#!/usr/bin/env python
"""
Script para diagnosticar el problema de salidas de stock
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
django.setup()

from accounts.models import Producto, LoteProducto, Transaccion, ActaEntrega
from django.db import models
from datetime import datetime, date

def diagnosticar_producto():
    """Diagnostica el estado del producto Leche de vaca 1 L"""
    try:
        producto = Producto.objects.get(codigo_barra='100041')
        print(f"=== DIAGNÓSTICO PRODUCTO: {producto.descripcion} ===")
        print(f"Código: {producto.codigo_barra}")
        print(f"Stock actual: {producto.stock}")
        print(f"Tiene vencimiento: {producto.tiene_vencimiento}")
        
        print("\n--- LOTES ---")
        lotes = producto.lotes.all().order_by('numero_lote')
        total_stock_lotes = 0
        for lote in lotes:
            print(f"Lote {lote.numero_lote}: {lote.stock} unidades - Vence: {lote.fecha_vencimiento}")
            total_stock_lotes += lote.stock
        
        print(f"\nStock total en lotes: {total_stock_lotes}")
        print(f"Diferencia: {producto.stock - total_stock_lotes}")
        
        print("\n--- TRANSACCIONES RECIENTES ---")
        transacciones = Transaccion.objects.filter(producto=producto).order_by('-fecha')[:10]
        for trans in transacciones:
            acta_info = f" (Acta {trans.acta_entrega.numero_acta})" if trans.acta_entrega else ""
            print(f"{trans.fecha.strftime('%Y-%m-%d %H:%M')} - {trans.tipo.upper()}: {trans.cantidad} unidades{acta_info}")
        
        print("\n--- ACTAS DE ENTREGA RECIENTES ---")
        actas = ActaEntrega.objects.filter(producto=producto).order_by('-fecha')[:5]
        for acta in actas:
            print(f"Acta {acta.numero_acta} - {acta.fecha.strftime('%Y-%m-%d %H:%M')} - {acta.cantidad} unidades - {acta.departamento}")
        
        return producto
        
    except Producto.DoesNotExist:
        print("Error: Producto con código 100041 no encontrado")
        return None

def simular_salida(producto, cantidad):
    """Simula una salida para verificar la funcionalidad"""
    print(f"\n=== SIMULANDO SALIDA DE {cantidad} UNIDADES ===")
    print(f"Stock antes: {producto.stock}")
    
    # Mostrar lotes antes
    print("Lotes antes:")
    for lote in producto.lotes.filter(stock__gt=0):
        print(f"  Lote {lote.numero_lote}: {lote.stock} unidades")
    
    # Ejecutar reducción de stock
    exito = producto.reducir_stock_fifo(cantidad)
    
    # Refrescar desde DB
    producto.refresh_from_db()
    
    print(f"Stock después: {producto.stock}")
    print(f"Operación exitosa: {exito}")
    
    # Mostrar lotes después
    print("Lotes después:")
    for lote in producto.lotes.filter(stock__gt=0):
        print(f"  Lote {lote.numero_lote}: {lote.stock} unidades")

def corregir_sincronizacion(producto):
    """Corrige la sincronización de stock"""
    print(f"\n=== CORRIGIENDO SINCRONIZACIÓN ===")
    print(f"Stock actual del producto: {producto.stock}")
    
    # Calcular stock real desde lotes
    total_lotes = producto.lotes.aggregate(total=models.Sum('stock'))['total'] or 0
    print(f"Stock total en lotes: {total_lotes}")
    
    if producto.stock != total_lotes:
        print(f"¡DESINCRONIZACIÓN DETECTADA! Diferencia: {producto.stock - total_lotes}")
        producto.stock = total_lotes
        producto.save()
        print(f"Stock corregido a: {producto.stock}")
    else:
        print("Stock sincronizado correctamente")

if __name__ == "__main__":
    producto = diagnosticar_producto()
    if producto:
        corregir_sincronizacion(producto)
