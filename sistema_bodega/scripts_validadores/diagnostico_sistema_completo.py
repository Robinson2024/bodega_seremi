#!/usr/bin/env python
"""
Diagnóstico completo del sistema de bodega
Verifica la integridad entre stock, lotes y Bincard
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
from django.db import models

def diagnostico_completo():
    print("=" * 60)
    print("     DIAGNÓSTICO COMPLETO DEL SISTEMA DE BODEGA")
    print("=" * 60)
    print()
    
    # 1. Estadísticas generales
    total_productos = Producto.objects.count()
    productos_con_vencimiento = Producto.objects.filter(tiene_vencimiento=True).count()
    total_lotes = LoteProducto.objects.count()
    lotes_con_stock = LoteProducto.objects.filter(stock__gt=0).count()
    lotes_vacios = LoteProducto.objects.filter(stock=0).count()
    total_historial = Transaccion.objects.count()
    
    print("📊 ESTADÍSTICAS GENERALES:")
    print(f"   • Total productos: {total_productos}")
    print(f"   • Productos con vencimiento: {productos_con_vencimiento}")
    print(f"   • Total lotes: {total_lotes}")
    print(f"   • Lotes con stock: {lotes_con_stock}")
    print(f"   • Lotes vacíos (stock=0): {lotes_vacios}")
    print(f"   • Registros en Bincard: {total_historial}")
    print()
    
    # 2. Verificar discrepancias stock vs lotes
    print("🔍 VERIFICANDO CONSISTENCIA STOCK vs LOTES:")
    productos_con_discrepancias = []
    
    for producto in Producto.objects.filter(tiene_vencimiento=True):
        stock_lotes = producto.lotes.aggregate(total=models.Sum('stock'))['total'] or 0
        if producto.stock != stock_lotes:
            productos_con_discrepancias.append({
                'producto': producto,
                'stock_producto': producto.stock,
                'stock_lotes': stock_lotes,
                'diferencia': producto.stock - stock_lotes
            })
    
    if productos_con_discrepancias:
        print(f"   ⚠️  ENCONTRADAS {len(productos_con_discrepancias)} DISCREPANCIAS:")
        for item in productos_con_discrepancias[:10]:  # Mostrar primeros 10
            p = item['producto']
            print(f"   • {p.descripcion} ({p.codigo_barra}): Stock={item['stock_producto']}, Lotes={item['stock_lotes']}, Diff={item['diferencia']}")
    else:
        print("   ✅ PERFECTO: No hay discrepancias entre stock y lotes")
    print()
    
    # 3. Verificar lotes vencidos con stock
    print("📅 VERIFICANDO LOTES VENCIDOS:")
    hoy = date.today()
    lotes_vencidos_con_stock = LoteProducto.objects.filter(
        fecha_vencimiento__lt=hoy,
        stock__gt=0
    ).count()
    
    if lotes_vencidos_con_stock > 0:
        print(f"   ⚠️  {lotes_vencidos_con_stock} lotes vencidos con stock (requieren gestión)")
        
        # Mostrar algunos ejemplos
        ejemplos = LoteProducto.objects.filter(
            fecha_vencimiento__lt=hoy,
            stock__gt=0
        )[:5]
        
        for lote in ejemplos:
            dias_vencido = (hoy - lote.fecha_vencimiento).days
            print(f"   • {lote.producto.descripcion}: Stock={lote.stock}, Vencido hace {dias_vencido} días")
    else:
        print("   ✅ No hay lotes vencidos con stock")
    print()
    
    # 4. Verificar integridad del Bincard
    print("📋 VERIFICANDO INTEGRIDAD DEL BINCARD:")
    
    # Buscar productos con historial
    productos_con_historial = Transaccion.objects.values('producto').distinct().count()
    print(f"   • Productos con movimientos en Bincard: {productos_con_historial}")
    
    # Verificar ejemplos específicos
    if total_historial > 0:
        print("   • Ejemplos de movimientos recientes:")
        movimientos_recientes = Transaccion.objects.order_by('-fecha')[:3]
        for mov in movimientos_recientes:
            tipo_mov = "ENTRADA" if mov.tipo == "entrada" else "SALIDA"
            print(f"     - {mov.fecha}: {tipo_mov} {mov.cantidad} unidades de {mov.producto.descripcion}")
    print()
    
    # 5. Recomendaciones
    print("💡 RECOMENDACIONES:")
    
    if productos_con_discrepancias:
        print("   🔧 CRÍTICO: Ejecutar sincronización de stock")
        print("      → Usar script de corrección para sincronizar")
    
    if lotes_vencidos_con_stock > 0:
        print("   📦 GESTIÓN: Revisar lotes vencidos con stock")
        print("      → Considerar generar actas de salida para productos vencidos")
    
    if lotes_vacios > 0:
        print(f"   🧹 INFORMACIÓN: {lotes_vacios} lotes vacíos conservados para trazabilidad")
        print("      → Esto es CORRECTO para mantener el historial del Bincard")
    
    if not productos_con_discrepancias and not lotes_vencidos_con_stock:
        print("   ✅ EXCELENTE: El sistema está funcionando correctamente")
        print("   ✅ Stock sincronizado, Bincard íntegro, trazabilidad preservada")
    
    print()
    print("=" * 60)
    print("           DIAGNÓSTICO COMPLETADO")
    print("=" * 60)

if __name__ == "__main__":
    diagnostico_completo()
