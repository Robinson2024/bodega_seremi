#!/usr/bin/env python
"""
Script para verificar que todas las vistas muestren el stock correcto
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
django.setup()

from accounts.models import Producto, LoteProducto, Transaccion
from django.db import models

def verificar_stock_en_todas_las_vistas():
    """Verifica el stock en todas las fuentes posibles"""
    producto = Producto.objects.get(codigo_barra='100041')
    
    print(f"=== VERIFICACIÓN COMPLETA DE STOCK - {producto.descripcion} ===")
    
    # 1. Stock directo del producto
    stock_producto = producto.stock
    print(f"1. Stock en modelo Producto: {stock_producto}")
    
    # 2. Stock calculado desde lotes
    stock_lotes = producto.lotes.aggregate(total=models.Sum('stock'))['total'] or 0
    print(f"2. Stock calculado desde lotes: {stock_lotes}")
    
    # 3. Lotes individuales
    print(f"3. Lotes individuales:")
    lotes_activos = producto.lotes.filter(stock__gt=0)
    for lote in lotes_activos:
        print(f"   Lote #{lote.numero_lote}: {lote.stock} unidades (vence {lote.fecha_vencimiento})")
    
    # 4. Stock según método del producto
    producto.actualizar_stock_total()
    producto.refresh_from_db()
    stock_actualizado = producto.stock
    print(f"4. Stock después de actualizar_stock_total(): {stock_actualizado}")
    
    # 5. Verificar consistencia
    print(f"\n=== VERIFICACIÓN DE CONSISTENCIA ===")
    
    todas_iguales = (stock_producto == stock_lotes == stock_actualizado)
    
    if todas_iguales:
        print(f"✅ TODAS LAS FUENTES COINCIDEN: {stock_producto} unidades")
        print("   - Modelo Producto ✓")
        print("   - Suma de lotes ✓") 
        print("   - Método actualización ✓")
    else:
        print("❌ INCONSISTENCIA DETECTADA:")
        print(f"   - Modelo Producto: {stock_producto}")
        print(f"   - Suma de lotes: {stock_lotes}")
        print(f"   - Después actualización: {stock_actualizado}")
    
    # 6. Estado de vencimientos
    print(f"\n=== INFORMACIÓN DE VENCIMIENTOS ===")
    if producto.tiene_vencimiento:
        estado = producto.get_estado_vencimiento_completo()
        proximo_venc = producto.get_proximo_vencimiento()
        print(f"Estado de vencimiento: {estado}")
        print(f"Próximo vencimiento: {proximo_venc}")
        
        lotes_detalle = producto.get_lotes_detalle()
        if lotes_detalle:
            print("Detalle de lotes:")
            for lote_info in lotes_detalle:
                print(f"  Lote #{lote_info['numero_lote']}: {lote_info['stock']} unidades - {lote_info['estado']}")
    
    return stock_actualizado

def limpiar_final():
    """Limpieza final para asegurar consistencia"""
    producto = Producto.objects.get(codigo_barra='100041')
    
    print(f"\n=== SINCRONIZACIÓN FINAL ===")
    
    # CRÍTICO: NO limpiar lotes vacíos - preservar trazabilidad para Bincard
    # Los lotes con stock=0 se conservan para mantener el historial
    print("✅ Lotes vacíos conservados para trazabilidad")
    
    # Sincronizar stock total
    producto.sincronizar_stock_con_lotes()
    print("✅ Stock sincronizado con lotes")
    
    # Verificar estado final
    stock_final = producto.stock
    stock_lotes_final = producto.lotes.aggregate(total=models.Sum('stock'))['total'] or 0
    
    print(f"\nEstado final:")
    print(f"  Stock en producto: {stock_final}")
    print(f"  Stock en lotes: {stock_lotes_final}")
    
    if stock_final == stock_lotes_final:
        print(f"✅ SINCRONIZACIÓN PERFECTA: {stock_final} unidades")
    else:
        print(f"❌ Aún hay inconsistencia")
    
    return stock_final

if __name__ == "__main__":
    stock_verificado = verificar_stock_en_todas_las_vistas()
    stock_final = limpiar_final()
    
    print(f"\n🎯 CONCLUSIÓN:")
    print(f"El producto 'Leche de vaca 1 L' debe mostrar {stock_final} unidades en TODAS las vistas:")
    print("  - Dashboard")
    print("  - Salida de productos") 
    print("  - Control de vencimientos")
    print("  - Bincard")
    print("  - Reportes Excel")
