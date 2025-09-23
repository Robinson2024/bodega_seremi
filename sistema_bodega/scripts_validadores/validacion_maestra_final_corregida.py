#!/usr/bin/env python
"""
VALIDACIÓN MAESTRA FINAL - SISTEMA BODEGA SEREMI
Ejecuta todas las validaciones y genera reporte consolidado

Autor: Sistema Bodega SEREMI  
Fecha: 22 de julio de 2025
"""

import os
import sys
import django
import json
import subprocess
from datetime import datetime
import traceback

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
django.setup()

class ValidadorMaestro:
    def __init__(self):
        self.resultados_consolidados = {
            'timestamp': datetime.now().isoformat(),
            'validaciones': {},
            'resumen_ejecutivo': {},
            'recomendaciones_criticas': [],
            'estado_general': ''
        }
        
    def ejecutar_script_validacion(self, script_name, descripcion):
        """Ejecuta un script de validación y captura resultados"""
        print(f"\n{'='*60}")
        print(f"🚀 EJECUTANDO: {descripcion}")
        print(f"📁 Script: {script_name}")
        print(f"{'='*60}")
        
        try:
            # Ejecutar script
            resultado = subprocess.run(
                [sys.executable, script_name],
                capture_output=True,
                text=True,
                cwd=os.getcwd(),
                timeout=300  # 5 minutos máximo por script
            )
            
            salida = resultado.stdout
            errores = resultado.stderr
            codigo_salida = resultado.returncode
            
            # Mostrar salida en tiempo real
            print(salida)
            
            if errores:
                print(f"⚠️  Errores: {errores}")
            
            # Guardar resultado
            self.resultados_consolidados['validaciones'][script_name] = {
                'descripcion': descripcion,
                'codigo_salida': codigo_salida,
                'salida': salida,
                'errores': errores,
                'exitoso': codigo_salida == 0,
                'timestamp': datetime.now().isoformat()
            }
            
            # Buscar archivo de reporte JSON generado
            self.buscar_y_cargar_reporte(script_name)
            
            if codigo_salida == 0:
                print(f"✅ {descripcion} - COMPLETADO EXITOSAMENTE")
            else:
                print(f"❌ {descripcion} - ERROR (código: {codigo_salida})")
                
            return codigo_salida == 0
            
        except subprocess.TimeoutExpired:
            print(f"⏰ {descripcion} - TIMEOUT (más de 5 minutos)")
            self.resultados_consolidados['validaciones'][script_name] = {
                'descripcion': descripcion,
                'error': 'Timeout después de 5 minutos',
                'exitoso': False
            }
            return False
            
        except Exception as e:
            print(f"💥 {descripcion} - ERROR FATAL: {e}")
            self.resultados_consolidados['validaciones'][script_name] = {
                'descripcion': descripcion,
                'error': str(e),
                'exitoso': False
            }
            return False
    
    def buscar_y_cargar_reporte(self, script_name):
        """Busca y carga reportes JSON generados por los scripts"""
        try:
            # Buscar archivos de reporte recientes
            import glob
            import os.path
            
            patrones_reporte = [
                'REPORTE_VALIDACION_*.json',
                'REPORTE_SEGURIDAD_*.json', 
                'REPORTE_ESCALABILIDAD_*.json'
            ]
            
            archivos_encontrados = []
            for patron in patrones_reporte:
                archivos = glob.glob(patron)
                archivos_encontrados.extend(archivos)
            
            # Buscar el más reciente
            if archivos_encontrados:
                archivo_mas_reciente = max(archivos_encontrados, key=os.path.getctime)
                
                # Verificar que sea reciente (último minuto)
                tiempo_archivo = os.path.getctime(archivo_mas_reciente)
                tiempo_actual = datetime.now().timestamp()
                
                if tiempo_actual - tiempo_archivo < 120:  # 2 minutos
                    with open(archivo_mas_reciente, 'r', encoding='utf-8') as f:
                        datos_reporte = json.load(f)
                    
                    # Agregar datos del reporte al resultado
                    if script_name in self.resultados_consolidados['validaciones']:
                        self.resultados_consolidados['validaciones'][script_name]['reporte_json'] = datos_reporte
                        print(f"📊 Reporte cargado: {archivo_mas_reciente}")
                        
        except Exception as e:
            print(f"⚠️  No se pudo cargar reporte JSON: {e}")
    
    def analizar_resultados_consolidados(self):
        """Analiza todos los resultados y genera resumen ejecutivo"""
        print(f"\n{'='*60}")
        print("📊 ANÁLISIS CONSOLIDADO DE RESULTADOS")
        print(f"{'='*60}")
        
        total_validaciones = len(self.resultados_consolidados['validaciones'])
        validaciones_exitosas = sum(1 for v in self.resultados_consolidados['validaciones'].values() if v.get('exitoso', False))
        validaciones_fallidas = total_validaciones - validaciones_exitosas
        
        print(f"📈 Validaciones ejecutadas: {total_validaciones}")
        print(f"✅ Exitosas: {validaciones_exitosas}")
        print(f"❌ Fallidas: {validaciones_fallidas}")
        print(f"📊 Porcentaje éxito: {(validaciones_exitosas/total_validaciones*100):.1f}%")
        
        # Analizar reportes específicos
        vulnerabilidades_criticas = 0
        vulnerabilidades_altas = 0
        problemas_escalabilidad = 0
        errores_funcionales = 0
        
        for script, resultado in self.resultados_consolidados['validaciones'].items():
            if 'reporte_json' in resultado:
                reporte = resultado['reporte_json']
                
                # Análisis de seguridad
                if 'vulnerabilidades' in reporte:
                    for vuln in reporte['vulnerabilidades']:
                        if vuln.get('nivel') == 'CRÍTICA':
                            vulnerabilidades_criticas += 1
                        elif vuln.get('nivel') == 'ALTA':
                            vulnerabilidades_altas += 1
                
                # Análisis de escalabilidad
                if 'nivel_escalabilidad' in reporte:
                    if 'LIMITADA' in reporte['nivel_escalabilidad'] or 'CRÍTICO' in reporte['nivel_escalabilidad']:
                        problemas_escalabilidad += 1
                
                # Análisis funcional
                if 'errores' in reporte and isinstance(reporte['errores'], list):
                    errores_funcionales += len(reporte['errores'])
        
        # Determinar estado general del sistema
        if vulnerabilidades_criticas > 0:
            estado_general = "🔴 CRÍTICO"
            mensaje_estado = "Vulnerabilidades críticas de seguridad detectadas"
        elif problemas_escalabilidad > 0:
            estado_general = "🟠 ALTO RIESGO"
            mensaje_estado = "Problemas serios de escalabilidad"
        elif vulnerabilidades_altas > 0 or errores_funcionales > 3:
            estado_general = "🟡 REQUIERE ATENCIÓN"
            mensaje_estado = "Múltiples problemas menores identificados"
        elif validaciones_fallidas > 0:
            estado_general = "🟡 PARCIALMENTE FUNCIONAL"
            mensaje_estado = "Algunas validaciones fallaron"
        else:
            estado_general = "🟢 EXCELENTE"
            mensaje_estado = "Sistema completamente validado"
        
        self.resultados_consolidados['estado_general'] = estado_general
        self.resultados_consolidados['mensaje_estado'] = mensaje_estado
        
        # Resumen ejecutivo
        self.resultados_consolidados['resumen_ejecutivo'] = {
            'total_validaciones': total_validaciones,
            'validaciones_exitosas': validaciones_exitosas,
            'validaciones_fallidas': validaciones_fallidas,
            'porcentaje_exito': (validaciones_exitosas/total_validaciones*100) if total_validaciones > 0 else 0,
            'vulnerabilidades_criticas': vulnerabilidades_criticas,
            'vulnerabilidades_altas': vulnerabilidades_altas,
            'problemas_escalabilidad': problemas_escalabilidad,
            'errores_funcionales': errores_funcionales
        }
        
        print(f"\n{estado_general} - {mensaje_estado}")
        print(f"🛡️  Vulnerabilidades críticas: {vulnerabilidades_criticas}")
        print(f"⚠️  Vulnerabilidades altas: {vulnerabilidades_altas}")
        print(f"📈 Problemas escalabilidad: {problemas_escalabilidad}")
        print(f"🔧 Errores funcionales: {errores_funcionales}")
    
    def generar_recomendaciones_criticas(self):
        """Genera recomendaciones críticas basadas en los resultados"""
        print(f"\n{'='*60}")
        print("💡 RECOMENDACIONES CRÍTICAS")
        print(f"{'='*60}")
        
        recomendaciones = []
        resumen = self.resultados_consolidados['resumen_ejecutivo']
        
        # Recomendaciones de seguridad
        if resumen['vulnerabilidades_criticas'] > 0:
            recomendaciones.append({
                'prioridad': 'CRÍTICA',
                'categoria': 'Seguridad',
                'descripcion': f"Resolver inmediatamente {resumen['vulnerabilidades_criticas']} vulnerabilidades críticas",
                'acciones': [
                    'Deshabilitar DEBUG en producción',
                    'Cambiar SECRET_KEY por una segura',
                    'Configurar ALLOWED_HOSTS apropiadamente',
                    'Implementar HTTPS'
                ]
            })
        
        if resumen['vulnerabilidades_altas'] > 0:
            recomendaciones.append({
                'prioridad': 'ALTA',
                'categoria': 'Seguridad',
                'descripcion': f"Resolver {resumen['vulnerabilidades_altas']} vulnerabilidades de alto riesgo",
                'acciones': [
                    'Configurar cookies seguras',
                    'Validar formatos de RUT',
                    'Proteger archivos de configuración'
                ]
            })
        
        # Recomendaciones de escalabilidad
        if resumen['problemas_escalabilidad'] > 0:
            recomendaciones.append({
                'prioridad': 'ALTA',
                'categoria': 'Escalabilidad',
                'descripcion': 'Optimizar rendimiento del sistema',
                'acciones': [
                    'Crear índices adicionales en base de datos',
                    'Implementar caché para consultas frecuentes',
                    'Considerar particionado de datos',
                    'Monitorear uso de recursos'
                ]
            })
        
        # Recomendaciones funcionales
        if resumen['errores_funcionales'] > 2:
            recomendaciones.append({
                'prioridad': 'MEDIA',
                'categoria': 'Funcionalidad',
                'descripcion': 'Corregir errores funcionales identificados',
                'acciones': [
                    'Revisar configuración de modelos de usuario',
                    'Validar configuraciones de base de datos',
                    'Implementar manejo de errores robusto'
                ]
            })
        
        # Recomendaciones generales
        recomendaciones.append({
            'prioridad': 'MEDIA',
            'categoria': 'Mantenimiento',
            'descripcion': 'Implementar monitoreo continuo',
            'acciones': [
                'Configurar logging detallado',
                'Implementar alertas automáticas',
                'Programar validaciones periódicas',
                'Crear respaldos automáticos'
            ]
        })
        
        # Mostrar recomendaciones
        for i, rec in enumerate(recomendaciones, 1):
            prioridad_color = {
                'CRÍTICA': '🔴',
                'ALTA': '🟠', 
                'MEDIA': '🟡',
                'BAJA': '🟢'
            }.get(rec['prioridad'], '⚪')
            
            print(f"\n{i}. {prioridad_color} [{rec['prioridad']}] {rec['categoria']}")
            print(f"   📋 {rec['descripcion']}")
            print(f"   🔧 Acciones:")
            for accion in rec['acciones']:
                print(f"      - {accion}")
        
        self.resultados_consolidados['recomendaciones_criticas'] = recomendaciones
    
    def generar_reporte_final_consolidado(self):
        """Genera el reporte final consolidado"""
        print(f"\n{'='*60}")
        print("📁 GENERANDO REPORTE FINAL CONSOLIDADO")
        print(f"{'='*60}")
        
        # Agregar timestamp final
        self.resultados_consolidados['timestamp_final'] = datetime.now().isoformat()
        
        # Guardar reporte consolidado
        archivo_consolidado = f'REPORTE_CONSOLIDADO_FINAL_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        try:
            with open(archivo_consolidado, 'w', encoding='utf-8') as f:
                json.dump(self.resultados_consolidados, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"✅ Reporte consolidado guardado: {archivo_consolidado}")
            
        except Exception as e:
            print(f"❌ Error guardando reporte: {e}")
        
        # Mostrar resumen final
        print(f"\n{'🏆'*20}")
        print("🏆 RESUMEN EJECUTIVO FINAL")
        print(f"{'🏆'*20}")
        
        resumen = self.resultados_consolidados['resumen_ejecutivo']
        estado = self.resultados_consolidados['estado_general']
        mensaje = self.resultados_consolidados['mensaje_estado']
        
        print(f"\n🎯 ESTADO GENERAL: {estado}")
        print(f"📝 {mensaje}")
        
        print(f"\n📊 ESTADÍSTICAS FINALES:")
        print(f"   ✅ Validaciones exitosas: {resumen['validaciones_exitosas']}/{resumen['total_validaciones']}")
        print(f"   📈 Porcentaje de éxito: {resumen['porcentaje_exito']:.1f}%")
        print(f"   🛡️  Vulnerabilidades críticas: {resumen['vulnerabilidades_criticas']}")
        print(f"   ⚠️  Vulnerabilidades altas: {resumen['vulnerabilidades_altas']}")
        print(f"   📈 Problemas escalabilidad: {resumen['problemas_escalabilidad']}")
        print(f"   🔧 Errores funcionales: {resumen['errores_funcionales']}")
        
        # Mostrar próximos pasos
        print(f"\n🚀 PRÓXIMOS PASOS RECOMENDADOS:")
        if resumen['vulnerabilidades_criticas'] > 0:
            print("   1. URGENTE: Resolver vulnerabilidades críticas de seguridad")
        if resumen['problemas_escalabilidad'] > 0:
            print("   2. ALTA PRIORIDAD: Optimizar rendimiento y escalabilidad")
        if resumen['errores_funcionales'] > 0:
            print("   3. MEDIA PRIORIDAD: Corregir errores funcionales")
        print("   4. Implementar monitoreo continuo")
        print("   5. Programar validaciones periódicas (semanales)")
        
        print(f"\n📁 Todos los reportes generados:")
        import glob
        reportes = glob.glob('REPORTE_*.json')
        for reporte in sorted(reportes):
            print(f"   - {reporte}")
        
        print(f"\n🏁 VALIDACIÓN MAESTRA COMPLETADA")
        print(f"📅 {datetime.now().strftime('%d de %B de %Y, %H:%M:%S')}")
        
        return self.resultados_consolidados
    
    def ejecutar_validacion_maestra(self):
        """Ejecuta toda la suite de validación maestra"""
        print("🎯 VALIDACIÓN MAESTRA FINAL - SISTEMA BODEGA SEREMI")
        print("="*70)
        print(f"Inicio: {datetime.now().strftime('%d de %B de %Y, %H:%M:%S')}")
        print("="*70)
        
        # Scripts de validación a ejecutar
        scripts_validacion = [
            ('validacion_completa_final.py', 'Validación Funcional Completa'),
            ('validacion_seguridad.py', 'Auditoría de Seguridad'),
            ('validacion_escalabilidad_simple.py', 'Análisis de Escalabilidad')
        ]
        
        # Ejecutar cada script
        for script, descripcion in scripts_validacion:
            try:
                if os.path.exists(script):
                    self.ejecutar_script_validacion(script, descripcion)
                else:
                    print(f"⚠️  Script no encontrado: {script}")
                    self.resultados_consolidados['validaciones'][script] = {
                        'descripcion': descripcion,
                        'error': 'Archivo no encontrado',
                        'exitoso': False
                    }
            except Exception as e:
                print(f"💥 Error ejecutando {script}: {e}")
                traceback.print_exc()
        
        # Analizar resultados
        self.analizar_resultados_consolidados()
        
        # Generar recomendaciones
        self.generar_recomendaciones_criticas()
        
        # Generar reporte final
        return self.generar_reporte_final_consolidado()

def main():
    """Función principal"""
    validador = ValidadorMaestro()
    try:
        return validador.ejecutar_validacion_maestra()
    except KeyboardInterrupt:
        print("\n⏹️  Validación maestra interrumpida por el usuario")
    except Exception as e:
        print(f"\n💥 Error fatal en validación maestra: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
