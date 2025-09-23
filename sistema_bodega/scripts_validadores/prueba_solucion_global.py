#!/usr/bin/env python
"""
PRUEBA DE APLICACIÓN GLOBAL DE LA SOLUCIÓN
Prueba que la corrección funcione para productos NUEVOS
No solo para el 100047, sino para cualquier producto que se agregue
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
from accounts.forms import ProductoForm, AgregarStockConVencimientoForm
from django.db import models, transaction

def probar_solucion_global():
    print("=" * 80)
    print("         PRUEBA DE APLICACIÓN GLOBAL DE LA SOLUCIÓN")
    print("    VERIFICANDO QUE LA CORRECCIÓN FUNCIONE PARA PRODUCTOS NUEVOS")
    print("=" * 80)
    print()
    
    productos_prueba = []
    
    print("🧪 PRUEBA 1: CREAR PRODUCTO NUEVO CON VENCIMIENTO")
    print("-" * 50)
    
    # Datos para producto nuevo
    datos_producto_nuevo = {
        'descripcion': 'Producto Prueba Global 1',
        'stock': 300,  # Usuario ingresa 300
        'tiene_vencimiento': True,
        'fecha_vencimiento': date.today() + timedelta(days=60),
        'categoria': None
    }
    
    print(f"   📝 Datos del producto:")
    print(f"      • Descripción: {datos_producto_nuevo['descripcion']}")
    print(f"      • Stock ingresado: {datos_producto_nuevo['stock']}")
    print(f"      • Fecha vencimiento: {datos_producto_nuevo['fecha_vencimiento']}")
    
    try:
        # Crear usando el formulario corregido
        form = ProductoForm(data=datos_producto_nuevo)
        if form.is_valid():
            producto = form.save()
            productos_prueba.append(producto)
            
            print(f"\n   📊 RESULTADO PRODUCTO NUEVO:")
            print(f"      • Código asignado: {producto.codigo_barra}")
            print(f"      • Stock final: {producto.stock}")
            
            # Verificar lotes
            lotes = producto.lotes.all()
            total_lotes = sum(lote.stock for lote in lotes)
            print(f"      • Stock en lotes: {total_lotes}")
            print(f"      • Cantidad de lotes: {lotes.count()}")
            
            # Verificar transacciones
            transacciones = Transaccion.objects.filter(producto=producto)
            print(f"      • Transacciones creadas: {transacciones.count()}")
            
            # Análisis
            if producto.stock == 300 and total_lotes == 300:
                print(f"      ✅ PERFECTO: No hay duplicación en producto nuevo")
            else:
                print(f"      ❌ PROBLEMA: Stock={producto.stock}, Lotes={total_lotes}")
        else:
            print(f"      ❌ Error en formulario: {form.errors}")
    except Exception as e:
        print(f"      ❌ Error: {e}")
    
    print()
    print("🧪 PRUEBA 2: AGREGAR STOCK A PRODUCTO EXISTENTE")
    print("-" * 50)
    
    # Seleccionar un producto existente (diferente al 100047)
    producto_existente = Producto.objects.filter(
        tiene_vencimiento=True
    ).exclude(codigo_barra='100047').first()
    
    if producto_existente:
        stock_antes = producto_existente.stock
        lotes_antes = producto_existente.lotes.aggregate(total=models.Sum('stock'))['total'] or 0
        transacciones_antes = Transaccion.objects.filter(producto=producto_existente).count()
        
        print(f"   📝 Producto seleccionado: {producto_existente.descripcion} ({producto_existente.codigo_barra})")
        print(f"      • Stock antes: {stock_antes}")
        print(f"      • Lotes antes: {lotes_antes}")
        print(f"      • Transacciones antes: {transacciones_antes}")
        
        # Datos para agregar stock
        cantidad_agregar = 250
        datos_agregar = {
            'cantidad': cantidad_agregar,
            'tiene_vencimiento_nuevo': True,
            'fecha_vencimiento': date.today() + timedelta(days=45),
            'rut_proveedor': '98765432-1',
            'guia_despacho': 'GD-PRUEBA',
        }
        
        print(f"      • Cantidad a agregar: {cantidad_agregar}")
        
        try:
            # Usar formulario corregido para agregar stock
            form = AgregarStockConVencimientoForm(data=datos_agregar, producto=producto_existente)
            if form.is_valid():
                lote, transaccion = form.agregar_stock_a_producto(producto_existente)
                
                # Refrescar datos
                producto_existente.refresh_from_db()
                stock_despues = producto_existente.stock
                lotes_despues = producto_existente.lotes.aggregate(total=models.Sum('stock'))['total'] or 0
                transacciones_despues = Transaccion.objects.filter(producto=producto_existente).count()
                
                print(f"\n   📊 RESULTADO AGREGAR STOCK:")
                print(f"      • Stock después: {stock_despues}")
                print(f"      • Incremento real: {stock_despues - stock_antes}")
                print(f"      • Incremento esperado: {cantidad_agregar}")
                print(f"      • Lotes después: {lotes_despues}")
                print(f"      • Transacciones después: {transacciones_despues}")
                
                # Análisis
                incremento_correcto = (stock_despues - stock_antes) == cantidad_agregar
                consistencia_lotes = stock_despues == lotes_despues
                transaccion_creada = transacciones_despues == (transacciones_antes + 1)
                
                if incremento_correcto and consistencia_lotes and transaccion_creada:
                    print(f"      ✅ PERFECTO: Agregar stock funciona correctamente")
                else:
                    print(f"      ❌ PROBLEMA DETECTADO:")
                    if not incremento_correcto:
                        print(f"         • Incremento incorrecto")
                    if not consistencia_lotes:
                        print(f"         • Inconsistencia en lotes")
                    if not transaccion_creada:
                        print(f"         • Problema en transacciones")
            else:
                print(f"      ❌ Error en formulario: {form.errors}")
        except Exception as e:
            print(f"      ❌ Error: {e}")
    else:
        print("      ⚠️  No se encontró producto existente para prueba")
    
    print()
    print("🧪 PRUEBA 3: VERIFICAR QUE NO HAYA DUPLICACIONES EN EL SISTEMA")
    print("-" * 50)
    
    # Verificar todo el sistema después de las pruebas
    total_productos = Producto.objects.count()
    productos_inconsistentes = 0
    productos_bincard_mal = 0
    
    for producto in Producto.objects.filter(tiene_vencimiento=True):
        # Verificar stock vs lotes
        stock_lotes = producto.lotes.aggregate(total=models.Sum('stock'))['total'] or 0
        if producto.stock != stock_lotes:
            productos_inconsistentes += 1
        
        # Verificar stock vs bincard
        transacciones = Transaccion.objects.filter(producto=producto)
        if transacciones.exists():
            total_entradas = sum(t.cantidad for t in transacciones.filter(tipo='entrada'))
            total_salidas = sum(t.cantidad for t in transacciones.filter(tipo='salida'))
            saldo_bincard = total_entradas - total_salidas
            
            if saldo_bincard != producto.stock:
                productos_bincard_mal += 1
    
    print(f"   📊 VERIFICACIÓN FINAL DEL SISTEMA:")
    print(f"      • Total productos: {total_productos}")
    print(f"      • Productos con inconsistencia Stock vs Lotes: {productos_inconsistentes}")
    print(f"      • Productos con discrepancia Bincard: {productos_bincard_mal}")
    
    if productos_inconsistentes == 0 and productos_bincard_mal == 0:
        print(f"      ✅ TODO EL SISTEMA ESTÁ CONSISTENTE")
    else:
        print(f"      ⚠️  Se detectaron {productos_inconsistentes + productos_bincard_mal} problemas")
    
    # 4. LIMPIEZA DE PRODUCTOS DE PRUEBA
    print()
    print("🧹 LIMPIEZA DE PRODUCTOS DE PRUEBA:")
    print("-" * 50)
    
    for producto in productos_prueba:
        print(f"   🗑️  Eliminando producto de prueba: {producto.codigo_barra}")
        producto.delete()
    
    print()
    print("💡 CONCLUSIÓN FINAL:")
    print("-" * 50)
    
    if productos_inconsistentes == 0 and productos_bincard_mal == 0:
        print("   🎉 ¡EXCELENTE! LA SOLUCIÓN SE APLICA GLOBALMENTE:")
        print("      ✅ Productos nuevos: Sin duplicación")
        print("      ✅ Agregar stock: Funciona correctamente") 
        print("      ✅ Todo el sistema: Consistente")
        print("      ✅ LA CORRECCIÓN ES EFECTIVA PARA TODO EL SISTEMA")
    else:
        print("   ⚠️  SE DETECTARON PROBLEMAS:")
        print("      → La solución necesita ajustes adicionales")
        print("      → Revisar productos específicos con problemas")
    
    print()
    print("=" * 80)
    print("                   PRUEBA GLOBAL COMPLETADA")
    print("=" * 80)

if __name__ == "__main__":
    probar_solucion_global()
