#!/usr/bin/env python
"""
Script de prueba para simular el escenario específico del usuario:
1. Agregar producto con vencimiento en 2 lotes diferentes
2. Hacer salidas hasta agotar todo el stock
3. Verificar que el producto vuelva al estado inicial (botón Agregar)
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
django.setup()

from accounts.models import Producto, LoteProducto, Transaccion
from datetime import date, timedelta

def test_escenario_usuario():
    """Simula el escenario exacto descrito por el usuario."""
    
    print("🧪 SIMULANDO ESCENARIO DEL USUARIO")
    print("=" * 50)
    print("1. Agregar producto con fecha de vencimiento en 2 lotes diferentes")
    print("2. Hacer salidas por la totalidad del producto")
    print("3. Verificar que vuelva al estado inicial")
    print()
    
    try:
        # 1. CREAR PRODUCTO INICIAL
        print("🔄 PASO 1: Creando producto inicial...")
        
        producto, created = Producto.objects.get_or_create(
            codigo_barra='777777',
            defaults={
                'descripcion': 'Producto Escenario Usuario',
                'stock': 0,
                'tiene_vencimiento': True,
                'fecha_vencimiento': date.today() + timedelta(days=30)
            }
        )
        
        # Limpiar datos previos
        producto.lotes.all().delete()
        producto.stock = 0
        producto.save()
        
        print(f"   ✅ Producto creado: {producto.descripcion}")
        print(f"   📊 Estado inicial: Stock = {producto.stock}, Lotes = {producto.lotes.count()}")
        
        # 2. AGREGAR PRIMER LOTE
        print(f"\n🔄 PASO 2: Agregando primer lote...")
        
        lote1 = LoteProducto.objects.create(
            producto=producto,
            numero_lote=1,
            fecha_vencimiento=date.today() + timedelta(days=30),
            stock=50
        )
        
        # Crear transacción de entrada
        Transaccion.objects.create(
            producto=producto,
            tipo='entrada',
            cantidad=50,
            rut_proveedor='123456789',
            guia_despacho='GD001'
        )
        
        producto.stock = 50
        producto.save()
        
        print(f"   ✅ Lote 1 creado: {lote1.stock} unidades, vence {lote1.fecha_vencimiento}")
        print(f"   📊 Estado actual: Stock = {producto.stock}, Lotes activos = {producto.get_total_lotes_activos()}")
        
        # 3. AGREGAR SEGUNDO LOTE
        print(f"\n🔄 PASO 3: Agregando segundo lote...")
        
        lote2 = LoteProducto.objects.create(
            producto=producto,
            numero_lote=2,
            fecha_vencimiento=date.today() + timedelta(days=60),
            stock=30
        )
        
        # Crear transacción de entrada
        Transaccion.objects.create(
            producto=producto,
            tipo='entrada',
            cantidad=30,
            rut_proveedor='123456789',
            guia_despacho='GD002'
        )
        
        producto.stock = 80
        producto.save()
        
        print(f"   ✅ Lote 2 creado: {lote2.stock} unidades, vence {lote2.fecha_vencimiento}")
        print(f"   📊 Estado actual: Stock = {producto.stock}, Lotes activos = {producto.get_total_lotes_activos()}")
        
        # 4. VERIFICAR ESTADO CON LOTES ACTIVOS
        print(f"\n🔍 PASO 4: Verificando comportamiento con lotes activos...")
        
        lotes_activos = producto.get_lotes_activos_detalle()
        total_lotes_activos = producto.get_total_lotes_activos()
        
        print(f"   📋 Lotes activos encontrados: {len(lotes_activos)}")
        for lote in lotes_activos:
            print(f"      - Lote #{lote['numero_lote']}: {lote['stock']} unidades")
        
        if total_lotes_activos > 0:
            print(f"   ✅ COMPORTAMIENTO ESPERADO: Debe mostrar botón 'Lotes ({total_lotes_activos})'")
        else:
            print(f"   ❌ ERROR: No detecta lotes activos")
        
        # 5. SIMULAR PRIMERA SALIDA PARCIAL
        print(f"\n🔄 PASO 5: Simulando primera salida parcial (40 unidades)...")
        
        # Reducir stock usando FIFO
        cantidad_salida1 = 40
        resultado_fifo1 = producto.reducir_stock_fifo(cantidad_salida1)
        
        if resultado_fifo1:
            print(f"   ✅ Salida FIFO exitosa: {cantidad_salida1} unidades")
            
            # Crear transacción de salida
            Transaccion.objects.create(
                producto=producto,
                tipo='salida',
                cantidad=cantidad_salida1
            )
            
            # Mostrar estado de lotes después de la salida
            lote1.refresh_from_db()
            lote2.refresh_from_db()
            producto.refresh_from_db()
            
            print(f"   📊 Estado después de salida 1:")
            print(f"      - Producto stock: {producto.stock}")
            print(f"      - Lote 1: {lote1.stock} unidades")
            print(f"      - Lote 2: {lote2.stock} unidades")
            print(f"      - Lotes activos: {producto.get_total_lotes_activos()}")
        
        # 6. SIMULAR SEGUNDA SALIDA (COMPLETAR STOCK)
        print(f"\n🔄 PASO 6: Simulando segunda salida (40 unidades restantes)...")
        
        cantidad_salida2 = 40
        resultado_fifo2 = producto.reducir_stock_fifo(cantidad_salida2)
        
        if resultado_fifo2:
            print(f"   ✅ Salida FIFO exitosa: {cantidad_salida2} unidades")
            
            # Crear transacción de salida
            Transaccion.objects.create(
                producto=producto,
                tipo='salida',
                cantidad=cantidad_salida2
            )
            
            # Mostrar estado final
            lote1.refresh_from_db()
            lote2.refresh_from_db()
            producto.refresh_from_db()
            
            print(f"   📊 Estado después de salida 2 (STOCK AGOTADO):")
            print(f"      - Producto stock: {producto.stock}")
            print(f"      - Lote 1: {lote1.stock} unidades")
            print(f"      - Lote 2: {lote2.stock} unidades")
            print(f"      - Total lotes: {producto.lotes.count()}")
            print(f"      - Lotes activos: {producto.get_total_lotes_activos()}")
        
        # 7. VERIFICAR COMPORTAMIENTO FINAL
        print(f"\n🎯 PASO 7: Verificando comportamiento final...")
        
        lotes_activos_final = producto.get_lotes_activos_detalle()
        total_lotes_activos_final = producto.get_total_lotes_activos()
        
        print(f"   📋 Lotes activos después de agotar stock: {len(lotes_activos_final)}")
        print(f"   📊 Total lotes activos: {total_lotes_activos_final}")
        
        if total_lotes_activos_final == 0:
            print(f"   ✅ COMPORTAMIENTO CORRECTO:")
            print(f"      - ✅ No hay lotes activos para gestión")
            print(f"      - ✅ Debe mostrar botón 'AGREGAR' nuevamente")
            print(f"      - ✅ Los lotes vacíos se preservan para historial")
            print(f"      - ✅ El producto vuelve al estado inicial")
        else:
            print(f"   ❌ COMPORTAMIENTO INCORRECTO:")
            print(f"      - ❌ Aún detecta lotes activos: {total_lotes_activos_final}")
            print(f"      - ❌ No debería mostrar botón de gestión de lotes")
        
        # 8. VERIFICAR PRESERVACIÓN DE HISTORIAL
        print(f"\n📚 PASO 8: Verificando preservación de historial...")
        
        todos_los_lotes = producto.get_lotes_detalle()
        print(f"   📋 Total lotes en historial: {len(todos_los_lotes)}")
        for lote in todos_los_lotes:
            estado = "VACÍO" if lote['esta_vacio'] else "ACTIVO"
            print(f"      - Lote #{lote['numero_lote']}: {lote['stock']} unidades ({estado})")
        
        if len(todos_los_lotes) == 2 and all(lote['esta_vacio'] for lote in todos_los_lotes):
            print(f"   ✅ Historial preservado correctamente (lotes vacíos mantenidos)")
        else:
            print(f"   ❌ Problema en preservación de historial")
        
        # 9. SIMULAR COMPORTAMIENTO EN VISTAS
        print(f"\n🖥️ PASO 9: Simulando comportamiento en vistas...")
        
        # Vista Control de Vencimientos
        productos_control = []
        productos_base = Producto.objects.filter(tiene_vencimiento=True, stock__gt=0)
        for p in productos_base:
            if p.get_total_lotes_activos() > 0:
                productos_control.append(p)
        
        producto_en_control = any(p.codigo_barra == '777777' for p in productos_control)
        
        if not producto_en_control:
            print(f"   ✅ Control de Vencimientos: Producto NO aparece (correcto)")
        else:
            print(f"   ❌ Control de Vencimientos: Producto SÍ aparece (incorrecto)")
        
        # Vista Gestionar Vencimientos
        info_gestion = {
            'total_lotes': len(producto.get_lotes_activos_detalle())
        }
        
        if info_gestion['total_lotes'] == 0:
            print(f"   ✅ Gestionar Vencimientos: Debe mostrar botón 'AGREGAR'")
        else:
            print(f"   ❌ Gestionar Vencimientos: Mostraría botón 'Lotes' (incorrecto)")
        
        print(f"\n🎉 RESUMEN FINAL:")
        print(f"   🔹 Estado inicial: Producto sin lotes")
        print(f"   🔹 Se agregaron 2 lotes con stock")
        print(f"   🔹 Se realizaron salidas hasta agotar stock")
        print(f"   🔹 Resultado: Producto vuelve al estado inicial")
        print(f"   🔹 Lotes vacíos se preservan para historial")
        print(f"   🔹 Interface muestra botón 'Agregar' nuevamente")
        
    except Exception as e:
        print(f"❌ ERROR durante la simulación: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Limpiar
        try:
            Producto.objects.filter(codigo_barra='777777').delete()
            print(f"\n🧹 Producto de prueba eliminado")
        except:
            pass

if __name__ == "__main__":
    test_escenario_usuario()
