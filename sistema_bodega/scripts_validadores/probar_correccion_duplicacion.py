#!/usr/bin/env python
"""
Prueba específica de corrección de duplicación en productos existentes
Simula el proceso completo de agregar stock usando el formulario corregido
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
from accounts.forms import AgregarStockConVencimientoForm
from django.db import models

def probar_correccion_duplicacion():
    print("=" * 70)
    print("   PRUEBA DE CORRECCIÓN - AGREGAR STOCK SIN DUPLICACIÓN")
    print("=" * 70)
    print()
    
    # Verificar si ya existe el producto 100047
    try:
        producto = Producto.objects.get(codigo_barra='100047')
        print(f"📦 USANDO PRODUCTO EXISTENTE:")
        print(f"   • Código: {producto.codigo_barra}")
        print(f"   • Descripción: {producto.descripcion}")
        print(f"   • Stock antes: {producto.stock}")
        
        stock_antes = producto.stock
        total_lotes_antes = producto.lotes.aggregate(total=models.Sum('stock'))['total'] or 0
        print(f"   • Stock en lotes antes: {total_lotes_antes}")
        
    except Producto.DoesNotExist:
        print("❌ Producto 100047 no encontrado. Creando producto para prueba...")
        producto = Producto.objects.create(
            descripcion='Producto Prueba Stock',
            stock=0,
            tiene_vencimiento=True,
            fecha_vencimiento=date.today() + timedelta(days=30)
        )
        stock_antes = 0
        total_lotes_antes = 0
    
    print()
    
    # Simular datos del formulario (usuario quiere agregar 500 unidades)
    cantidad_a_agregar = 500
    datos_formulario = {
        'cantidad': cantidad_a_agregar,
        'tiene_vencimiento_nuevo': True,
        'fecha_vencimiento': date.today() + timedelta(days=45),
        'rut_proveedor': '12345678-9',
        'guia_despacho': 'GD-001',
        'numero_factura': 'F-001',
        'orden_compra': 'OC-001'
    }
    
    print(f"🧪 SIMULANDO AGREGAR STOCK:")
    print(f"   • Cantidad a agregar: {cantidad_a_agregar}")
    print(f"   • Fecha vencimiento: {datos_formulario['fecha_vencimiento']}")
    print()
    
    # Contar transacciones antes
    transacciones_antes = Transaccion.objects.filter(producto=producto).count()
    
    # Procesar formulario
    form = AgregarStockConVencimientoForm(data=datos_formulario, producto=producto)
    
    if form.is_valid():
        print("✅ Formulario válido. Agregando stock...")
        
        # Ejecutar el método que agrega stock
        lote, transaccion = form.agregar_stock_a_producto(producto)
        
        # Verificar resultados
        producto.refresh_from_db()
        stock_despues = producto.stock
        total_lotes_despues = producto.lotes.aggregate(total=models.Sum('stock'))['total'] or 0
        transacciones_despues = Transaccion.objects.filter(producto=producto).count()
        
        print(f"\n📊 RESULTADOS:")
        print(f"   • Stock antes: {stock_antes}")
        print(f"   • Stock después: {stock_despues}")
        print(f"   • Incremento real: {stock_despues - stock_antes}")
        print(f"   • Incremento esperado: {cantidad_a_agregar}")
        print()
        print(f"   • Lotes antes: {total_lotes_antes}")
        print(f"   • Lotes después: {total_lotes_despues}")
        print(f"   • Incremento lotes: {total_lotes_despues - total_lotes_antes}")
        print()
        print(f"   • Transacciones antes: {transacciones_antes}")
        print(f"   • Transacciones después: {transacciones_despues}")
        
        # Verificar transacción creada
        if transaccion:
            print(f"   • Transacción registrada: {transaccion.cantidad} unidades")
        
        # Análisis final
        print(f"\n🎯 ANÁLISIS:")
        
        incremento_correcto = (stock_despues - stock_antes) == cantidad_a_agregar
        lotes_consistentes = stock_despues == total_lotes_despues
        transaccion_correcta = transaccion and transaccion.cantidad == cantidad_a_agregar
        
        if incremento_correcto and lotes_consistentes and transaccion_correcta:
            print("   ✅ ¡PERFECTO! Corrección exitosa:")
            print("      • Stock se incrementó exactamente por la cantidad ingresada")
            print("      • Stock producto = Stock lotes")
            print("      • Transacción registra la cantidad correcta")
            print("      • NO HAY DUPLICACIÓN")
        else:
            print("   ❌ Aún hay problemas:")
            if not incremento_correcto:
                print(f"      • Stock duplicado: esperado +{cantidad_a_agregar}, obtenido +{stock_despues - stock_antes}")
            if not lotes_consistentes:
                print(f"      • Inconsistencia: Stock={stock_despues}, Lotes={total_lotes_despues}")
            if not transaccion_correcta:
                cantidad_trans = transaccion.cantidad if transaccion else 0
                print(f"      • Transacción incorrecta: esperado {cantidad_a_agregar}, registrado {cantidad_trans}")
        
        # Mostrar lotes actuales
        print(f"\n📋 LOTES ACTUALES:")
        lotes = producto.lotes.all().order_by('numero_lote')
        for lote in lotes:
            print(f"   • Lote {lote.numero_lote}: {lote.stock} unidades, vence {lote.fecha_vencimiento}")
            
    else:
        print("❌ Error en formulario:")
        for field, errors in form.errors.items():
            print(f"   • {field}: {errors}")
    
    print()
    print("=" * 70)
    print("                    PRUEBA COMPLETADA")
    print("=" * 70)

if __name__ == "__main__":
    probar_correccion_duplicacion()
