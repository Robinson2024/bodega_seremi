#!/usr/bin/env python
"""
Script para analizar el historial de transacciones y verificar coherencia
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
django.setup()

from accounts.models import Producto, LoteProducto, Transaccion
from django.db import models

def analizar_historial():
    """Analiza el historial de transacciones para verificar coherencia"""
    producto = Producto.objects.get(codigo_barra='100041')
    
    print(f"=== ANÁLISIS DE HISTORIAL - {producto.descripcion} ===")
    print(f"Stock actual en BD: {producto.stock}")
    print(f"Stock en lotes: {producto.lotes.aggregate(total=models.Sum('stock'))['total'] or 0}")
    
    print("\n--- HISTORIAL DE TRANSACCIONES (últimas 10) ---")
    transacciones = Transaccion.objects.filter(producto=producto).order_by('-fecha')[:10]
    
    # Analizar desde la más antigua hacia la más reciente
    for trans in reversed(transacciones):
        acta_info = f" (Acta {trans.acta_entrega.numero_acta})" if trans.acta_entrega else ""
        print(f"{trans.fecha.strftime('%Y-%m-%d %H:%M')} - {trans.tipo.upper()}: {trans.cantidad} unidades{acta_info}")
    
    print("\n--- CÁLCULO MANUAL DEL STOCK ---")
    
    # Buscar el stock base más reciente antes de estas transacciones
    print("Para calcular correctamente, necesitamos ver el stock antes de la última secuencia de transacciones")
    
    # Mostrar solo las transacciones de hoy
    from datetime import date
    hoy = date.today()
    transacciones_hoy = Transaccion.objects.filter(
        producto=producto,
        fecha__date=hoy
    ).order_by('fecha')
    
    print(f"\n--- TRANSACCIONES DE HOY ({hoy}) ---")
    for trans in transacciones_hoy:
        acta_info = f" (Acta {trans.acta_entrega.numero_acta})" if trans.acta_entrega else ""
        print(f"{trans.fecha.strftime('%H:%M')} - {trans.tipo.upper()}: {trans.cantidad} unidades{acta_info}")

def verificar_problema_salida():
    """Verifica si las salidas se están procesando correctamente"""
    producto = Producto.objects.get(codigo_barra='100041')
    
    print(f"\n=== VERIFICACIÓN DE SALIDAS ===")
    
    # Simular una salida pequeña para ver si funciona
    stock_antes = producto.stock
    lotes_antes = list(producto.lotes.filter(stock__gt=0).values('numero_lote', 'stock'))
    
    print(f"Antes de simular salida:")
    print(f"  Stock: {stock_antes}")
    print(f"  Lotes: {lotes_antes}")
    
    # Simular salida de 1 unidad
    print(f"\nSimulando salida de 1 unidad...")
    resultado = producto.reducir_stock_fifo(1)
    
    # Refrescar desde BD
    producto.refresh_from_db()
    
    stock_despues = producto.stock
    lotes_despues = list(producto.lotes.filter(stock__gt=0).values('numero_lote', 'stock'))
    
    print(f"Después de simular salida:")
    print(f"  Stock: {stock_despues}")
    print(f"  Lotes: {lotes_despues}")
    print(f"  Resultado exitoso: {resultado}")
    print(f"  Cambio en stock: {stock_antes - stock_despues}")
    
    # Restaurar el stock original
    print(f"\nRestaurando stock original...")
    producto.stock = stock_antes
    producto.save()
    
    # Restaurar lotes
    for lote_info in lotes_antes:
        lote = producto.lotes.get(numero_lote=lote_info['numero_lote'])
        lote.stock = lote_info['stock']
        lote.save()
    
    print(f"Stock restaurado a: {producto.stock}")

if __name__ == "__main__":
    analizar_historial()
    verificar_problema_salida()
