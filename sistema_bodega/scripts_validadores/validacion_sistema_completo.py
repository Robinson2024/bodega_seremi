#!/usr/bin/env python
"""
VALIDACIÓN COMPLETA DEL SISTEMA
Verifica que la solución de duplicaciones se aplique a TODOS los productos
No solo al 100047, sino a todo el sistema de bodega
"""

import os
import sys
import django
from datetime import date, timedelta

# Configurar Django
sys.path.append('c:\\Users\\Robinson Bravo\\Desktop\\bodega_seremi\\sistema_bodega')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
django.setup()

from accounts.models import Producto, LoteProducto, Transaccion
from django.db import models

def validacion_sistema_completo():
    print("=" * 80)
    print("        VALIDACIÓN COMPLETA DEL SISTEMA DE BODEGA")
    print("    VERIFICANDO QUE LA SOLUCIÓN APLIQUE A TODOS LOS PRODUCTOS")
    print("=" * 80)
    print()
    
    # 1. ESTADÍSTICAS GENERALES
    total_productos = Producto.objects.count()
    productos_con_vencimiento = Producto.objects.filter(tiene_vencimiento=True).count()
    productos_sin_vencimiento = Producto.objects.filter(tiene_vencimiento=False).count()
    total_lotes = LoteProducto.objects.count()
    total_transacciones = Transaccion.objects.count()
    
    print("📊 ESTADÍSTICAS GENERALES DEL SISTEMA:")
    print(f"   • Total productos: {total_productos}")
    print(f"   • Con vencimiento: {productos_con_vencimiento}")
    print(f"   • Sin vencimiento: {productos_sin_vencimiento}")
    print(f"   • Total lotes: {total_lotes}")
    print(f"   • Total transacciones: {total_transacciones}")
    print()
    
    # 2. VERIFICAR CONSISTENCIA STOCK vs LOTES EN TODO EL SISTEMA
    print("🔍 VERIFICANDO CONSISTENCIA STOCK vs LOTES (TODOS LOS PRODUCTOS):")
    productos_inconsistentes = []
    productos_verificados = 0
    
    for producto in Producto.objects.filter(tiene_vencimiento=True):
        productos_verificados += 1
        stock_lotes = producto.lotes.aggregate(total=models.Sum('stock'))['total'] or 0
        if producto.stock != stock_lotes:
            productos_inconsistentes.append({
                'codigo': producto.codigo_barra,
                'descripcion': producto.descripcion,
                'stock_producto': producto.stock,
                'stock_lotes': stock_lotes,
                'diferencia': producto.stock - stock_lotes
            })
    
    print(f"   • Productos verificados: {productos_verificados}")
    if productos_inconsistentes:
        print(f"   ❌ PRODUCTOS CON INCONSISTENCIAS: {len(productos_inconsistentes)}")
        for item in productos_inconsistentes:
            print(f"      • {item['codigo']}: {item['descripcion'][:30]}...")
            print(f"        Stock={item['stock_producto']}, Lotes={item['stock_lotes']}, Diff={item['diferencia']}")
    else:
        print(f"   ✅ PERFECTO: Todos los {productos_verificados} productos están consistentes")
    print()
    
    # 3. VERIFICAR DISCREPANCIAS STOCK vs BINCARD EN TODO EL SISTEMA
    print("📋 VERIFICANDO CONSISTENCIA STOCK vs BINCARD (TODOS LOS PRODUCTOS):")
    productos_con_discrepancia_bincard = []
    productos_con_transacciones = 0
    
    for producto in Producto.objects.all():
        transacciones = Transaccion.objects.filter(producto=producto)
        if transacciones.exists():
            productos_con_transacciones += 1
            
            total_entradas = sum(t.cantidad for t in transacciones.filter(tipo='entrada'))
            total_salidas = sum(t.cantidad for t in transacciones.filter(tipo='salida'))
            saldo_bincard = total_entradas - total_salidas
            
            if saldo_bincard != producto.stock:
                productos_con_discrepancia_bincard.append({
                    'codigo': producto.codigo_barra,
                    'descripcion': producto.descripcion,
                    'stock_real': producto.stock,
                    'saldo_bincard': saldo_bincard,
                    'diferencia': saldo_bincard - producto.stock,
                    'entradas': total_entradas,
                    'salidas': total_salidas
                })
    
    print(f"   • Productos con transacciones: {productos_con_transacciones}")
    if productos_con_discrepancia_bincard:
        print(f"   ❌ PRODUCTOS CON DISCREPANCIA BINCARD: {len(productos_con_discrepancia_bincard)}")
        for item in productos_con_discrepancia_bincard:
            print(f"      • {item['codigo']}: {item['descripcion'][:30]}...")
            print(f"        Stock={item['stock_real']}, Bincard={item['saldo_bincard']}, Diff={item['diferencia']}")
            print(f"        Entradas={item['entradas']}, Salidas={item['salidas']}")
    else:
        print(f"   ✅ PERFECTO: Todos los {productos_con_transacciones} productos tienen Bincard consistente")
    print()
    
    # 4. DETECTAR POSIBLES DUPLICACIONES RECIENTES
    print("🔍 DETECTANDO POSIBLES DUPLICACIONES RECIENTES:")
    hoy = date.today()
    ayer = hoy - timedelta(days=1)
    
    # Buscar transacciones de entrada de hoy que podrían ser duplicadas
    entradas_hoy = Transaccion.objects.filter(
        tipo='entrada',
        fecha__date=hoy
    ).order_by('producto', 'fecha')
    
    productos_con_multiples_entradas = {}
    for entrada in entradas_hoy:
        codigo = entrada.producto.codigo_barra
        if codigo not in productos_con_multiples_entradas:
            productos_con_multiples_entradas[codigo] = []
        productos_con_multiples_entradas[codigo].append(entrada)
    
    posibles_duplicaciones = []
    for codigo, entradas in productos_con_multiples_entradas.items():
        if len(entradas) > 1:
            # Verificar si hay entradas sospechosas (misma cantidad o una el doble de otra)
            for i, entrada1 in enumerate(entradas):
                for entrada2 in entradas[i+1:]:
                    if (entrada1.cantidad == entrada2.cantidad * 2 or 
                        entrada2.cantidad == entrada1.cantidad * 2 or
                        entrada1.cantidad == entrada2.cantidad):
                        posibles_duplicaciones.append({
                            'producto': entrada1.producto,
                            'entrada1': entrada1,
                            'entrada2': entrada2
                        })
    
    if posibles_duplicaciones:
        print(f"   ⚠️  POSIBLES DUPLICACIONES DETECTADAS: {len(posibles_duplicaciones)}")
        for dup in posibles_duplicaciones:
            p = dup['producto']
            e1 = dup['entrada1']
            e2 = dup['entrada2']
            print(f"      • {p.codigo_barra}: {p.descripcion[:30]}...")
            print(f"        {e1.fecha.strftime('%H:%M')}: {e1.cantidad} unidades")
            print(f"        {e2.fecha.strftime('%H:%M')}: {e2.cantidad} unidades")
    else:
        print(f"   ✅ No se detectaron duplicaciones en las entradas de hoy")
    print()
    
    # 5. VERIFICAR LOTES HUÉRFANOS O PROBLEMÁTICOS
    print("📦 VERIFICANDO INTEGRIDAD DE LOTES:")
    lotes_huerfanos = LoteProducto.objects.filter(producto__isnull=True).count()
    lotes_con_stock_negativo = LoteProducto.objects.filter(stock__lt=0).count()
    lotes_sin_fecha = LoteProducto.objects.filter(fecha_vencimiento__isnull=True).count()
    
    total_lotes_verificados = LoteProducto.objects.count()
    
    print(f"   • Total lotes verificados: {total_lotes_verificados}")
    print(f"   • Lotes huérfanos: {lotes_huerfanos}")
    print(f"   • Lotes con stock negativo: {lotes_con_stock_negativo}")
    print(f"   • Lotes sin fecha vencimiento: {lotes_sin_fecha}")
    
    if lotes_huerfanos == 0 and lotes_con_stock_negativo == 0:
        print(f"   ✅ Todos los lotes están correctos")
    else:
        print(f"   ⚠️  Se detectaron lotes problemáticos")
    print()
    
    # 6. RESUMEN FINAL Y RECOMENDACIONES
    print("💡 RESUMEN FINAL:")
    
    total_problemas = (len(productos_inconsistentes) + 
                      len(productos_con_discrepancia_bincard) + 
                      len(posibles_duplicaciones) +
                      lotes_huerfanos + 
                      lotes_con_stock_negativo)
    
    if total_problemas == 0:
        print("   🎉 ¡EXCELENTE! SISTEMA COMPLETAMENTE SANO:")
        print("      ✅ Todos los productos tienen stock consistente")
        print("      ✅ Todos los Bincards están sincronizados")
        print("      ✅ No hay duplicaciones detectadas")
        print("      ✅ Todos los lotes están correctos")
        print("      ✅ LA SOLUCIÓN SE APLICA A TODO EL SISTEMA")
    else:
        print(f"   ⚠️  SE DETECTARON {total_problemas} PROBLEMAS:")
        
        if productos_inconsistentes:
            print(f"      🔧 {len(productos_inconsistentes)} productos con inconsistencia Stock vs Lotes")
        
        if productos_con_discrepancia_bincard:
            print(f"      🔧 {len(productos_con_discrepancia_bincard)} productos con discrepancia en Bincard")
        
        if posibles_duplicaciones:
            print(f"      🔧 {len(posibles_duplicaciones)} posibles duplicaciones recientes")
        
        if lotes_huerfanos or lotes_con_stock_negativo:
            print(f"      🔧 {lotes_huerfanos + lotes_con_stock_negativo} lotes problemáticos")
        
        print("\n   📋 RECOMENDACIONES:")
        print("      → Ejecutar script de corrección automática")
        print("      → Revisar productos con discrepancias específicas")
        print("      → Verificar duplicaciones recientes manualmente")
    
    print()
    print("=" * 80)
    print("                    VALIDACIÓN COMPLETA TERMINADA")
    print("=" * 80)
    
    return {
        'total_productos': total_productos,
        'productos_inconsistentes': len(productos_inconsistentes),
        'productos_discrepancia_bincard': len(productos_con_discrepancia_bincard),
        'posibles_duplicaciones': len(posibles_duplicaciones),
        'total_problemas': total_problemas
    }

if __name__ == "__main__":
    resultado = validacion_sistema_completo()
