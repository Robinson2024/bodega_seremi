#!/usr/bin/env python
"""
Script para diagnosticar y corregir la desincronización completa
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
django.setup()

from accounts.models import Producto, LoteProducto, Transaccion
from django.db import models

def diagnosticar_completo():
    """Diagnóstico completo del estado del producto"""
    producto = Producto.objects.get(codigo_barra='100041')
    
    print(f"=== DIAGNÓSTICO COMPLETO - {producto.descripcion} ===")
    
    # Estado actual en base de datos
    print(f"\n1. ESTADO EN BASE DE DATOS:")
    print(f"   Stock en producto: {producto.stock}")
    
    # Stock calculado desde lotes
    stock_lotes = producto.lotes.aggregate(total=models.Sum('stock'))['total'] or 0
    print(f"   Stock en lotes: {stock_lotes}")
    
    # Lotes individuales
    print(f"\n2. LOTES INDIVIDUALES:")
    for lote in producto.lotes.all().order_by('numero_lote'):
        estado = f"ACTIVO ({lote.stock} unidades)" if lote.stock > 0 else "VACÍO (0 unidades)"
        print(f"   Lote #{lote.numero_lote}: {estado} - Vence: {lote.fecha_vencimiento}")
    
    # Cálculo manual desde transacciones
    print(f"\n3. CÁLCULO DESDE TRANSACCIONES:")
    transacciones = Transaccion.objects.filter(producto=producto).order_by('fecha')
    
    stock_calculado = 0
    print("   Historial completo:")
    for trans in transacciones:
        if trans.tipo == 'entrada':
            stock_calculado += trans.cantidad
            operacion = f"+{trans.cantidad}"
        else:
            stock_calculado -= trans.cantidad
            operacion = f"-{trans.cantidad}"
        
        acta_info = f" (Acta {trans.acta_entrega.numero_acta})" if trans.acta_entrega else ""
        print(f"   {trans.fecha.strftime('%Y-%m-%d %H:%M')} - {trans.tipo.upper()}: {operacion} = {stock_calculado}{acta_info}")
    
    print(f"\n4. RESUMEN:")
    print(f"   Stock en producto BD: {producto.stock}")
    print(f"   Stock suma de lotes: {stock_lotes}")
    print(f"   Stock calculado transacciones: {stock_calculado}")
    
    # Detectar inconsistencias
    print(f"\n5. INCONSISTENCIAS:")
    if producto.stock != stock_lotes:
        print(f"   ❌ Producto vs Lotes: {producto.stock} ≠ {stock_lotes}")
    else:
        print(f"   ✅ Producto vs Lotes: Sincronizado")
    
    if stock_calculado != stock_lotes:
        print(f"   ⚠️  Transacciones vs Lotes: {stock_calculado} ≠ {stock_lotes}")
        print(f"      Esto puede indicar transacciones de prueba no limpiadas")
    else:
        print(f"   ✅ Transacciones vs Lotes: Coherente")
    
    return producto, stock_lotes, stock_calculado

def corregir_sincronizacion():
    """Corrige la sincronización estableciendo el stock correcto"""
    producto = Producto.objects.get(codigo_barra='100041')
    
    print(f"\n=== CORRECCIÓN DE SINCRONIZACIÓN ===")
    
    # Primero, limpiar lotes vacíos
    lotes_vacios = producto.lotes.filter(stock=0)
    if lotes_vacios.exists():
        count = lotes_vacios.count()
        lotes_vacios.delete()
        print(f"✅ Eliminados {count} lotes vacíos")
    
    # Calcular stock real desde lotes activos
    stock_real_lotes = producto.lotes.aggregate(total=models.Sum('stock'))['total'] or 0
    print(f"Stock real desde lotes: {stock_real_lotes}")
    
    # Determinar el stock correcto basado en el historial VÁLIDO
    # Eliminar transacciones de prueba si existen
    trans_prueba = Transaccion.objects.filter(
        producto=producto,
        observacion__icontains='prueba'
    )
    if trans_prueba.exists():
        count = trans_prueba.count()
        trans_prueba.delete()
        print(f"✅ Eliminadas {count} transacciones de prueba")
    
    # Recalcular desde transacciones válidas
    transacciones_validas = Transaccion.objects.filter(producto=producto).order_by('fecha')
    stock_correcto = 0
    
    for trans in transacciones_validas:
        if trans.tipo == 'entrada':
            stock_correcto += trans.cantidad
        else:
            stock_correcto -= trans.cantidad
    
    print(f"Stock correcto según historial válido: {stock_correcto}")
    
    # Decidir cuál es el stock correcto
    # Si hay diferencia, usar el stock calculado desde transacciones válidas
    if stock_real_lotes != stock_correcto:
        print(f"⚠️  Detectada inconsistencia: Lotes={stock_real_lotes}, Historial={stock_correcto}")
        print(f"🔧 Usando stock del historial como referencia: {stock_correcto}")
        
        # Ajustar lotes para que coincidan con el historial
        lote_principal = producto.lotes.first()
        if lote_principal:
            lote_principal.stock = stock_correcto
            lote_principal.save()
            print(f"✅ Lote #{lote_principal.numero_lote} ajustado a {stock_correcto} unidades")
        
        stock_final = stock_correcto
    else:
        stock_final = stock_real_lotes
    
    # Actualizar stock del producto
    producto.stock = stock_final
    producto.save()
    
    print(f"\n✅ SINCRONIZACIÓN COMPLETADA")
    print(f"Stock final establecido: {stock_final} unidades")
    
    return stock_final

if __name__ == "__main__":
    # Diagnóstico
    producto, stock_lotes, stock_calculado = diagnosticar_completo()
    
    # Corrección
    stock_final = corregir_sincronizacion()
    
    print(f"\n🎯 RESULTADO FINAL:")
    print(f"El producto {producto.descripcion} tiene {stock_final} unidades correctamente sincronizadas")
    print(f"Todas las vistas ahora deberían mostrar {stock_final} unidades")
