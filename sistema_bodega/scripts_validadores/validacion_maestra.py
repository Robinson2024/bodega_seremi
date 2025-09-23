#!/usr/bin/env python
"""
SCRIPT MAESTRO DE VALIDACIÓN FINAL
Sistema de Bodega SEREMI

Este script ejecuta todas las validaciones del sistema:
1. Análisis de escalabilidad completo
2. Validación de bincard y sincronización
3. Validación de dashboard y tiempo real
4. Pruebas de seguridad y rendimiento
5. Generación de reporte consolidado

Autor: Sistema Bodega SEREMI
Fecha: 22 de julio de 2025
Versión: 1.0
"""

import os
import sys
import subprocess
import json
from datetime import datetime
import traceback

class ValidadorMaestro:
    def __init__(self):
        self.resultados = {}
        self.errores_criticos = []
        self.tiempo_total = 0
        
    def ejecutar_script(self, script_name, descripcion):
        """Ejecuta un script de validación específico"""
        print(f"\n{'='*60}")
        print(f"🚀 EJECUTANDO: {descripcion}")
        print(f"📝 Script: {script_name}")
        print(f"{'='*60}")
        
        try:
            inicio = datetime.now()
            
            # Ejecutar script
            resultado = subprocess.run([
                sys.executable, script_name
            ], capture_output=True, text=True, cwd=os.getcwd())
            
            fin = datetime.now()
            duracion = (fin - inicio).total_seconds()
            
            # Guardar resultados
            self.resultados[script_name] = {
                'descripcion': descripcion,
                'inicio': inicio.isoformat(),
                'fin': fin.isoformat(),
                'duracion': duracion,
                'codigo_salida': resultado.returncode,
                'stdout': resultado.stdout,
                'stderr': resultado.stderr,
                'exitoso': resultado.returncode == 0
            }
            
            if resultado.returncode == 0:
                print(f"✅ {descripcion} - COMPLETADO EXITOSAMENTE")
                print(f"⏱️  Duración: {duracion:.2f}s")
            else:
                print(f"❌ {descripcion} - FALLÓ")
                print(f"⏱️  Duración: {duracion:.2f}s")
                print(f"Error: {resultado.stderr}")
                self.errores_criticos.append({
                    'script': script_name,
                    'error': resultado.stderr
                })
            
            # Mostrar últimas líneas de salida
            if resultado.stdout:
                lineas = resultado.stdout.split('\n')
                print("\n📄 Últimas líneas de salida:")
                for linea in lineas[-10:]:  # Últimas 10 líneas
                    if linea.strip():
                        print(f"   {linea}")
            
            return resultado.returncode == 0
            
        except Exception as e:
            print(f"💥 Error ejecutando {script_name}: {e}")
            self.errores_criticos.append({
                'script': script_name,
                'error': str(e)
            })
            return False

    def ejecutar_validacion_completa(self):
        """Ejecuta toda la suite de validación"""
        print("🏁 INICIANDO VALIDACIÓN COMPLETA DEL SISTEMA")
        print("Sistema de Bodega SEREMI - Versión 1.0")
        print(f"Fecha: {datetime.now().strftime('%d de %B de %Y, %H:%M:%S')}")
        print("="*80)
        
        inicio_total = datetime.now()
        
        # Scripts a ejecutar en orden
        scripts = [
            {
                'archivo': 'analisis_escalabilidad.py',
                'descripcion': 'Análisis de Escalabilidad y Funcionalidad Completa'
            },
            {
                'archivo': 'validador_bincard.py',
                'descripcion': 'Validación de Bincard y Sincronización'
            },
            {
                'archivo': 'validador_dashboard.py',
                'descripcion': 'Validación de Dashboard y Tiempo Real'
            }
        ]
        
        scripts_exitosos = 0
        scripts_fallidos = 0
        
        for script in scripts:
            if self.ejecutar_script(script['archivo'], script['descripcion']):
                scripts_exitosos += 1
            else:
                scripts_fallidos += 1
            
            print("\n" + "-"*60)
        
        fin_total = datetime.now()
        self.tiempo_total = (fin_total - inicio_total).total_seconds()
        
        # Generar reporte consolidado
        self.generar_reporte_consolidado(scripts_exitosos, scripts_fallidos)

    def extraer_metricas_reportes(self):
        """Extrae métricas de los reportes individuales generados"""
        metricas_consolidadas = {}
        
        # Buscar archivos de reporte generados
        import glob
        
        reportes_encontrados = []
        patrones = [
            'reporte_validacion_*.json',
            'reporte_bincard_*.json', 
            'reporte_dashboard_*.json'
        ]
        
        for patron in patrones:
            archivos = glob.glob(patron)
            reportes_encontrados.extend(archivos)
        
        # Procesar cada reporte
        for archivo_reporte in reportes_encontrados:
            try:
                with open(archivo_reporte, 'r', encoding='utf-8') as f:
                    datos_reporte = json.load(f)
                
                # Extraer métricas relevantes
                nombre_reporte = archivo_reporte.split('_')[1]  # validacion, bincard, dashboard
                
                if 'resumen' in datos_reporte:
                    metricas_consolidadas[nombre_reporte] = datos_reporte['resumen']
                
                if 'metricas_rendimiento' in datos_reporte:
                    metricas_consolidadas[f'{nombre_reporte}_rendimiento'] = datos_reporte['metricas_rendimiento']
                
                if 'estadisticas' in datos_reporte:
                    metricas_consolidadas[f'{nombre_reporte}_estadisticas'] = datos_reporte['estadisticas']
                    
            except Exception as e:
                print(f"⚠️  Error procesando reporte {archivo_reporte}: {e}")
        
        return metricas_consolidadas

    def generar_reporte_consolidado(self, scripts_exitosos, scripts_fallidos):
        """Genera un reporte consolidado de toda la validación"""
        print("\n" + "="*80)
        print("📊 GENERANDO REPORTE CONSOLIDADO")
        print("="*80)
        
        # Extraer métricas de reportes individuales
        metricas = self.extraer_metricas_reportes()
        
        # Crear reporte consolidado
        reporte_consolidado = {
            'timestamp': datetime.now().isoformat(),
            'duracion_total': self.tiempo_total,
            'resumen_ejecucion': {
                'scripts_ejecutados': len(self.resultados),
                'scripts_exitosos': scripts_exitosos,
                'scripts_fallidos': scripts_fallidos,
                'porcentaje_exito': (scripts_exitosos / len(self.resultados) * 100) if self.resultados else 0
            },
            'resultados_scripts': self.resultados,
            'errores_criticos': self.errores_criticos,
            'metricas_consolidadas': metricas,
            'evaluacion_final': self.evaluar_estado_sistema()
        }
        
        # Guardar reporte consolidado
        archivo_consolidado = f'REPORTE_FINAL_SISTEMA_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        try:
            with open(archivo_consolidado, 'w', encoding='utf-8') as f:
                json.dump(reporte_consolidado, f, indent=2, ensure_ascii=False)
            
            print(f"📁 Reporte consolidado guardado: {archivo_consolidado}")
        except Exception as e:
            print(f"Error guardando reporte consolidado: {e}")
        
        # Mostrar resumen final
        self.mostrar_resumen_final(reporte_consolidado)
        
        return reporte_consolidado

    def evaluar_estado_sistema(self):
        """Evalúa el estado general del sistema basado en los resultados"""
        total_scripts = len(self.resultados)
        scripts_exitosos = sum(1 for r in self.resultados.values() if r['exitoso'])
        errores_criticos = len(self.errores_criticos)
        
        if scripts_exitosos == total_scripts and errores_criticos == 0:
            estado = "EXCELENTE"
            mensaje = "Sistema funcionando perfectamente, listo para producción"
            icono = "🟢"
        elif scripts_exitosos >= total_scripts * 0.8 and errores_criticos <= 2:
            estado = "BUENO"
            mensaje = "Sistema funcionando bien con errores menores"
            icono = "🟡"
        elif scripts_exitosos >= total_scripts * 0.6:
            estado = "REGULAR"
            mensaje = "Sistema con problemas moderados que requieren atención"
            icono = "🟠"
        else:
            estado = "CRÍTICO"
            mensaje = "Sistema con problemas graves que requieren corrección inmediata"
            icono = "🔴"
        
        return {
            'estado': estado,
            'mensaje': mensaje,
            'icono': icono,
            'puntuacion': (scripts_exitosos / total_scripts * 100) if total_scripts > 0 else 0
        }

    def mostrar_resumen_final(self, reporte):
        """Muestra el resumen final de la validación"""
        print("\n" + "🏆" * 80)
        print("📋 RESUMEN FINAL DE VALIDACIÓN DEL SISTEMA")
        print("🏆" * 80)
        
        evaluacion = reporte['evaluacion_final']
        resumen = reporte['resumen_ejecucion']
        
        print(f"\n{evaluacion['icono']} ESTADO DEL SISTEMA: {evaluacion['estado']}")
        print(f"📝 {evaluacion['mensaje']}")
        print(f"📊 Puntuación: {evaluacion['puntuacion']:.1f}%")
        
        print(f"\n⏱️  TIEMPO TOTAL DE VALIDACIÓN: {self.tiempo_total:.2f} segundos")
        
        print(f"\n📈 RESUMEN DE EJECUCIÓN:")
        print(f"   ✅ Scripts exitosos: {resumen['scripts_exitosos']}")
        print(f"   ❌ Scripts fallidos: {resumen['scripts_fallidos']}")
        print(f"   📊 Porcentaje de éxito: {resumen['porcentaje_exito']:.1f}%")
        
        if self.errores_criticos:
            print(f"\n🚨 ERRORES CRÍTICOS DETECTADOS:")
            for error in self.errores_criticos:
                print(f"   - {error['script']}: {error['error'][:100]}...")
        
        # Mostrar métricas consolidadas si están disponibles
        if 'metricas_consolidadas' in reporte and reporte['metricas_consolidadas']:
            print(f"\n📊 MÉTRICAS CONSOLIDADAS:")
            for categoria, metricas in reporte['metricas_consolidadas'].items():
                if isinstance(metricas, dict):
                    print(f"   {categoria.upper()}:")
                    for metrica, valor in metricas.items():
                        print(f"     - {metrica}: {valor}")
        
        # Recomendaciones finales
        print(f"\n💡 RECOMENDACIONES:")
        if evaluacion['estado'] == "EXCELENTE":
            print("   • Sistema listo para producción")
            print("   • Continuar con monitoreo regular")
            print("   • Documentar configuración actual")
        elif evaluacion['estado'] == "BUENO":
            print("   • Revisar y corregir errores menores")
            print("   • Implementar monitoreo adicional")
            print("   • Planificar mejoras de rendimiento")
        elif evaluacion['estado'] == "REGULAR":
            print("   • Corregir problemas detectados antes de producción")
            print("   • Revisar configuración de base de datos")
            print("   • Optimizar consultas lentas")
        else:  # CRÍTICO
            print("   • NO DESPLEGAR EN PRODUCCIÓN")
            print("   • Corregir errores críticos inmediatamente")
            print("   • Revisar integridad de datos")
            print("   • Ejecutar correcciones automáticas donde sea posible")
        
        print("\n" + "🏁" * 80)
        print("VALIDACIÓN COMPLETA FINALIZADA")
        print("🏁" * 80)

