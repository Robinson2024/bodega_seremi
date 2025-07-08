#!/usr/bin/env python
"""
Corrección específica del Bincard del producto 100047
Corrige la transacción duplicada para que coincida con el stock real
"""

import os
import sys
import django
from datetime import datetime

# Configurar Django
sys.path.append('c:\\Users\\Robinson Bravo\\Desktop\\bodega_seremi\\sistema_bodega')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
django.setup()

from accounts.models import Producto, LoteProducto, Transaccion
from django.db import models, transaction

def corregir_bincard_100047():
    print("=" * 70)
    print("   CORRECCIÓN DEL BINCARD - PRODUCTO 100047")
    print("=" * 70)
    print()
    
    try:
        producto = Producto.objects.get(codigo_barra='100047')
        print(f"📦 PRODUCTO: {producto.descripcion}")
        print(f"   • Stock actual: {producto.stock}")
        
        # Analizar situación actual
        lotes = producto.lotes.all().order_by('numero_lote')
        total_stock_lotes = sum(lote.stock for lote in lotes)
        
        print(f"\n📋 ESTADO ACTUAL:")
        print(f"   • Stock en producto: {producto.stock}")
        print(f"   • Stock en lotes: {total_stock_lotes}")
        print(f"   • Lotes actuales:")
        for lote in lotes:
            print(f"     - Lote {lote.numero_lote}: {lote.stock} unidades")
        
        # Analizar transacciones
        transacciones = Transaccion.objects.filter(producto=producto).order_by('fecha')
        total_entradas_bincard = sum(t.cantidad for t in transacciones if t.tipo == 'entrada')
        
        print(f"\n📊 TRANSACCIONES ACTUALES:")
        print(f"   • Total transacciones: {transacciones.count()}")
        print(f"   • Total entradas en Bincard: {total_entradas_bincard}")
        print()
        
        for i, trans in enumerate(transacciones, 1):
            tipo_icon = "📥" if trans.tipo == "entrada" else "📤"
            print(f"   {i}. {tipo_icon} {trans.fecha.strftime('%Y-%m-%d %H:%M')}: {trans.cantidad} unidades")
        
        # Verificar discrepancia
        discrepancia = total_entradas_bincard - producto.stock
        
        print(f"\n🔍 ANÁLISIS DE DISCREPANCIA:")
        print(f"   • Stock real: {producto.stock}")
        print(f"   • Total Bincard: {total_entradas_bincard}")
        print(f"   • Discrepancia: {discrepancia}")
        
        if discrepancia > 0:
            print(f"\n🔧 APLICANDO CORRECCIÓN:")
            print(f"   • Se detecta entrada duplicada de {discrepancia} unidades")
            
            # Buscar la transacción problemática (la primera entrada con 1000)
            primera_entrada = transacciones.filter(tipo='entrada').first()
            
            if primera_entrada and primera_entrada.cantidad == 1000:
                print(f"   • Transacción problemática: {primera_entrada.fecha} - {primera_entrada.cantidad} unidades")
                
                # Calcular la cantidad correcta
                cantidad_correcta = primera_entrada.cantidad - discrepancia
                
                print(f"   • Cantidad actual: {primera_entrada.cantidad}")
                print(f"   • Cantidad correcta: {cantidad_correcta}")
                
                # Aplicar corrección
                confirmar = input(f"\n¿Confirmar corrección de {primera_entrada.cantidad} → {cantidad_correcta}? (s/n): ")
                
                if confirmar.lower() == 's':
                    with transaction.atomic():
                        primera_entrada.cantidad = cantidad_correcta
                        primera_entrada.observacion = f"Corregido: era {primera_entrada.cantidad + discrepancia}, ajustado a {cantidad_correcta}"
                        primera_entrada.save()
                        
                        print(f"   ✅ Transacción corregida exitosamente")
                        
                        # Verificar resultado
                        transacciones_actualizadas = Transaccion.objects.filter(producto=producto)
                        nuevo_total = sum(t.cantidad for t in transacciones_actualizadas if t.tipo == 'entrada')
                        
                        print(f"\n📊 RESULTADO:")
                        print(f"   • Nuevo total Bincard: {nuevo_total}")
                        print(f"   • Stock real: {producto.stock}")
                        
                        if nuevo_total == producto.stock:
                            print(f"   ✅ ¡PERFECTO! Bincard sincronizado con stock real")
                        else:
                            print(f"   ⚠️  Aún hay discrepancia: {nuevo_total - producto.stock}")
                else:
                    print("   ❌ Corrección cancelada")
            else:
                print("   ⚠️  No se encontró la transacción problemática esperada")
        else:
            print("   ✅ No hay discrepancias - Bincard está correcto")
        
    except Producto.DoesNotExist:
        print("❌ Producto 100047 no encontrado")
    
    print()
    print("=" * 70)
    print("              CORRECCIÓN COMPLETADA")
    print("=" * 70)

if __name__ == "__main__":
    corregir_bincard_100047()
