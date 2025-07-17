#!/usr/bin/env python
"""
TEST DE STRESS FINAL - Reproduce condiciones extremas similares al error reportado
"""
import os
import sys
import django
import json
from datetime import date, timedelta
import random
import time

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
django.setup()

from accounts.models import Producto, LoteProducto, Transaccion
from django.db import transaction
from django.core.serializers.json import DjangoJSONEncoder

def test_stress_extremo():
    """Test de stress con condiciones extremas."""
    print("🔥 TEST DE STRESS EXTREMO")
    print("=" * 50)
    
    errores_encontrados = []
    
    try:
        with transaction.atomic():
            # Limpiar producto existente si existe
            Producto.objects.filter(codigo_barra='STRESS001').delete()
            
            # Crear producto similar a "tomates"
            producto = Producto.objects.create(
                codigo_barra='STRESS001',  # Código único para test
                descripcion='Tomates Stress Test',
                tiene_vencimiento=True,
                fecha_vencimiento=date.today() + timedelta(days=90),
                stock=0
            )
            
            print(f"📦 Creando producto: {producto.descripcion}")
            
            # ESCENARIO 1: Crear MUCHOS lotes (50+)
            print(f"🏭 Creando 50 lotes con diferentes características...")
            
            stock_total = 0
            lotes_creados = []
            
            for i in range(50):
                # Variedad de cantidades
                cantidad = random.randint(10, 200)
                
                # Variedad de fechas (algunos vencidos, otros no)
                dias_vencimiento = random.randint(-30, 365)  # Incluye fechas pasadas
                fecha_venc = date.today() + timedelta(days=dias_vencimiento)
                
                lote = LoteProducto.objects.create(
                    producto=producto,
                    numero_lote=i+1,
                    fecha_vencimiento=fecha_venc,
                    stock=cantidad
                )
                
                lotes_creados.append(lote)
                stock_total += cantidad
                
                # Probar serialización después de cada lote
                try:
                    datos_temp = {
                        'lote': {
                            'numero_lote': lote.numero_lote,
                            'fecha_vencimiento': lote.fecha_vencimiento,
                            'stock': lote.stock,
                            'dias_restantes': lote.get_dias_para_vencer(),
                            'estado': lote.get_estado_vencimiento(),
                            'esta_vencido': lote.esta_vencido()
                        }
                    }
                    json.dumps(datos_temp, cls=DjangoJSONEncoder)
                    
                except Exception as e:
                    errores_encontrados.append(f"Error serialización lote {i+1}: {e}")
            
            producto.stock = stock_total
            producto.save()
            
            print(f"✅ Stock total: {stock_total} en {len(lotes_creados)} lotes")
            
            # ESCENARIO 2: Probar métodos con muchos lotes
            print(f"🧪 Probando métodos con {len(lotes_creados)} lotes...")
            
            try:
                # Probar cada método que puede fallar
                metodos_test = [
                    ('get_lotes_detalle', producto.get_lotes_detalle),
                    ('get_lotes_activos_detalle', producto.get_lotes_activos_detalle),
                    ('get_estadisticas_lotes', producto.get_estadisticas_lotes),
                    ('get_total_lotes_activos', producto.get_total_lotes_activos),
                    ('get_estado_vencimiento_completo', producto.get_estado_vencimiento_completo),
                    ('get_proximo_vencimiento', producto.get_proximo_vencimiento)
                ]
                
                for metodo_nombre, metodo_func in metodos_test:
                    try:
                        resultado = metodo_func()
                        
                        # Intentar serializar resultado
                        json.dumps(resultado, cls=DjangoJSONEncoder)
                        
                        print(f"  ✅ {metodo_nombre}: OK")
                        
                    except Exception as e:
                        error_msg = f"Error en {metodo_nombre}: {e}"
                        errores_encontrados.append(error_msg)
                        print(f"  ❌ {error_msg}")
                        
            except Exception as e:
                errores_encontrados.append(f"Error general en métodos: {e}")
            
            # ESCENARIO 3: Salidas masivas hasta agotar stock
            print(f"📤 Realizando salidas masivas...")
            
            salidas_realizadas = 0
            
            while producto.stock > 0:
                # Salidas de tamaño variable
                cantidad_salida = random.randint(1, min(500, producto.stock))
                
                # Aplicar FIFO
                if not producto.reducir_stock_fifo(cantidad_salida):
                    errores_encontrados.append(f"Error FIFO en salida {salidas_realizadas}")
                    break
                
                producto.refresh_from_db()
                salidas_realizadas += 1
                
                # Probar serialización después de cada salida
                try:
                    datos_salida = {
                        'producto': {
                            'codigo_barra': producto.codigo_barra,
                            'descripcion': producto.descripcion,
                            'stock': producto.stock,
                            'lotes_activos': producto.get_total_lotes_activos(),
                            'lotes_detalle': producto.get_lotes_detalle(),
                            'lotes_activos_detalle': producto.get_lotes_activos_detalle(),
                            'estadisticas': producto.get_estadisticas_lotes()
                        },
                        'salida': {
                            'numero': salidas_realizadas,
                            'cantidad': cantidad_salida,
                            'stock_restante': producto.stock
                        }
                    }
                    
                    json.dumps(datos_salida, cls=DjangoJSONEncoder)
                    
                except Exception as e:
                    error_msg = f"Error serialización salida {salidas_realizadas}: {e}"
                    errores_encontrados.append(error_msg)
                    print(f"    ❌ {error_msg}")
                    
                    # Analizar qué campo específico causa el error
                    try:
                        # Probar cada campo del producto
                        for campo, valor in datos_salida['producto'].items():
                            try:
                                json.dumps(valor, cls=DjangoJSONEncoder)
                            except Exception as e2:
                                error_msg2 = f"Campo problemático '{campo}': {e2}"
                                errores_encontrados.append(error_msg2)
                                print(f"      🔍 {error_msg2}")
                    except:
                        pass
                    
                    break
                
                # Cada 10 salidas, mostrar progreso
                if salidas_realizadas % 10 == 0:
                    print(f"    Salida #{salidas_realizadas}: {producto.stock} unidades restantes")
                
                # Protección contra bucles infinitos
                if salidas_realizadas > 200:
                    break
            
            print(f"📊 Salidas realizadas: {salidas_realizadas}")
            print(f"📊 Stock final: {producto.stock}")
            
            # ESCENARIO 4: Validación final con stock agotado
            print(f"🎯 Validación final con stock agotado...")
            
            try:
                # Probar todos los métodos con stock agotado
                validaciones_finales = {
                    'stock': producto.stock,
                    'lotes_activos': producto.get_total_lotes_activos(),
                    'total_lotes': producto.lotes.count(),
                    'lotes_detalle': producto.get_lotes_detalle(),
                    'lotes_activos_detalle': producto.get_lotes_activos_detalle(),
                    'estadisticas': producto.get_estadisticas_lotes(),
                    'estado_vencimiento': producto.get_estado_vencimiento_completo()
                }
                
                # Serializar datos finales
                json.dumps(validaciones_finales, cls=DjangoJSONEncoder)
                
                print(f"✅ Validación final exitosa")
                
                # Verificar que lotes activos sea 0
                if producto.get_total_lotes_activos() != 0:
                    errores_encontrados.append("Lotes activos no es 0 después de agotar stock")
                
                # Verificar que lotes históricos se preserven
                if producto.lotes.count() == 0:
                    errores_encontrados.append("Lotes históricos fueron eliminados")
                
            except Exception as e:
                error_msg = f"Error validación final: {e}"
                errores_encontrados.append(error_msg)
                print(f"❌ {error_msg}")
            
            # Limpiar
            producto.delete()
            
    except Exception as e:
        errores_encontrados.append(f"Error general en test: {e}")
        print(f"💥 ERROR GENERAL: {e}")
        import traceback
        traceback.print_exc()
    
    # Mostrar resumen
    print(f"\n📊 RESUMEN DEL TEST DE STRESS")
    print(f"=" * 50)
    print(f"🔥 Errores encontrados: {len(errores_encontrados)}")
    
    if errores_encontrados:
        print(f"\n❌ ERRORES DETALLADOS:")
        for i, error in enumerate(errores_encontrados, 1):
            print(f"   {i}. {error}")
        
        print(f"\n🚨 SISTEMA REQUIERE CORRECCIÓN")
        return False
    else:
        print(f"\n✅ SISTEMA PASÓ EL TEST DE STRESS")
        print(f"   No se encontraron errores bajo condiciones extremas")
        return True

def main():
    """Ejecuta el test de stress final."""
    print("🔥 TEST DE STRESS FINAL - CONDICIONES EXTREMAS")
    print("=" * 70)
    
    inicio = time.time()
    resultado = test_stress_extremo()
    fin = time.time()
    
    print(f"\n⏱️  Tiempo de ejecución: {fin - inicio:.2f} segundos")
    
    if resultado:
        print(f"\n🎉 CONCLUSIÓN: El sistema está estable y maneja correctamente:")
        print(f"   ✅ Múltiples lotes (50+)")
        print(f"   ✅ Salidas masivas hasta agotar stock")
        print(f"   ✅ Serialización JSON en todos los estados")
        print(f"   ✅ Preservación de lotes históricos")
        print(f"   ✅ Métodos de lotes activos vs históricos")
        print(f"\n💡 Es posible que el error se haya solucionado con las mejoras anteriores")
    else:
        print(f"\n⚠️  CONCLUSIÓN: Se encontraron errores que requieren corrección")
    
    print("=" * 70)

if __name__ == "__main__":
    main()