def crear_script_ejecucion():
    """Crea un script batch para ejecutar fácilmente las validaciones"""
    contenido_batch = """@echo off
echo ====================================
echo Sistema de Validacion Bodega SEREMI
echo ====================================
echo.

echo Iniciando validacion completa del sistema...
python validacion_maestra.py

echo.
echo Validacion completada. Presione cualquier tecla para continuar.
pause > nul
"""
    
    try:
        with open('ejecutar_validacion.bat', 'w', encoding='utf-8') as f:
            f.write(contenido_batch)
        print("📝 Script de ejecución creado: ejecutar_validacion.bat")
    except Exception as e:
        print(f"Error creando script batch: {e}")

def main():
    """Función principal"""
    print("🔍 VALIDADOR MAESTRO - Sistema Bodega SEREMI")
    print("Iniciando validación completa del sistema...")
    print("="*50)
    
    # Crear script de ejecución batch
    crear_script_ejecucion()
    
    validador = ValidadorMaestro()
    
    try:
        validador.ejecutar_validacion_completa()
    except KeyboardInterrupt:
        print("\n⏹️  Validación interrumpida por el usuario")
    except Exception as e:
        print(f"\n💥 Error fatal en validación maestra: {e}")
        traceback.print_exc()
    finally:
        print("\n🔚 Proceso de validación finalizado")

if __name__ == "__main__":
    main()
