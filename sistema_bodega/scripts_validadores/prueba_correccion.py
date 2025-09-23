#!/usr/bin/env python
"""
Script para probar la corrección del bincard
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
django.setup()

from accounts.models import Producto, LoteProducto, Transaccion
from django.db import models

def probar_correccion():
    """Prueba la corrección del problema de sincronización"""
    producto = Producto.objects.get(codigo_barra='100041')
    
    print(f"=== ESTADO ANTES DE LA CORRECCIÓN ===")
    print(f"Stock en producto: {producto.stock}")
    print(f"Stock en lotes: {producto.lotes.aggregate(total=models.Sum('stock'))['total'] or 0}")
    
    # Simular una entrada de 100 unidades
    print(f"\n=== SIMULANDO ENTRADA DE 100 UNIDADES ===")
    stock_antes = producto.stock
    
    # Crear un lote con fecha de vencimiento
    from datetime import date, timedelta
    fecha_vencimiento = date.today() + timedelta(days=30)
    
    lote = LoteProducto.objects.create(
        producto=producto,
        numero_lote=producto.get_proximo_numero_lote(),
        fecha_vencimiento=fecha_vencimiento,
        stock=100
    )
    
    # Actualizar stock del producto
    producto.stock += 100
    producto.save()
    
    # Crear transacción de entrada
    Transaccion.objects.create(
        producto=producto,
        tipo='entrada',
        cantidad=100,
        observacion='Entrada de prueba'
    )
    
    print(f"Stock después de entrada: {producto.stock}")
    print(f"Nuevo lote creado: #{lote.numero_lote} con {lote.stock} unidades")
    
    # Simular una salida de 50 unidades
    print(f"\n=== SIMULANDO SALIDA DE 50 UNIDADES ===")
    
    # Usar el método FIFO
    exito = producto.reducir_stock_fifo(50)
    print(f"Reducción FIFO exitosa: {exito}")
    
    # Crear transacción de salida
    Transaccion.objects.create(
        producto=producto,
        tipo='salida',
        cantidad=50,
        observacion='Salida de prueba'
    )
    
    # Refrescar producto
    producto.refresh_from_db()
    
    print(f"Stock después de salida: {producto.stock}")
    print(f"Stock en lotes: {producto.lotes.aggregate(total=models.Sum('stock'))['total'] or 0}")
    
    # Verificar lotes
    print("\nLotes actuales:")
    for lote in producto.lotes.filter(stock__gt=0):
        print(f"  Lote {lote.numero_lote}: {lote.stock} unidades - Vence: {lote.fecha_vencimiento}")
    
    return True

def limpiar_prueba():
    """Limpia las transacciones de prueba"""
    print(f"\n=== LIMPIANDO TRANSACCIONES DE PRUEBA ===")
    
    # Eliminar transacciones de prueba
    Transaccion.objects.filter(observacion__contains='prueba').delete()
    
    # Corregir stock del producto
    producto = Producto.objects.get(codigo_barra='100041')
    producto.actualizar_stock_total()
    
    print(f"Stock después de limpieza: {producto.stock}")
    print("Limpieza completada")

if __name__ == "__main__":
    try:
        probar_correccion()
    except Exception as e:
        print(f"Error durante la prueba: {e}")
    finally:
        limpiar_prueba()
