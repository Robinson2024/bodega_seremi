#!/usr/bin/env python
"""
Análisis específico del producto 100047 (Leche podrida) con duplicación
"""

import os
import sys
import django

# Configurar Django
sys.path.append('c:\\Users\\Robinson Bravo\\Desktop\\bodega_seremi\\sistema_bodega')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
django.setup()

from accounts.models import Producto, LoteProducto, Transaccion
from django.db import models

def analizar_producto_100047():
    print("=" * 60)
    print("   ANÁLISIS DEL PRODUCTO 100047 (Leche podrida)")
    print("=" * 60)
    print()
    
    try:
        # Obtener el producto problemático
        producto = Producto.objects.get(codigo_barra='100047')
        
        print(f"📦 PRODUCTO ENCONTRADO:")
        print(f"   • Código: {producto.codigo_barra}")
        print(f"   • Descripción: {producto.descripcion}")
        print(f"   • Stock actual: {producto.stock}")
        print(f"   • Tiene vencimiento: {producto.tiene_vencimiento}")
        print()
        
        # Analizar lotes
        lotes = producto.lotes.all()
        total_stock_lotes = lotes.aggregate(total=models.Sum('stock'))['total'] or 0
        
        print(f"📋 ANÁLISIS DE LOTES:")
        print(f"   • Cantidad de lotes: {lotes.count()}")
        print(f"   • Stock total en lotes: {total_stock_lotes}")
        print()
        
        if lotes.exists():
            print("   Detalle de lotes:")
            for lote in lotes.order_by('numero_lote'):
                print(f"     - Lote {lote.numero_lote}: {lote.stock} unidades, vence {lote.fecha_vencimiento}")
        
        # Analizar transacciones
        transacciones = Transaccion.objects.filter(producto=producto).order_by('-fecha')
        
        print(f"\n📊 HISTORIAL DE TRANSACCIONES:")
        print(f"   • Total transacciones: {transacciones.count()}")
        
        if transacciones.exists():
            print("   Últimas 3 transacciones:")
            for trans in transacciones[:3]:
                tipo_icon = "📥" if trans.tipo == "entrada" else "📤"
                print(f"     {tipo_icon} {trans.fecha.strftime('%Y-%m-%d %H:%M')}: {trans.tipo.upper()} {trans.cantidad} unidades")
        
        # Verificar discrepancia
        print(f"\n🔍 VERIFICACIÓN DE CONSISTENCIA:")
        if producto.stock == total_stock_lotes:
            print(f"   ✅ CONSISTENTE: Stock producto ({producto.stock}) = Stock lotes ({total_stock_lotes})")
        else:
            print(f"   ❌ DISCREPANCIA DETECTADA:")
            print(f"      • Stock en producto: {producto.stock}")
            print(f"      • Stock en lotes: {total_stock_lotes}")
            print(f"      • Diferencia: {producto.stock - total_stock_lotes}")
            
            print(f"\n🔧 APLICANDO CORRECCIÓN AUTOMÁTICA:")
            # Sincronizar usando el método del modelo
            if hasattr(producto, 'sincronizar_stock_con_lotes'):
                resultado = producto.sincronizar_stock_con_lotes()
                if resultado:
                    producto.refresh_from_db()
                    print(f"   ✅ Stock sincronizado: {producto.stock}")
                else:
                    print(f"   ✅ Ya estaba sincronizado")
        
        # Análisis de entrada duplicada
        entradas_hoy = transacciones.filter(tipo='entrada', fecha__date=django.utils.timezone.now().date())
        if entradas_hoy.exists():
            print(f"\n📥 ENTRADAS DE HOY:")
            total_entradas_hoy = sum(t.cantidad for t in entradas_hoy)
            print(f"   • Número de entradas: {entradas_hoy.count()}")
            print(f"   • Total ingresado hoy: {total_entradas_hoy}")
            
            for entrada in entradas_hoy:
                print(f"     - {entrada.fecha.strftime('%H:%M')}: +{entrada.cantidad} unidades")
        
    except Producto.DoesNotExist:
        print("❌ Producto 100047 no encontrado")
        
        # Buscar productos similares
        productos_leche = Producto.objects.filter(descripcion__icontains='leche')
        if productos_leche.exists():
            print("\n📦 PRODUCTOS SIMILARES ENCONTRADOS:")
            for p in productos_leche:
                print(f"   • {p.codigo_barra}: {p.descripcion} (Stock: {p.stock})")
    
    print()
    print("=" * 60)
    print("         ANÁLISIS COMPLETADO")
    print("=" * 60)

if __name__ == "__main__":
    analizar_producto_100047()
