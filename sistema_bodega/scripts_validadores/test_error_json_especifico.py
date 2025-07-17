#!/usr/bin/env python
"""
Test específico para reproducir el error JSON en salida de productos.
Simula el escenario exacto: múltiples lotes, salidas graduales, operaciones de vista/AJAX.
"""
import os
import sys
import django
import json
from datetime import date, timedelta
import random

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
django.setup()

from accounts.models import Producto, LoteProducto, Transaccion
from django.db import transaction
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

def test_error_json_salida():
    """Test específico para reproducir el error JSON en salida de productos."""
    print("🚀 TEST ESPECÍFICO: Error JSON en Salida de Productos")
    print("=" * 60)
    
    try:
        with transaction.atomic():
            # 1. CREAR PRODUCTO CON MUCHOS LOTES (como tomate)
            print("\n1️⃣ CREANDO PRODUCTO CON MÚLTIPLES LOTES...")
            
            producto = Producto.objects.create(
                codigo_barra='TESTJSON001',
                descripcion='Tomates Test JSON',
                tiene_vencimiento=True,
                fecha_vencimiento=date.today() + timedelta(days=90),
                stock=0
            )
            
            # Crear 50 lotes con diferentes cantidades y vencimientos
            stock_total = 0
            for i in range(50):
                cantidad = random.randint(20, 150)
                dias_venc = random.randint(10, 200)
                
                lote = LoteProducto.objects.create(
                    producto=producto,
                    numero_lote=i+1,
                    fecha_vencimiento=date.today() + timedelta(days=dias_venc),
                    stock=cantidad
                )
                stock_total += cantidad
            
            producto.stock = stock_total
            producto.save()
            
            print(f"✅ Producto creado: {producto.codigo_barra}")
            print(f"📊 Stock total: {stock_total}")
            print(f"📋 Lotes creados: {producto.lotes.count()}")
            
            # 2. SIMULAR MÚLTIPLES SALIDAS COMO EN EL SISTEMA REAL
            print(f"\n2️⃣ SIMULANDO SALIDAS GRADUALES...")
            
            salidas_realizadas = 0
            
            while producto.stock > 0:
                # Cantidad de salida aleatoria
                cantidad_salida = random.randint(1, min(200, producto.stock))
                
                print(f"   Salida #{salidas_realizadas + 1}: {cantidad_salida} unidades (Stock restante: {producto.stock})")
                
                # Aplicar FIFO
                if not producto.reducir_stock_fifo(cantidad_salida):
                    print(f"❌ Error en FIFO - salida #{salidas_realizadas + 1}")
                    break
                
                # Refrescar producto
                producto.refresh_from_db()
                
                # 3. SIMULAR OPERACIONES DE VISTA/AJAX DESPUÉS DE CADA SALIDA
                try:
                    # Simular datos que se envían en respuesta AJAX
                    datos_ajax = {
                        'codigo_barra': producto.codigo_barra,
                        'descripcion': producto.descripcion,
                        'stock': producto.stock,
                        'tiene_vencimiento': producto.tiene_vencimiento,
                        'lotes_activos': producto.get_total_lotes_activos(),
                        'lotes_detalle': producto.get_lotes_detalle(),
                        'lotes_activos_detalle': producto.get_lotes_activos_detalle(),
                        'estadisticas': producto.get_estadisticas_lotes()
                    }
                    
                    # Intentar serializar a JSON (aquí puede fallar)
                    json_string = json.dumps(datos_ajax, cls=DjangoJSONEncoder)
                    
                    # Simular operación de sesión
                    productos_salida = [datos_ajax]
                    session_json = json.dumps(productos_salida, cls=DjangoJSONEncoder)
                    
                except Exception as e:
                    print(f"❌ ERROR JSON en salida #{salidas_realizadas + 1}: {e}")
                    print(f"   Stock actual: {producto.stock}")
                    print(f"   Lotes activos: {producto.get_total_lotes_activos()}")
                    print(f"   Total lotes: {producto.lotes.count()}")
                    
                    # Mostrar detalles del error
                    try:
                        lotes_detalle = producto.get_lotes_detalle()
                        print(f"   Lotes detalle: {len(lotes_detalle)}")
                        for lote in lotes_detalle[:5]:  # Mostrar primeros 5
                            print(f"     - Lote {lote['numero_lote']}: {lote['stock']} unidades")
                    except Exception as e2:
                        print(f"   Error adicional: {e2}")
                    
                    raise e
                
                salidas_realizadas += 1
                
                # Protección
                if salidas_realizadas > 500:
                    print("⚠️  Demasiadas salidas, interrumpiendo...")
                    break
            
            print(f"\n3️⃣ VALIDACIÓN FINAL...")
            print(f"✅ Salidas realizadas: {salidas_realizadas}")
            print(f"📊 Stock final: {producto.stock}")
            print(f"📋 Lotes activos finales: {producto.get_total_lotes_activos()}")
            print(f"📋 Total lotes (historial): {producto.lotes.count()}")
            
            # 4. PRUEBA FINAL DE SERIALIZACIÓN
            try:
                datos_finales = {
                    'producto': {
                        'codigo_barra': producto.codigo_barra,
                        'descripcion': producto.descripcion,
                        'stock': producto.stock,
                        'lotes_activos': producto.get_total_lotes_activos(),
                        'lotes_detalle': producto.get_lotes_detalle(),
                        'estadisticas': producto.get_estadisticas_lotes()
                    }
                }
                
                json_final = json.dumps(datos_finales, cls=DjangoJSONEncoder)
                print(f"✅ Serialización final exitosa")
                
            except Exception as e:
                print(f"❌ Error en serialización final: {e}")
                raise e
            
            # Limpiar
            producto.delete()
            print(f"\n🧹 Producto test eliminado")
            
    except Exception as e:
        print(f"\n💥 ERROR DETECTADO: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print(f"\n✅ TEST COMPLETADO SIN ERRORES")
    return True

def test_error_especifico_campos():
    """Test específico para detectar errores en campos específicos."""
    print("\n🔍 TEST ESPECÍFICO: Validación de Campos")
    print("=" * 50)
    
    try:
        with transaction.atomic():
            # Crear producto
            producto = Producto.objects.create(
                codigo_barra='TESTCAMPOS001',
                descripcion='Test Campos Específicos',
                tiene_vencimiento=True,
                fecha_vencimiento=date.today() + timedelta(days=60),
                stock=0
            )
            
            # Crear lotes
            for i in range(20):
                LoteProducto.objects.create(
                    producto=producto,
                    numero_lote=i+1,
                    fecha_vencimiento=date.today() + timedelta(days=i*5),
                    stock=50
                )
            
            producto.stock = 20 * 50  # 1000 unidades
            producto.save()
            
            # Agotar stock completamente
            producto.reducir_stock_fifo(1000)
            producto.refresh_from_db()
            
            # Validar cada método individualmente
            print("📋 Validando métodos individuales...")
            
            try:
                detalle = producto.get_lotes_detalle()
                print(f"✅ get_lotes_detalle(): {len(detalle)} lotes")
                
                # Verificar cada campo
                for lote in detalle:
                    for campo, valor in lote.items():
                        try:
                            json.dumps(valor, cls=DjangoJSONEncoder)
                        except Exception as e:
                            print(f"❌ Campo '{campo}' no serializable: {valor} - {e}")
                            
            except Exception as e:
                print(f"❌ Error en get_lotes_detalle(): {e}")
            
            try:
                activos = producto.get_lotes_activos_detalle()
                print(f"✅ get_lotes_activos_detalle(): {len(activos)} lotes")
                
                # Verificar serialización
                json.dumps(activos, cls=DjangoJSONEncoder)
                
            except Exception as e:
                print(f"❌ Error en get_lotes_activos_detalle(): {e}")
            
            try:
                stats = producto.get_estadisticas_lotes()
                print(f"✅ get_estadisticas_lotes(): {stats}")
                
                # Verificar serialización
                json.dumps(stats, cls=DjangoJSONEncoder)
                
            except Exception as e:
                print(f"❌ Error en get_estadisticas_lotes(): {e}")
            
            # Limpiar
            producto.delete()
            
    except Exception as e:
        print(f"❌ Error en test de campos: {e}")
        return False
    
    return True

def main():
    """Ejecuta todos los tests específicos."""
    print("🧪 TESTS ESPECÍFICOS PARA DETECTAR ERROR JSON")
    print("=" * 70)
    
    # Test 1: Simulación completa del error
    test1_ok = test_error_json_salida()
    
    # Test 2: Validación de campos específicos
    test2_ok = test_error_especifico_campos()
    
    # Resumen
    print("\n" + "=" * 70)
    print("📊 RESUMEN DE TESTS ESPECÍFICOS")
    print("=" * 70)
    print(f"Test 1 (Simulación completa): {'✅ PASÓ' if test1_ok else '❌ FALLÓ'}")
    print(f"Test 2 (Validación campos): {'✅ PASÓ' if test2_ok else '❌ FALLÓ'}")
    
    if test1_ok and test2_ok:
        print("\n✅ TODOS LOS TESTS PASARON")
        print("   No se detectó el error JSON. El sistema está estable.")
    else:
        print("\n❌ ALGUNOS TESTS FALLARON")
        print("   Se detectaron errores que requieren corrección.")
    
    print("=" * 70)

if __name__ == "__main__":
    main()
