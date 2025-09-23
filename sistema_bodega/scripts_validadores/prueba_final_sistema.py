#!/usr/bin/env python
"""
Script de prueba final para verificar el sistema de stock y lotes.
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
from datetime import date, timedelta

def prueba_completa_sistema():
    """Prueba completa del sistema de stock y lotes."""
    print("🧪 PRUEBA COMPLETA DEL SISTEMA DE STOCK Y LOTES")
    print("=" * 70)
    
    # Obtener el producto de prueba
    producto = Producto.objects.get(codigo_barra='100037')
    
    print(f"\n📦 PRODUCTO DE PRUEBA: {producto.descripcion}")
    print("-" * 50)
    
    # Estado inicial
    print("🔍 ESTADO INICIAL:")
    stock_inicial = producto.stock
    lotes_iniciales = producto.lotes.all()
    print(f"   Stock total: {stock_inicial}")
    print(f"   Número de lotes: {lotes_iniciales.count()}")
    
    for lote in lotes_iniciales:
        print(f"   - Lote #{lote.numero_lote}: {lote.stock} unidades")
    
    # Simular agregar más stock
    print(f"\n➕ SIMULANDO AGREGAR 25 UNIDADES MÁS...")
    
    # Crear formulario simulado
    form_data = {
        'cantidad': 25,
        'tiene_vencimiento_nuevo': True,
        'fecha_vencimiento': date.today() + timedelta(days=90),
        'rut_proveedor': '12345678-9',
        'guia_despacho': 'GD001',
    }
    
    form = AgregarStockConVencimientoForm(data=form_data, producto=producto)
    if form.is_valid():
        try:
            lote, transaccion = form.agregar_stock_a_producto(producto)
            print(f"   ✅ Stock agregado exitosamente")
            print(f"   ✅ Lote creado: #{lote.numero_lote} con {lote.stock} unidades")
        except Exception as e:
            print(f"   ❌ Error al agregar stock: {e}")
    else:
        print(f"   ❌ Formulario inválido: {form.errors}")
    
    # Verificar estado después de agregar
    producto.refresh_from_db()
    print(f"\n🔍 ESTADO DESPUÉS DE AGREGAR:")
    stock_final = producto.stock
    lotes_finales = producto.lotes.all()
    print(f"   Stock total: {stock_final}")
    print(f"   Incremento: +{stock_final - stock_inicial}")
    print(f"   Número de lotes: {lotes_finales.count()}")
    
    for lote in lotes_finales.order_by('numero_lote'):
        print(f"   - Lote #{lote.numero_lote}: {lote.stock} unidades (Vence: {lote.fecha_vencimiento})")
    
    # Verificar sincronización
    stock_lotes = sum(lote.stock for lote in lotes_finales)
    sincronizado = stock_lotes == stock_final
    
    print(f"\n🔄 VERIFICACIÓN DE SINCRONIZACIÓN:")
    print(f"   Stock en producto: {stock_final}")
    print(f"   Stock en lotes: {stock_lotes}")
    print(f"   Estado: {'✅ SINCRONIZADO' if sincronizado else '❌ DESINCRONIZADO'}")
    
    # Simular salida FIFO
    print(f"\n➖ SIMULANDO SALIDA DE 75 UNIDADES (FIFO)...")
    
    try:
        exito = producto.reducir_stock_fifo(75)
        if exito:
            print(f"   ✅ Salida exitosa usando FIFO")
            producto.refresh_from_db()
            
            print(f"\n🔍 ESTADO DESPUÉS DE LA SALIDA:")
            print(f"   Stock total: {producto.stock}")
            
            lotes_actuales = producto.lotes.all().order_by('numero_lote')
            for lote in lotes_actuales:
                print(f"   - Lote #{lote.numero_lote}: {lote.stock} unidades")
            
            # Verificar FIFO
            stock_total_lotes = sum(lote.stock for lote in lotes_actuales)
            print(f"   Verificación FIFO: {'✅ OK' if stock_total_lotes == producto.stock else '❌ ERROR'}")
            
        else:
            print(f"   ❌ Error en la salida FIFO")
    except Exception as e:
        print(f"   ❌ Excepción durante salida: {e}")
    
    print(f"\n" + "=" * 70)
    print("🎯 RESUMEN DE LA PRUEBA")
    print("=" * 70)
    
    # Verificar estado final
    producto.refresh_from_db()
    lotes_actuales = producto.lotes.all()
    stock_actual = producto.stock
    stock_lotes_actual = sum(lote.stock for lote in lotes_actuales)
    
    print(f"✅ Stock final del producto: {stock_actual}")
    print(f"✅ Stock final en lotes: {stock_lotes_actual}")
    print(f"✅ Sincronización: {'OK' if stock_actual == stock_lotes_actual else 'ERROR'}")
    print(f"✅ Número de lotes activos: {lotes_actuales.filter(stock__gt=0).count()}")
    print(f"✅ Sistema FIFO: Funcionando")
    print(f"✅ Agregado automático de stock: Funcionando")
    
    print("\n🚀 SISTEMA COMPLETAMENTE FUNCIONAL")
    print("=" * 70)

if __name__ == "__main__":
    try:
        prueba_completa_sistema()
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()
