#!/usr/bin/env python
"""
VALIDACIÓN DE ESCALABILIDAD Y RENDIMIENTO - SISTEMA BODEGA SEREMI
Evalúa límites, rendimiento y capacidad de crecimiento

Autor: Sistema Bodega SEREMI  
Fecha: 22 de julio de 2025
"""

import os
import sys
import django
import json
import time
import psutil
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

class ValidadorEscalabilidad:
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
    
    def medir_recursos_sistema(self):
        """Mide recursos del sistema"""
        print("\n🖥️  EVALUANDO RECURSOS DEL SISTEMA")
        print("-" * 50)
        
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Memoria
        memoria = psutil.virtual_memory()
        memoria_total_gb = memoria.total / (1024**3)
        memoria_disponible_gb = memoria.available / (1024**3)
        memoria_usada_percent = memoria.percent
        
        # Disco
        disco = psutil.disk_usage('.')
        disco_total_gb = disco.total / (1024**3)
        disco_libre_gb = disco.free / (1024**3)
        disco_usado_percent = (disco.used / disco.total) * 100
        
        print(f"🔧 CPU: {cpu_count} núcleos, {cpu_percent}% uso")
        print(f"🧠 RAM: {memoria_total_gb:.1f}GB total, {memoria_disponible_gb:.1f}GB libre ({memoria_usada_percent}% usado)")
        print(f"💾 Disco: {disco_total_gb:.1f}GB total, {disco_libre_gb:.1f}GB libre ({disco_usado_percent:.1f}% usado)")
        
        # Guardar métricas
        self.metricas['sistema'] = {
            'cpu_nucleos': cpu_count,
            'cpu_uso_percent': cpu_percent,
            'memoria_total_gb': memoria_total_gb,
            'memoria_disponible_gb': memoria_disponible_gb,
            'memoria_usada_percent': memoria_usada_percent,
            'disco_total_gb': disco_total_gb,
            'disco_libre_gb': disco_libre_gb,
            'disco_usado_percent': disco_usado_percent
        }
        
        # Evaluaciones
        if memoria_usada_percent > 80:
            self.log_resultado("Uso de memoria alto", nivel="WARNING")
        elif memoria_usada_percent < 50:
            self.log_resultado("Uso de memoria óptimo")
        
        if disco_usado_percent > 90:
            self.log_resultado("Poco espacio en disco", nivel="WARNING")
        elif disco_usado_percent < 70:
            self.log_resultado("Espacio en disco adecuado")
        
        if cpu_percent < 30:
            self.log_resultado("CPU con carga baja - bueno para escalabilidad")
        elif cpu_percent > 70:
            self.log_resultado("CPU con carga alta", nivel="WARNING")
    
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
        
        # 2. Transacciones por mes
        transacciones_agregadas = Transaccion.objects.extra(
            select={'mes': "strftime('%%Y-%%m', fecha)"}
        ).values('mes').annotate(total=Count('id')).order_by('mes')
        
        tiempo_agregadas = time.time() - consultas_inicio
        
        # 3. Stock total por categoría
        if Categoria.objects.exists():
            stock_por_categoria = Categoria.objects.annotate(
                total_stock=Sum('producto__stock')
            ).order_by('-total_stock')
            
            tiempo_categorias = time.time() - consultas_inicio
        else:
            tiempo_categorias = 0
        
        self.log_resultado(f"Consulta productos top", tiempo_productos_top)
        self.log_resultado(f"Consulta transacciones agregadas", tiempo_agregadas)
        if tiempo_categorias > 0:
            self.log_resultado(f"Consulta stock por categoría", tiempo_categorias)
        
        # Guardar métricas de BD
        self.metricas['base_datos'] = {
            'total_registros': sum(stats.values()),
            'estadisticas': stats,
            'tiempo_stats_basicas': tiempo_stats,
            'tiempo_consultas_complejas': tiempo_agregadas
        }
        
        # Evaluar rendimiento
        tiempo_promedio = (tiempo_stats + tiempo_agregadas + tiempo_categorias) / 3
        if tiempo_promedio < 0.1:
            self.log_resultado("Rendimiento de BD excelente")
        elif tiempo_promedio < 0.5:
            self.log_resultado("Rendimiento de BD bueno")
        else:
            self.log_resultado("Rendimiento de BD lento", nivel="WARNING")
    
    def prueba_carga_concurrente(self):
        """Simula carga concurrente en el sistema"""
        print("\n🔄 PRUEBA DE CARGA CONCURRENTE")
        print("-" * 50)
        
        def consulta_producto_random():
            """Consulta un producto aleatorio"""
            try:
                productos_ids = list(Producto.objects.values_list('id', flat=True)[:50])
                if productos_ids:
                    producto_id = random.choice(productos_ids)
                    producto = Producto.objects.get(id=producto_id)
                    # Simular algún procesamiento
                    transacciones = producto.transaccion_set.count()
                    return True
                return False
            except:
                return False
        
        def consulta_transacciones_recientes():
            """Consulta transacciones recientes"""
            try:
                transacciones = list(Transaccion.objects.order_by('-fecha')[:20])
                return len(transacciones) > 0
            except:
                return False
        
        def consulta_lotes_criticos():
            """Consulta lotes próximos a vencer"""
            try:
                fecha_limite = date.today() + timedelta(days=30)
                lotes = list(LoteProducto.objects.filter(
                    fecha_vencimiento__lte=fecha_limite
                )[:10])
                return len(lotes) >= 0
            except:
                return False
        
        # Configurar prueba concurrente
        num_hilos = min(10, psutil.cpu_count())  # Máximo 10 hilos
        num_operaciones_por_hilo = 20
        
        print(f"🧵 Ejecutando {num_hilos} hilos con {num_operaciones_por_hilo} operaciones cada uno")
        
        inicio = time.time()
        resultados_exitosos = 0
        errores_concurrencia = 0
        
        def ejecutar_operaciones():
            """Ejecuta operaciones en un hilo"""
            nonlocal resultados_exitosos, errores_concurrencia
            
            for _ in range(num_operaciones_por_hilo):
                try:
                    # Alternar entre diferentes tipos de consultas
                    operacion = random.choice([
                        consulta_producto_random,
                        consulta_transacciones_recientes,
                        consulta_lotes_criticos
                    ])
                    
                    if operacion():
                        resultados_exitosos += 1
                    else:
                        errores_concurrencia += 1
                        
                except Exception as e:
                    errores_concurrencia += 1
        
        # Ejecutar hilos concurrentes
        with ThreadPoolExecutor(max_workers=num_hilos) as executor:
            futuros = [executor.submit(ejecutar_operaciones) for _ in range(num_hilos)]
            
            # Esperar que terminen todos
            for futuro in futuros:
                futuro.result()
        
        tiempo_total = time.time() - inicio
        total_operaciones = num_hilos * num_operaciones_por_hilo
        operaciones_por_segundo = total_operaciones / tiempo_total
        
        print(f"⚡ Operaciones totales: {total_operaciones}")
        print(f"✅ Exitosas: {resultados_exitosos}")
        print(f"❌ Errores: {errores_concurrencia}")
        print(f"🔥 Velocidad: {operaciones_por_segundo:.1f} ops/seg")
        
        self.log_resultado(f"Prueba concurrente completada", tiempo_total)
        self.log_resultado(f"Operaciones por segundo: {operaciones_por_segundo:.1f}")
        
        # Guardar métricas
        self.metricas['concurrencia'] = {
            'hilos': num_hilos,
            'operaciones_totales': total_operaciones,
            'exitosas': resultados_exitosos,
            'errores': errores_concurrencia,
            'tiempo_total': tiempo_total,
            'ops_por_segundo': operaciones_por_segundo
        }
        
        # Evaluar rendimiento concurrente
        if operaciones_por_segundo > 100:
            self.log_resultado("Excelente rendimiento bajo carga")
        elif operaciones_por_segundo > 50:
            self.log_resultado("Buen rendimiento bajo carga")
        else:
            self.log_resultado("Rendimiento bajo carga limitado", nivel="WARNING")
    
    def simular_crecimiento(self):
        """Simula el crecimiento futuro del sistema"""
        print("\n📈 SIMULACIÓN DE CRECIMIENTO")
        print("-" * 50)
        
        # Obtener estadísticas actuales
        productos_actuales = Producto.objects.count()
        transacciones_actuales = Transaccion.objects.count()
        lotes_actuales = LoteProducto.objects.count()
        
        print(f"📊 Estado actual:")
        print(f"   - Productos: {productos_actuales}")
        print(f"   - Transacciones: {transacciones_actuales}")
        print(f"   - Lotes: {lotes_actuales}")
        
        # Proyecciones de crecimiento
        factores_crecimiento = [2, 5, 10, 20, 50]
        
        print(f"\n🔮 Proyecciones de crecimiento:")
        
        for factor in factores_crecimiento:
            productos_proyectados = productos_actuales * factor
            transacciones_proyectadas = transacciones_actuales * factor
            lotes_proyectados = lotes_actuales * factor
            
            # Estimar uso de memoria (muy aproximado)
            # Asumiendo ~1KB por producto, ~0.5KB por transacción, ~0.3KB por lote
            memoria_estimada_mb = (productos_proyectados * 1 + 
                                 transacciones_proyectadas * 0.5 + 
                                 lotes_proyectados * 0.3) / 1024
            
            print(f"   📊 Factor {factor}x:")
            print(f"      - Productos: {productos_proyectados:,}")
            print(f"      - Transacciones: {transacciones_proyectadas:,}")
            print(f"      - Lotes: {lotes_proyectados:,}")
            print(f"      - Memoria estimada: {memoria_estimada_mb:.1f} MB")
            
            # Evaluar viabilidad
            memoria_disponible_mb = self.metricas.get('sistema', {}).get('memoria_disponible_gb', 1) * 1024
            
            if memoria_estimada_mb > memoria_disponible_mb * 0.8:
                print(f"      ⚠️  Puede requerir más memoria")
            elif memoria_estimada_mb > memoria_disponible_mb * 0.5:
                print(f"      🟡 Uso moderado de memoria")
            else:
                print(f"      ✅ Memoria suficiente")
        
        self.log_resultado("Simulación de crecimiento completada")
    
    def crear_productos_masivos_prueba(self, cantidad=100):
        """Crea productos masivos para prueba de rendimiento"""
        print(f"\n🏭 CREANDO {cantidad} PRODUCTOS DE PRUEBA")
        print("-" * 50)
        
        inicio = time.time()
        productos_creados = []
        
        try:
            with transaction.atomic():
                for i in range(cantidad):
                    codigo = f'ESCALA{i:05d}'
                    producto = Producto.objects.create(
                        codigo_barra=codigo,
                        descripcion=f'Producto escalabilidad {i}',
                        stock=random.randint(0, 1000),
                        rut_proveedor='12345678-9',
                        tiene_vencimiento=random.choice([True, False])
                    )
                    productos_creados.append(producto)
                    
                    # Crear algunas transacciones para cada producto
                    if i % 10 == 0:  # Solo cada 10 productos para no sobrecargar
                        Transaccion.objects.create(
                            producto=producto,
                            tipo='entrada',
                            cantidad=random.randint(10, 100),
                            rut_proveedor='12345678-9',
                            observacion=f'Entrada masiva {i}'
                        )
            
            tiempo_creacion = time.time() - inicio
            velocidad = cantidad / tiempo_creacion
            
            print(f"✅ Creados {len(productos_creados)} productos")
            print(f"⚡ Velocidad: {velocidad:.1f} productos/seg")
            
            self.log_resultado(f"Creación masiva completada", tiempo_creacion)
            self.datos_prueba_creados.extend(productos_creados)
            
            # Pruebar consultas después de la inserción masiva
            self.probar_consultas_post_insercion()
            
        except Exception as e:
            self.log_resultado(f"Error en creación masiva: {e}", nivel="ERROR")
    
    def probar_consultas_post_insercion(self):
        """Prueba consultas después de inserción masiva"""
        print("\n🔍 PROBANDO CONSULTAS POST-INSERCIÓN")
        print("-" * 40)
        
        consultas = [
            ("Count productos", lambda: Producto.objects.count()),
            ("Productos con stock", lambda: Producto.objects.filter(stock__gt=0).count()),
            ("Últimos 50 productos", lambda: list(Producto.objects.order_by('-id')[:50])),
            ("Productos por rango stock", lambda: Producto.objects.filter(stock__range=[100, 500]).count()),
            ("Agregación stock total", lambda: Producto.objects.aggregate(total=Sum('stock'))['total'])
        ]
        
        for nombre, consulta in consultas:
            inicio = time.time()
            try:
                resultado = consulta()
                tiempo = time.time() - inicio
                print(f"   ✅ {nombre}: {tiempo:.3f}s")
            except Exception as e:
                tiempo = time.time() - inicio
                print(f"   ❌ {nombre}: Error - {e}")
    
    def limpiar_datos_prueba(self):
        """Limpia todos los datos de prueba"""
        print("\n🧹 LIMPIANDO DATOS DE PRUEBA")
        print("-" * 50)
        
        if self.datos_prueba_creados:
            try:
                # Eliminar transacciones primero (FK)
                Transaccion.objects.filter(
                    producto__in=self.datos_prueba_creados
                ).delete()
                
                # Eliminar productos
                productos_ids = [p.id for p in self.datos_prueba_creados]
                eliminados = Producto.objects.filter(id__in=productos_ids).delete()
                
                print(f"✅ Eliminados {eliminados[0]} registros de prueba")
                self.log_resultado("Limpieza de datos completada")
                
            except Exception as e:
                self.log_resultado(f"Error en limpieza: {e}", nivel="ERROR")
        
        # Limpiar productos de escalabilidad que puedan haber quedado
        productos_escala = Producto.objects.filter(codigo_barra__startswith='ESCALA')
        if productos_escala.exists():
            count = productos_escala.count()
            productos_escala.delete()
            print(f"✅ Eliminados {count} productos de escalabilidad adicionales")
    
    def generar_reporte_escalabilidad(self):
        """Genera reporte final de escalabilidad"""
        print("\n" + "="*60)
        print("📊 REPORTE FINAL DE ESCALABILIDAD")
        print("="*60)
        
        total_resultados = len(self.resultados)
        errores = [r for r in self.resultados if r['nivel'] == 'ERROR']
        warnings = [r for r in self.resultados if r['nivel'] == 'WARNING']
        
        # Evaluar capacidad de escalabilidad
        if len(errores) > 0:
            nivel_escalabilidad = "🔴 LIMITADA"
            mensaje = "Problemas críticos encontrados"
        elif len(warnings) > 3:
            nivel_escalabilidad = "🟡 MODERADA"
            mensaje = "Algunas limitaciones identificadas"
        elif self.metricas.get('concurrencia', {}).get('ops_por_segundo', 0) > 100:
            nivel_escalabilidad = "🟢 EXCELENTE"
            mensaje = "Sistema altamente escalable"
        else:
            nivel_escalabilidad = "🟢 BUENA"
            mensaje = "Sistema escalable con rendimiento adecuado"
        
        print(f"\n{nivel_escalabilidad} - {mensaje}")
        print(f"✅ Pruebas exitosas: {total_resultados - len(errores) - len(warnings)}")
        print(f"⚠️  Advertencias: {len(warnings)}")
        print(f"❌ Errores: {len(errores)}")
        
        # Mostrar métricas clave
        if 'concurrencia' in self.metricas:
            conc = self.metricas['concurrencia']
            print(f"\n⚡ RENDIMIENTO CONCURRENTE:")
            print(f"   - Operaciones/segundo: {conc['ops_por_segundo']:.1f}")
            print(f"   - Éxito: {(conc['exitosas']/conc['operaciones_totales']*100):.1f}%")
        
        if 'sistema' in self.metricas:
            sys = self.metricas['sistema']
            print(f"\n🖥️  RECURSOS SISTEMA:")
            print(f"   - CPU: {sys['cpu_nucleos']} núcleos")
            print(f"   - RAM disponible: {sys['memoria_disponible_gb']:.1f}GB")
            print(f"   - Disco libre: {sys['disco_libre_gb']:.1f}GB")
        
        # Recomendaciones
        print(f"\n💡 RECOMENDACIONES:")
        if len(errores) > 0:
            print("   1. CRÍTICO: Resolver errores de escalabilidad")
        
        ops_seg = self.metricas.get('concurrencia', {}).get('ops_por_segundo', 0)
        if ops_seg < 50:
            print("   2. Optimizar consultas para mejor rendimiento")
        
        memoria_uso = self.metricas.get('sistema', {}).get('memoria_usada_percent', 0)
        if memoria_uso > 70:
            print("   3. Considerar ampliación de memoria")
        
        disco_uso = self.metricas.get('sistema', {}).get('disco_usado_percent', 0)
        if disco_uso > 80:
            print("   4. Considerar ampliación de almacenamiento")
        
        print("   5. Implementar monitoreo de rendimiento continuo")
        print("   6. Planificar archivado de datos históricos")
        print("   7. Considerar índices de base de datos adicionales")
        
        # Guardar reporte
        reporte = {
            'timestamp': datetime.now().isoformat(),
            'nivel_escalabilidad': nivel_escalabilidad,
            'mensaje': mensaje,
            'metricas': self.metricas,
            'resultados': self.resultados,
            'resumen': {
                'total_pruebas': total_resultados,
                'errores': len(errores),
                'warnings': len(warnings),
                'exitosas': total_resultados - len(errores) - len(warnings)
            }
        }
        
        archivo_reporte = f'REPORTE_ESCALABILIDAD_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        try:
            with open(archivo_reporte, 'w', encoding='utf-8') as f:
                json.dump(reporte, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"\n📁 Reporte de escalabilidad guardado: {archivo_reporte}")
            
        except Exception as e:
            print(f"⚠️  No se pudo guardar reporte: {e}")
        
        print("\n🚀 ANÁLISIS DE ESCALABILIDAD COMPLETADO")
        return reporte
    
    def ejecutar_analisis_completo(self):
        """Ejecuta todo el análisis de escalabilidad"""
        print("🚀 ANÁLISIS DE ESCALABILIDAD - SISTEMA BODEGA SEREMI")
        print("="*60)
        print(f"Fecha: {datetime.now().strftime('%d de %B de %Y, %H:%M:%S')}")
        print("="*60)
        
        try:
            self.medir_recursos_sistema()
            self.analizar_base_datos()
            self.prueba_carga_concurrente()
            self.simular_crecimiento()
            self.crear_productos_masivos_prueba(50)  # Reducido para no sobrecargar
            self.limpiar_datos_prueba()
            
            return self.generar_reporte_escalabilidad()
            
        except Exception as e:
            self.log_resultado(f"Error fatal en análisis: {e}", nivel="ERROR")
            return None

def main():
    """Función principal"""
    validador = ValidadorEscalabilidad()
    try:
        return validador.ejecutar_analisis_completo()
    except KeyboardInterrupt:
        print("\n⏹️  Análisis interrumpido por el usuario")
        validador.limpiar_datos_prueba()
    except Exception as e:
        print(f"\n💥 Error fatal: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
