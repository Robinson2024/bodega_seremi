#!/usr/bin/env python
"""
Test específico para simular las operaciones exactas de la vista de salida de productos.
Reproduce el flujo completo: sesión, AJAX, limpieza, etc.
"""
import os
import sys
import django
import json
from datetime import date, timedelta

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
django.setup()

from accounts.models import Producto, LoteProducto, Transaccion
from django.db import transaction
from django.core.serializers.json import DjangoJSONEncoder
from django.test import RequestFactory, Client
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.auth import get_user_model
from django.http import JsonResponse

User = get_user_model()

def test_vista_salida_completa():
    """Test que simula exactamente la vista de salida de productos."""
    print("🎯 TEST VISTA SALIDA COMPLETA")
    print("=" * 50)
    
    try:
        with transaction.atomic():
            # 1. CREAR PRODUCTO CON MÚLTIPLES LOTES
            print("\n1️⃣ Creando producto con múltiples lotes...")
            
            producto = Producto.objects.create(
                codigo_barra='TESTVISTA001',
                descripcion='Tomates Vista Test',
                tiene_vencimiento=True,
                fecha_vencimiento=date.today() + timedelta(days=90),
                stock=0
            )
            
            # Crear 30 lotes
            stock_total = 0
            for i in range(30):
                cantidad = 50 + (i * 10)  # Cantidades incrementales
                lote = LoteProducto.objects.create(
                    producto=producto,
                    numero_lote=i+1,
                    fecha_vencimiento=date.today() + timedelta(days=30 + i*5),
                    stock=cantidad
                )
                stock_total += cantidad
            
            producto.stock = stock_total
            producto.save()
            
            print(f"✅ Producto creado: {stock_total} unidades en {producto.lotes.count()} lotes")
            
            # 2. SIMULAR SESIÓN CON PRODUCTOS_SALIDA
            print("\n2️⃣ Simulando sesión de productos_salida...")
            
            # Crear cliente y configurar sesión
            client = Client()
            session = client.session
            
            # Simular productos_salida en sesión
            productos_salida = []
            
            # 3. SIMULAR MÚLTIPLES SALIDAS HASTA AGOTAR STOCK
            print("\n3️⃣ Simulando salidas hasta agotar stock...")
            
            salida_numero = 1
            
            while producto.stock > 0:
                cantidad_salida = min(200, producto.stock)
                
                print(f"   Salida #{salida_numero}: {cantidad_salida} unidades")
                
                # Aplicar FIFO
                if not producto.reducir_stock_fifo(cantidad_salida):
                    print(f"❌ Error en FIFO")
                    break
                
                producto.refresh_from_db()
                
                # Simular agregado a productos_salida
                item_salida = {
                    'codigo_barra': producto.codigo_barra,
                    'descripcion': producto.descripcion,
                    'stock': producto.stock,
                    'cantidad_salida': cantidad_salida,
                    'tiene_vencimiento': producto.tiene_vencimiento,
                    'lotes_activos': producto.get_total_lotes_activos(),
                    'lotes_detalle': producto.get_lotes_detalle(),
                    'estadisticas': producto.get_estadisticas_lotes()
                }
                
                productos_salida.append(item_salida)
                
                # Simular serialización de sesión (aquí puede fallar)
                try:
                    session_json = json.dumps(productos_salida, cls=DjangoJSONEncoder)
                    session['productos_salida'] = productos_salida
                    session.save()
                except Exception as e:
                    print(f"❌ ERROR SESIÓN en salida #{salida_numero}: {e}")
                    print(f"   Stock actual: {producto.stock}")
                    print(f"   Lotes activos: {producto.get_total_lotes_activos()}")
                    
                    # Analizar el item problemático
                    try:
                        json.dumps(item_salida, cls=DjangoJSONEncoder)
                    except Exception as e2:
                        print(f"   Error en item_salida: {e2}")
                        
                        # Verificar cada campo
                        for campo, valor in item_salida.items():
                            try:
                                json.dumps(valor, cls=DjangoJSONEncoder)
                            except Exception as e3:
                                print(f"     Campo problemático '{campo}': {e3}")
                    
                    raise e
                
                # Simular respuesta AJAX
                try:
                    response_data = {
                        'status': 'success',
                        'productos_salida': productos_salida,
                        'total_productos': len(productos_salida),
                        'producto_actual': item_salida
                    }
                    
                    ajax_json = json.dumps(response_data, cls=DjangoJSONEncoder)
                    
                except Exception as e:
                    print(f"❌ ERROR AJAX en salida #{salida_numero}: {e}")
                    raise e
                
                salida_numero += 1
                
                if salida_numero > 100:  # Protección
                    break
            
            # 4. SIMULAR LIMPIEZA FINAL DE SESIÓN
            print(f"\n4️⃣ Simulando limpieza final de sesión...")
            
            try:
                # Verificar estado final del producto
                producto.refresh_from_db()
                
                final_data = {
                    'producto': {
                        'codigo_barra': producto.codigo_barra,
                        'descripcion': producto.descripcion,
                        'stock': producto.stock,
                        'lotes_activos': producto.get_total_lotes_activos(),
                        'total_lotes': producto.lotes.count(),
                        'lotes_detalle': producto.get_lotes_detalle(),
                        'estadisticas': producto.get_estadisticas_lotes()
                    },
                    'productos_salida': productos_salida
                }
                
                # Simular limpieza de sesión
                final_json = json.dumps(final_data, cls=DjangoJSONEncoder)
                
                # Limpiar sesión
                session.pop('productos_salida', None)
                session.save()
                
                print(f"✅ Limpieza de sesión exitosa")
                
            except Exception as e:
                print(f"❌ ERROR LIMPIEZA: {e}")
                raise e
            
            # 5. VERIFICACIONES FINALES
            print(f"\n5️⃣ Verificaciones finales...")
            
            print(f"📊 Salidas realizadas: {salida_numero - 1}")
            print(f"📊 Stock final: {producto.stock}")
            print(f"📊 Lotes activos: {producto.get_total_lotes_activos()}")
            print(f"📊 Total lotes: {producto.lotes.count()}")
            print(f"📊 Items en productos_salida: {len(productos_salida)}")
            
            # Verificar cada item de productos_salida
            for i, item in enumerate(productos_salida):
                try:
                    json.dumps(item, cls=DjangoJSONEncoder)
                except Exception as e:
                    print(f"❌ Item {i} no serializable: {e}")
                    raise e
            
            # Limpiar
            producto.delete()
            print(f"\n🧹 Producto test eliminado")
            
    except Exception as e:
        print(f"\n💥 ERROR DETECTADO EN VISTA: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print(f"\n✅ TEST VISTA COMPLETADO SIN ERRORES")
    return True

def test_condiciones_especificas():
    """Test para condiciones específicas que pueden causar el error."""
    print("\n🔍 TEST CONDICIONES ESPECÍFICAS")
    print("=" * 50)
    
    try:
        with transaction.atomic():
            # Crear producto con condiciones específicas
            producto = Producto.objects.create(
                codigo_barra='TESTCOND001',
                descripcion='Test Condiciones Específicas',
                tiene_vencimiento=True,
                fecha_vencimiento=date.today() + timedelta(days=60),
                stock=0
            )
            
            # Crear lotes con fechas problemáticas
            print("📅 Creando lotes con fechas específicas...")
            
            # Lote vencido
            LoteProducto.objects.create(
                producto=producto,
                numero_lote=1,
                fecha_vencimiento=date.today() - timedelta(days=5),
                stock=100
            )
            
            # Lote que vence hoy
            LoteProducto.objects.create(
                producto=producto,
                numero_lote=2,
                fecha_vencimiento=date.today(),
                stock=50
            )
            
            # Lote crítico (vence en 3 días)
            LoteProducto.objects.create(
                producto=producto,
                numero_lote=3,
                fecha_vencimiento=date.today() + timedelta(days=3),
                stock=75
            )
            
            producto.stock = 225
            producto.save()
            
            print(f"✅ Producto creado con lotes problemáticos")
            
            # Probar serialización en diferentes estados
            print("🧪 Probando serialización en diferentes estados...")
            
            estados = [
                ("Estado inicial", producto.stock),
                ("Después de salida parcial", 150),
                ("Después de más salidas", 50),
                ("Stock agotado", 0)
            ]
            
            for estado_desc, stock_objetivo in estados:
                if producto.stock > stock_objetivo:
                    cantidad_reducir = producto.stock - stock_objetivo
                    producto.reducir_stock_fifo(cantidad_reducir)
                    producto.refresh_from_db()
                
                print(f"  {estado_desc} (stock: {producto.stock})...")
                
                try:
                    # Datos típicos de vista
                    datos_vista = {
                        'producto': {
                            'codigo_barra': producto.codigo_barra,
                            'descripcion': producto.descripcion,
                            'stock': producto.stock,
                            'tiene_vencimiento': producto.tiene_vencimiento,
                            'fecha_vencimiento': producto.fecha_vencimiento.isoformat() if producto.fecha_vencimiento else None,
                            'lotes_activos': producto.get_total_lotes_activos(),
                            'lotes_detalle': producto.get_lotes_detalle(),
                            'lotes_activos_detalle': producto.get_lotes_activos_detalle(),
                            'estadisticas': producto.get_estadisticas_lotes(),
                            'estado_vencimiento': producto.get_estado_vencimiento_completo(),
                            'proximo_vencimiento': producto.get_proximo_vencimiento().isoformat() if producto.get_proximo_vencimiento() else None
                        }
                    }
                    
                    # Serializar
                    json_string = json.dumps(datos_vista, cls=DjangoJSONEncoder)
                    
                    print(f"    ✅ Serialización OK")
                    
                except Exception as e:
                    print(f"    ❌ Error serialización: {e}")
                    
                    # Probar cada campo individualmente
                    for campo, valor in datos_vista['producto'].items():
                        try:
                            json.dumps(valor, cls=DjangoJSONEncoder)
                        except Exception as e2:
                            print(f"      Campo problemático '{campo}': {e2}")
                    
                    raise e
            
            # Limpiar
            producto.delete()
            
    except Exception as e:
        print(f"❌ Error en test de condiciones: {e}")
        return False
    
    return True

def main():
    """Ejecuta todos los tests de vista."""
    print("🎯 TESTS ESPECÍFICOS DE VISTA DE SALIDA")
    print("=" * 60)
    
    # Test 1: Vista completa
    test1_ok = test_vista_salida_completa()
    
    # Test 2: Condiciones específicas
    test2_ok = test_condiciones_especificas()
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE TESTS DE VISTA")
    print("=" * 60)
    print(f"Test 1 (Vista completa): {'✅ PASÓ' if test1_ok else '❌ FALLÓ'}")
    print(f"Test 2 (Condiciones específicas): {'✅ PASÓ' if test2_ok else '❌ FALLÓ'}")
    
    if test1_ok and test2_ok:
        print("\n✅ TODOS LOS TESTS DE VISTA PASARON")
        print("   No se detectó el error de vista. El sistema está estable.")
    else:
        print("\n❌ ALGUNOS TESTS DE VISTA FALLARON")
        print("   Se detectaron errores en las vistas que requieren corrección.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
