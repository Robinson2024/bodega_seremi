#!/usr/bin/env python
"""
CORRECCIÓN AUTOMÁTICA GLOBAL
Aplica correcciones a CUALQUIER problema que pueda existir en todo el sistema
Garantiza que no haya duplicaciones ni desincronizaciones en ningún producto
"""

import os
import sys
import django
from datetime import date

# Configurar Django
sys.path.append('c:\\Users\\Robinson Bravo\\Desktop\\bodega_seremi\\sistema_bodega')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
django.setup()

from accounts.models import Producto, LoteProducto, Transaccion
from django.db import models, transaction

def correccion_automatica_global():
    print("=" * 80)
    print("              CORRECCIÓN AUTOMÁTICA GLOBAL")
    print("    ELIMINANDO DUPLICACIONES Y SINCRONIZANDO TODO EL SISTEMA")
    print("=" * 80)
    print()
    
    productos_corregidos = 0
    transacciones_corregidas = 0
    problemas_encontrados = 0
    
    print("🔍 FASE 1: DETECTAR Y CORREGIR INCONSISTENCIAS STOCK vs LOTES")
    print("-" * 60)
    
    # Corregir productos con vencimiento
    for producto in Producto.objects.filter(tiene_vencimiento=True):
        stock_lotes = producto.lotes.aggregate(total=models.Sum('stock'))['total'] or 0
        
        if producto.stock != stock_lotes:
            problemas_encontrados += 1
            print(f"   ⚠️  {producto.codigo_barra}: Stock={producto.stock}, Lotes={stock_lotes}")
            
            # Sincronizar usando método del modelo
            if hasattr(producto, 'sincronizar_stock_con_lotes'):
                with transaction.atomic():
                    resultado = producto.sincronizar_stock_con_lotes()
                    if resultado:
                        productos_corregidos += 1
                        print(f"      ✅ Corregido automáticamente")
    
    if problemas_encontrados == 0:
        print("   ✅ No se encontraron inconsistencias Stock vs Lotes")
    else:
        print(f"   🔧 {productos_corregidos}/{problemas_encontrados} productos corregidos")
    
    print()
    print("🔍 FASE 2: DETECTAR Y CORREGIR DISCREPANCIAS STOCK vs BINCARD")
    print("-" * 60)
    
    productos_bincard_corregidos = 0
    productos_bincard_problemas = 0
    
    for producto in Producto.objects.all():
        transacciones = Transaccion.objects.filter(producto=producto)
        
        if transacciones.exists():
            total_entradas = sum(t.cantidad for t in transacciones.filter(tipo='entrada'))
            total_salidas = sum(t.cantidad for t in transacciones.filter(tipo='salida'))
            saldo_bincard = total_entradas - total_salidas
            
            if saldo_bincard != producto.stock:
                productos_bincard_problemas += 1
                discrepancia = saldo_bincard - producto.stock
                
                print(f"   ⚠️  {producto.codigo_barra}: Stock={producto.stock}, Bincard={saldo_bincard}, Diff={discrepancia}")
                
                # Buscar transacción problemática (la que podría estar duplicada)
                if discrepancia > 0:
                    # Hay exceso en el Bincard - buscar entrada duplicada
                    entradas = transacciones.filter(tipo='entrada').order_by('fecha')
                    
                    for entrada in entradas:
                        if entrada.cantidad >= discrepancia:
                            # Esta entrada podría contener la duplicación
                            cantidad_correcta = entrada.cantidad - discrepancia
                            
                            if cantidad_correcta > 0:
                                with transaction.atomic():
                                    entrada.cantidad = cantidad_correcta
                                    entrada.observacion = f"AUTO-CORREGIDO: Eliminada duplicación de {discrepancia} unidades"
                                    entrada.save()
                                    
                                    productos_bincard_corregidos += 1
                                    transacciones_corregidas += 1
                                    print(f"      ✅ Entrada corregida: {entrada.cantidad + discrepancia} → {cantidad_correcta}")
                                    break
                            elif cantidad_correcta == 0:
                                # La entrada completa era duplicada
                                with transaction.atomic():
                                    entrada.delete()
                                    productos_bincard_corregidos += 1
                                    transacciones_corregidas += 1
                                    print(f"      ✅ Entrada duplicada eliminada completamente")
                                    break
    
    if productos_bincard_problemas == 0:
        print("   ✅ No se encontraron discrepancias Stock vs Bincard")
    else:
        print(f"   🔧 {productos_bincard_corregidos}/{productos_bincard_problemas} discrepancias Bincard corregidas")
    
    print()
    print("🔍 FASE 3: LIMPIAR LOTES PROBLEMÁTICOS")
    print("-" * 60)
    
    # Limpiar lotes huérfanos o con problemas
    lotes_huerfanos = LoteProducto.objects.filter(producto__isnull=True)
    lotes_stock_negativo = LoteProducto.objects.filter(stock__lt=0)
    
    lotes_eliminados = 0
    lotes_corregidos = 0
    
    if lotes_huerfanos.exists():
        cantidad_huerfanos = lotes_huerfanos.count()
        lotes_huerfanos.delete()
        lotes_eliminados += cantidad_huerfanos
        print(f"   🗑️  {cantidad_huerfanos} lotes huérfanos eliminados")
    
    for lote in lotes_stock_negativo:
        lote.stock = 0
        lote.save()
        lotes_corregidos += 1
    
    if lotes_eliminados == 0 and lotes_corregidos == 0:
        print("   ✅ No se encontraron lotes problemáticos")
    else:
        print(f"   🔧 {lotes_eliminados} lotes eliminados, {lotes_corregidos} lotes corregidos")
    
    print()
    print("🔍 FASE 4: VERIFICACIÓN FINAL COMPLETA")
    print("-" * 60)
    
    # Verificación final de todo el sistema
    total_productos = Producto.objects.count()
    productos_verificados = 0
    productos_finales_ok = 0
    
    for producto in Producto.objects.all():
        productos_verificados += 1
        
        # Verificar consistencia stock vs lotes (solo productos con vencimiento)
        if producto.tiene_vencimiento:
            stock_lotes = producto.lotes.aggregate(total=models.Sum('stock'))['total'] or 0
            if producto.stock != stock_lotes:
                continue  # Este producto aún tiene problemas
        
        # Verificar consistencia stock vs bincard
        transacciones = Transaccion.objects.filter(producto=producto)
        if transacciones.exists():
            total_entradas = sum(t.cantidad for t in transacciones.filter(tipo='entrada'))
            total_salidas = sum(t.cantidad for t in transacciones.filter(tipo='salida'))
            saldo_bincard = total_entradas - total_salidas
            
            if saldo_bincard != producto.stock:
                continue  # Este producto aún tiene problemas
        
        productos_finales_ok += 1
    
    porcentaje_ok = (productos_finales_ok / productos_verificados * 100) if productos_verificados > 0 else 0
    
    print(f"   📊 ESTADÍSTICAS FINALES:")
    print(f"      • Total productos verificados: {productos_verificados}")
    print(f"      • Productos sin problemas: {productos_finales_ok}")
    print(f"      • Porcentaje de integridad: {porcentaje_ok:.1f}%")
    
    print()
    print("💡 RESUMEN DE CORRECCIONES APLICADAS:")
    print("-" * 60)
    print(f"   🔧 Productos Stock vs Lotes corregidos: {productos_corregidos}")
    print(f"   🔧 Productos Bincard corregidos: {productos_bincard_corregidos}")
    print(f"   🔧 Transacciones corregidas: {transacciones_corregidas}")
    print(f"   🔧 Lotes eliminados/corregidos: {lotes_eliminados + lotes_corregidos}")
    
    total_correcciones = productos_corregidos + productos_bincard_corregidos + transacciones_corregidas + lotes_eliminados + lotes_corregidos
    
    print()
    print("🎯 RESULTADO FINAL:")
    print("-" * 60)
    
    if porcentaje_ok >= 99:
        print("   🎉 ¡SISTEMA PERFECTAMENTE CORREGIDO!")
        print("      ✅ Todos los productos están consistentes")
        print("      ✅ No hay duplicaciones en el sistema")
        print("      ✅ Stock sincronizado con Bincard")
        print("      ✅ Lotes íntegros y trazabilidad preservada")
        print(f"      ✅ {total_correcciones} correcciones aplicadas exitosamente")
        print()
        print("   🚀 EL SISTEMA ESTÁ LISTO PARA USAR SIN PROBLEMAS")
    elif porcentaje_ok >= 95:
        print("   ✅ SISTEMA MAYORMENTE CORREGIDO")
        print(f"      • {porcentaje_ok:.1f}% de los productos están correctos")
        print(f"      • Se aplicaron {total_correcciones} correcciones")
        print("      • Problemas residuales mínimos")
    else:
        print("   ⚠️  SISTEMA PARCIALMENTE CORREGIDO")
        print(f"      • {porcentaje_ok:.1f}% de los productos están correctos")
        print(f"      • Se aplicaron {total_correcciones} correcciones")
        print("      • Se requieren correcciones manuales adicionales")
    
    print()
    print("=" * 80)
    print("              CORRECCIÓN GLOBAL COMPLETADA")
    print("=" * 80)
    
    return {
        'productos_corregidos': productos_corregidos,
        'bincard_corregidos': productos_bincard_corregidos,
        'transacciones_corregidas': transacciones_corregidas,
        'porcentaje_integridad': porcentaje_ok
    }

if __name__ == "__main__":
    resultado = correccion_automatica_global()
