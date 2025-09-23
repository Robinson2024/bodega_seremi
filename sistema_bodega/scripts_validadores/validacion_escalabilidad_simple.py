#!/usr/bin/env python
"""
VALIDACIÓN DE ESCALABILIDAD SIMPLIFICADA - SISTEMA BODEGA SEREMI
Evalúa rendimiento y capacidad sin dependencias externas

Autor: Sistema Bodega SEREMI  
Fecha: 22 de julio de 2025
"""

import os
import sys
import django
import json
import time
import threading
from datetime import datetime, timedelta, date
from concurrent.futures import ThreadPoolExecutor
import random

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
django.setup()

from django.db import transaction, connection
from django.db.models import Count, Sum, Avg, Max, Min
from accounts.models import Producto, Transaccion, LoteProducto, Categoria

class ValidadorEscalabilidadSimple:
    def __init__(self):
        self.metricas = {}
        self.resultados = []
        self.errores = []
        self.datos_prueba_creados = []
        
    def log_resultado(self, mensaje, tiempo=None, nivel="INFO"):
        """Registra un resultado"""
        resultado = {
            'mensaje': mensaje,
            'tiempo': tiempo,
            'nivel': nivel,
            'timestamp': datetime.now().isoformat()
        }
        self.resultados.append(resultado)
        
        if nivel == "ERROR":
            print(f"❌ {mensaje}")
        elif nivel == "WARNING":
            print(f"⚠️  {mensaje}")
        else:
            tiempo_str = f" ({tiempo:.3f}s)" if tiempo else ""
            print(f"✅ {mensaje}{tiempo_str}")
    
    def analizar_base_datos(self):
        """Analiza el estado y rendimiento de la base de datos"""
        print("\n🗄️  ANALIZANDO BASE DE DATOS")
        print("-" * 50)
        
        inicio = time.time()
        
        # Estadísticas básicas
        stats = {
            'productos': Producto.objects.count(),
            'transacciones': Transaccion.objects.count(),
            'lotes': LoteProducto.objects.count(),
            'categorias': Categoria.objects.count()
        }
        
        tiempo_stats = time.time() - inicio
        
        print(f"📊 Registros: {sum(stats.values())} total")
        for modelo, count in stats.items():
            print(f"   - {modelo.capitalize()}: {count}")
        
        self.log_resultado(f"Estadísticas básicas obtenidas", tiempo_stats)
        
        # Análisis de consultas complejas
        consultas_inicio = time.time()
        
        # 1. Productos más transaccionados
        productos_top = Producto.objects.annotate(
            num_transacciones=Count('transaccion')
        ).order_by('-num_transacciones')[:10]
        
        tiempo_productos_top = time.time() - consultas_inicio
        
        # 2. Transacciones por tipo
        transacciones_por_tipo = Transaccion.objects.values('tipo').annotate(
            total=Count('id')
        ).order_by('-total')
        
        tiempo_por_tipo = time.time() - consultas_inicio
        
        # 3. Stock total
        stock_total = Producto.objects.aggregate(
            total_stock=Sum('stock'),
            promedio_stock=Avg('stock'),
            max_stock=Max('stock'),
            min_stock=Min('stock')
        )
        
        tiempo_stock = time.time() - consultas_inicio
        
        print(f"📈 Análisis stock: Total={stock_total['total_stock']}, Promedio={stock_total['promedio_stock']:.1f}")
        print(f"📊 Transacciones por tipo: {list(transacciones_por_tipo)}")
        
        self.log_resultado(f"Consulta productos top", tiempo_productos_top)
        self.log_resultado(f"Consulta por tipo", tiempo_por_tipo)
        self.log_resultado(f"Consulta stock agregado", tiempo_stock)
        
        # Guardar métricas de BD
        self.metricas['base_datos'] = {
            'total_registros': sum(stats.values()),
            'estadisticas': stats,
            'tiempo_stats_basicas': tiempo_stats,
            'stock_total': stock_total['total_stock'],
            'tiempo_consultas_promedio': (tiempo_productos_top + tiempo_por_tipo + tiempo_stock) / 3
        }
        
        # Evaluar rendimiento
        tiempo_promedio = self.metricas['base_datos']['tiempo_consultas_promedio']
        if tiempo_promedio < 0.1:
            self.log_resultado("Rendimiento de BD excelente")
        elif tiempo_promedio < 0.5:
            self.log_resultado("Rendimiento de BD bueno")
        else:
            self.log_resultado("Rendimiento de BD lento", nivel="WARNING")
    
    def prueba_consultas_masivas(self):
        """Ejecuta múltiples consultas para medir rendimiento"""
        print("\n🔍 PRUEBA DE CONSULTAS MASIVAS")
        print("-" * 50)
        
        consultas = [
            ("Productos con stock > 0", lambda: Producto.objects.filter(stock__gt=0).count()),
            ("Transacciones últimos 30 días", lambda: Transaccion.objects.filter(
                fecha__gte=datetime.now() - timedelta(days=30)
            ).count()),
            ("Lotes próximos a vencer", lambda: LoteProducto.objects.filter(
                fecha_vencimiento__lte=date.today() + timedelta(days=30)
            ).count()),
            ("Productos más vendidos", lambda: list(Producto.objects.annotate(
                total_salidas=Count('transaccion', filter=transaction.models.Q(transaccion__tipo='salida'))
            ).order_by('-total_salidas')[:5])),
            ("Stock por categoría", lambda: list(Categoria.objects.annotate(
                total_stock=Sum('producto__stock')
            ).order_by('-total_stock')[:10]) if Categoria.objects.exists() else [])
        ]
        
        resultados_consultas = {}
        tiempo_total_consultas = 0
        
        for nombre, consulta_func in consultas:
            inicio = time.time()
            try:
                resultado = consulta_func()
                tiempo = time.time() - inicio
                tiempo_total_consultas += tiempo
                
                if isinstance(resultado, list):
                    cantidad = len(resultado)
                else:
                    cantidad = resultado
                
                print(f"   ✅ {nombre}: {cantidad} registros ({tiempo:.3f}s)")
                resultados_consultas[nombre] = {
                    'tiempo': tiempo,
                    'cantidad': cantidad,
                    'exitosa': True
                }
                
            except Exception as e:
                tiempo = time.time() - inicio
                print(f"   ❌ {nombre}: Error - {str(e)[:50]}... ({tiempo:.3f}s)")
                resultados_consultas[nombre] = {
                    'tiempo': tiempo,
                    'error': str(e),
                    'exitosa': False
                }
        
        promedio_tiempo = tiempo_total_consultas / len(consultas)
        consultas_exitosas = sum(1 for r in resultados_consultas.values() if r.get('exitosa', False))
        
        print(f"\n📊 Resumen consultas masivas:")
        print(f"   - Tiempo total: {tiempo_total_consultas:.3f}s")
        print(f"   - Tiempo promedio: {promedio_tiempo:.3f}s")
        print(f"   - Consultas exitosas: {consultas_exitosas}/{len(consultas)}")
        
        self.log_resultado(f"Consultas masivas completadas", tiempo_total_consultas)
        
        self.metricas['consultas_masivas'] = {
            'tiempo_total': tiempo_total_consultas,
            'tiempo_promedio': promedio_tiempo,
            'consultas_exitosas': consultas_exitosas,
            'total_consultas': len(consultas),
            'resultados': resultados_consultas
        }
        
        # Evaluar rendimiento
        if promedio_tiempo < 0.1:
            self.log_resultado("Rendimiento consultas masivas excelente")
        elif promedio_tiempo < 0.5:
            self.log_resultado("Rendimiento consultas masivas bueno")
        else:
            self.log_resultado("Rendimiento consultas masivas lento", nivel="WARNING")
    
    def simular_carga_secuencial(self):
        """Simula carga secuencial del sistema"""
        print("\n🔄 SIMULACIÓN DE CARGA SECUENCIAL")
        print("-" * 50)
        
        operaciones = [
            ("Buscar producto", lambda: Producto.objects.first()),
            ("Contar transacciones", lambda: Transaccion.objects.count()),
            ("Último lote", lambda: LoteProducto.objects.order_by('-id').first()),
            ("Productos con stock", lambda: Producto.objects.filter(stock__gt=0).count()),
            ("Stock total", lambda: Producto.objects.aggregate(total=Sum('stock'))['total'])
        ]
        
        num_iteraciones = 20
        print(f"🔁 Ejecutando {len(operaciones)} operaciones x {num_iteraciones} iteraciones = {len(operaciones) * num_iteraciones} total")
        
        inicio_total = time.time()
        operaciones_exitosas = 0
        errores = 0
        
        for iteracion in range(num_iteraciones):
            for nombre, operacion in operaciones:
                try:
                    inicio_op = time.time()
                    resultado = operacion()
                    tiempo_op = time.time() - inicio_op
                    operaciones_exitosas += 1
                    
                    if iteracion == 0:  # Solo mostrar primera iteración
                        print(f"   ✅ {nombre}: {tiempo_op:.4f}s")
                        
                except Exception as e:
                    errores += 1
                    if iteracion == 0:
                        print(f"   ❌ {nombre}: Error")
        
        tiempo_total = time.time() - inicio_total
        ops_por_segundo = (operaciones_exitosas + errores) / tiempo_total
        
        print(f"\n📊 Resultados carga secuencial:")
        print(f"   - Operaciones totales: {operaciones_exitosas + errores}")
        print(f"   - Exitosas: {operaciones_exitosas}")
        print(f"   - Errores: {errores}")
        print(f"   - Tiempo total: {tiempo_total:.3f}s")
        print(f"   - Velocidad: {ops_por_segundo:.1f} ops/seg")
        
        self.log_resultado(f"Carga secuencial completada", tiempo_total)
        
        self.metricas['carga_secuencial'] = {
            'operaciones_totales': operaciones_exitosas + errores,
            'exitosas': operaciones_exitosas,
            'errores': errores,
            'tiempo_total': tiempo_total,
            'ops_por_segundo': ops_por_segundo
        }
        
        if ops_por_segundo > 50:
            self.log_resultado(f"Excelente velocidad secuencial: {ops_por_segundo:.1f} ops/seg")
        elif ops_por_segundo > 20:
            self.log_resultado(f"Buena velocidad secuencial: {ops_por_segundo:.1f} ops/seg")
        else:
            self.log_resultado(f"Velocidad secuencial limitada: {ops_por_segundo:.1f} ops/seg", nivel="WARNING")
    
    def crear_datos_prueba_escalabilidad(self, cantidad=30):
        """Crea datos de prueba para evaluar escalabilidad"""
        print(f"\n🏭 CREANDO {cantidad} REGISTROS DE PRUEBA")
        print("-" * 50)
        
        inicio = time.time()
        productos_creados = []
        transacciones_creadas = []
        
        try:
            # Crear productos en lotes para mejor rendimiento
            productos_a_crear = []
            for i in range(cantidad):
                codigo = f'ESCTEST{i:04d}'
                productos_a_crear.append(Producto(
                    codigo_barra=codigo,
                    descripcion=f'Producto escalabilidad test {i}',
                    stock=random.randint(0, 100),
                    rut_proveedor='12345678-9',
                    tiene_vencimiento=random.choice([True, False])
                ))
            
            # Inserción masiva
            productos_creados = Producto.objects.bulk_create(productos_a_crear)
            
            # Crear algunas transacciones
            for i, producto in enumerate(productos_creados):
                if i % 5 == 0:  # Solo cada 5 para no sobrecargar
                    transaccion = Transaccion.objects.create(
                        producto=producto,
                        tipo='entrada',
                        cantidad=random.randint(10, 50),
                        rut_proveedor='12345678-9',
                        observacion=f'Test escalabilidad {i}'
                    )
                    transacciones_creadas.append(transaccion)
            
            tiempo_creacion = time.time() - inicio
            velocidad = len(productos_creados) / tiempo_creacion
            
            print(f"✅ Creados {len(productos_creados)} productos")
            print(f"✅ Creadas {len(transacciones_creadas)} transacciones")
            print(f"⚡ Velocidad creación: {velocidad:.1f} productos/seg")
            
            self.log_resultado(f"Creación de datos de prueba completada", tiempo_creacion)
            self.datos_prueba_creados = productos_creados + transacciones_creadas
            
            # Probar consultas después de la inserción
            self.probar_consultas_post_insercion(len(productos_creados))
            
        except Exception as e:
            self.log_resultado(f"Error en creación de datos: {e}", nivel="ERROR")
    
    def probar_consultas_post_insercion(self, productos_agregados):
        """Prueba consultas después de inserción"""
        print(f"\n🔍 CONSULTAS DESPUÉS DE AGREGAR {productos_agregados} PRODUCTOS")
        print("-" * 50)
        
        consultas_post = [
            ("Count total productos", lambda: Producto.objects.count()),
            ("Productos test", lambda: Producto.objects.filter(codigo_barra__startswith='ESCTEST').count()),
            ("Últimos 20 productos", lambda: list(Producto.objects.order_by('-id')[:20])),
            ("Productos por rango stock", lambda: Producto.objects.filter(stock__range=[10, 90]).count()),
            ("Stock total actualizado", lambda: Producto.objects.aggregate(total=Sum('stock'))['total'])
        ]
        
        for nombre, consulta in consultas_post:
            inicio = time.time()
            try:
                resultado = consulta()
                tiempo = time.time() - inicio
                
                if isinstance(resultado, list):
                    count = len(resultado)
                else:
                    count = resultado
                    
                print(f"   ✅ {nombre}: {count} ({tiempo:.3f}s)")
                
            except Exception as e:
                tiempo = time.time() - inicio
                print(f"   ❌ {nombre}: Error ({tiempo:.3f}s)")
    
    def simular_crecimiento_proyectado(self):
        """Simula crecimiento futuro"""
        print("\n📈 PROYECCIÓN DE CRECIMIENTO")
        print("-" * 50)
        
        # Estadísticas actuales
        stats_actuales = {
            'productos': Producto.objects.count(),
            'transacciones': Transaccion.objects.count(),
            'lotes': LoteProducto.objects.count()
        }
        
        print(f"📊 Estado actual:")
        for nombre, cantidad in stats_actuales.items():
            print(f"   - {nombre.capitalize()}: {cantidad:,}")
        
        # Proyecciones
        factores = [2, 5, 10, 25, 50]
        tiempo_consulta_actual = self.metricas.get('base_datos', {}).get('tiempo_consultas_promedio', 0.1)
        
        print(f"\n🔮 Proyecciones (tiempo base consulta: {tiempo_consulta_actual:.3f}s):")
        
        for factor in factores:
            productos_proj = stats_actuales['productos'] * factor
            transacciones_proj = stats_actuales['transacciones'] * factor
            
            # Estimar tiempo de consulta proyectado (muy básico)
            tiempo_estimado = tiempo_consulta_actual * (factor ** 0.5)  # Crecimiento sub-lineal
            
            print(f"   📊 Factor {factor}x:")
            print(f"      - Productos: {productos_proj:,}")
            print(f"      - Transacciones: {transacciones_proj:,}")
            print(f"      - Tiempo consulta estimado: {tiempo_estimado:.3f}s")
            
            if tiempo_estimado > 2.0:
                print(f"      ⚠️  Tiempo de respuesta alto")
            elif tiempo_estimado > 1.0:
                print(f"      🟡 Tiempo de respuesta moderado")
            else:
                print(f"      ✅ Tiempo de respuesta aceptable")
        
        self.log_resultado("Proyección de crecimiento completada")
    
    def limpiar_datos_prueba(self):
        """Limpia datos de prueba"""
        print("\n🧹 LIMPIANDO DATOS DE PRUEBA")
        print("-" * 50)
        
        try:
            # Eliminar productos de test
            productos_test = Producto.objects.filter(codigo_barra__startswith='ESCTEST')
            count_productos = productos_test.count()
            
            if count_productos > 0:
                # Eliminar transacciones asociadas primero
                Transaccion.objects.filter(producto__in=productos_test).delete()
                
                # Eliminar productos
                productos_test.delete()
                
                print(f"✅ Eliminados {count_productos} productos de prueba")
                self.log_resultado("Limpieza de datos completada")
            else:
                print("ℹ️  No hay datos de prueba que limpiar")
                
        except Exception as e:
            self.log_resultado(f"Error en limpieza: {e}", nivel="ERROR")
    
    def generar_reporte_escalabilidad(self):
        """Genera reporte final"""
        print("\n" + "="*60)
        print("📊 REPORTE FINAL DE ESCALABILIDAD")
        print("="*60)
        
        total_resultados = len(self.resultados)
        errores = [r for r in self.resultados if r['nivel'] == 'ERROR']
        warnings = [r for r in self.resultados if r['nivel'] == 'WARNING']
        exitosos = total_resultados - len(errores) - len(warnings)
        
        # Evaluar escalabilidad
        porcentaje_exito = (exitosos / total_resultados * 100) if total_resultados > 0 else 0
        
        if len(errores) > 0:
            nivel = "🔴 LIMITADA"
            mensaje = "Problemas críticos encontrados"
        elif len(warnings) > 2:
            nivel = "🟡 MODERADA"
            mensaje = "Algunas limitaciones identificadas"
        elif porcentaje_exito > 90:
            nivel = "🟢 EXCELENTE"
            mensaje = "Sistema altamente escalable"
        else:
            nivel = "🟢 BUENA"
            mensaje = "Sistema escalable"
        
        print(f"\n{nivel} - {mensaje}")
        print(f"✅ Pruebas exitosas: {exitosos}")
        print(f"⚠️  Advertencias: {len(warnings)}")
        print(f"❌ Errores: {len(errores)}")
        print(f"📊 Porcentaje éxito: {porcentaje_exito:.1f}%")
        
        # Mostrar métricas principales
        if 'base_datos' in self.metricas:
            bd = self.metricas['base_datos']
            print(f"\n🗄️  BASE DE DATOS:")
            print(f"   - Total registros: {bd['total_registros']:,}")
            print(f"   - Tiempo consultas: {bd.get('tiempo_consultas_promedio', 0):.3f}s promedio")
        
        if 'carga_secuencial' in self.metricas:
            cs = self.metricas['carga_secuencial']
            print(f"\n⚡ RENDIMIENTO:")
            print(f"   - Operaciones/segundo: {cs['ops_por_segundo']:.1f}")
            print(f"   - Éxito: {(cs['exitosas']/cs['operaciones_totales']*100):.1f}%")
        
        # Recomendaciones
        print(f"\n💡 RECOMENDACIONES:")
        if len(errores) > 0:
            print("   1. CRÍTICO: Resolver errores identificados")
        
        tiempo_consultas = self.metricas.get('base_datos', {}).get('tiempo_consultas_promedio', 0)
        if tiempo_consultas > 0.5:
            print("   2. Optimizar consultas lentas")
        
        total_registros = self.metricas.get('base_datos', {}).get('total_registros', 0)
        if total_registros > 10000:
            print("   3. Considerar archivado de datos antiguos")
        
        print("   4. Implementar índices adicionales si es necesario")
        print("   5. Monitorear rendimiento periódicamente")
        print("   6. Planificar crecimiento de hardware según proyecciones")
        
        # Guardar reporte
        reporte = {
            'timestamp': datetime.now().isoformat(),
            'nivel_escalabilidad': nivel,
            'mensaje': mensaje,
            'metricas': self.metricas,
            'resultados': self.resultados,
            'resumen': {
                'total_pruebas': total_resultados,
                'exitosas': exitosos,
                'warnings': len(warnings),
                'errores': len(errores),
                'porcentaje_exito': porcentaje_exito
            }
        }
        
        archivo_reporte = f'REPORTE_ESCALABILIDAD_SIMPLE_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        try:
            with open(archivo_reporte, 'w', encoding='utf-8') as f:
                json.dump(reporte, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"\n📁 Reporte guardado: {archivo_reporte}")
            
        except Exception as e:
            print(f"⚠️  Error guardando reporte: {e}")
        
        print("\n🚀 ANÁLISIS DE ESCALABILIDAD COMPLETADO")
        return reporte
    
    def ejecutar_analisis_completo(self):
        """Ejecuta análisis completo"""
        print("🚀 ANÁLISIS DE ESCALABILIDAD SIMPLE - SISTEMA BODEGA SEREMI")
        print("="*65)
        print(f"Fecha: {datetime.now().strftime('%d de %B de %Y, %H:%M:%S')}")
        print("="*65)
        
        try:
            self.analizar_base_datos()
            self.prueba_consultas_masivas()
            self.simular_carga_secuencial()
            self.crear_datos_prueba_escalabilidad(25)
            self.simular_crecimiento_proyectado()
            self.limpiar_datos_prueba()
            
            return self.generar_reporte_escalabilidad()
            
        except Exception as e:
            self.log_resultado(f"Error fatal: {e}", nivel="ERROR")
            return None

def main():
    """Función principal"""
    validador = ValidadorEscalabilidadSimple()
    try:
        return validador.ejecutar_analisis_completo()
    except KeyboardInterrupt:
        print("\n⏹️  Análisis interrumpido")
        validador.limpiar_datos_prueba()
    except Exception as e:
        print(f"\n💥 Error fatal: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
