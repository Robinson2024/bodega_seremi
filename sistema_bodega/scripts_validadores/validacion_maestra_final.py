#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VALIDACION MAESTRA FINAL - SISTEMA BODEGA SEREMI
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
        """Ejecuta un script de validacion y captura resultados"""
        print(f"\n{'='*60}")
        print(f"EJECUTANDO: {descripcion}")
        print(f"Script: {script_name}")
        print(f"{'='*60}")
        
        try:
            # Ejecutar script
            resultado = subprocess.run(
                [sys.executable, script_name],
                capture_output=True,
                text=True,
                cwd=os.getcwd(),
                timeout=300  # 5 minutos maximo por script
            )
            
            salida = resultado.stdout
            errores = resultado.stderr
            exitoso = resultado.returncode == 0
            
            print(salida)
            if errores:
                print(f"Errores: {errores}")
            
            # Buscar archivo de reporte generado
            import glob
            reportes = glob.glob('reporte_*.json')
            reporte_mas_reciente = None
            
            if reportes:
                # Obtener el mas reciente
                reporte_mas_reciente = max(reportes, key=os.path.getctime)
                with open(reporte_mas_reciente, 'r', encoding='utf-8') as f:
                    datos_reporte = json.load(f)
            else:
                datos_reporte = None
            
            # Guardar resultado
            self.resultados_consolidados['validaciones'][script_name] = {
                'descripcion': descripcion,
                'exitoso': exitoso,
                'salida': salida,
                'errores': errores,
                'archivo_reporte': reporte_mas_reciente,
                'datos_reporte': datos_reporte
            }
            
            if exitoso:
                print(f"EXITO: {descripcion} completado exitosamente")
            else:
                print(f"ERROR: {descripcion} fallo con errores")
                
        except subprocess.TimeoutExpired:
            print(f"Timeout: {descripcion} excedio tiempo limite")
            self.resultados_consolidados['validaciones'][script_name] = {
                'descripcion': descripcion,
                'exitoso': False,
                'error': 'Timeout'
            }
        except Exception as e:
            print(f"Error ejecutando {descripcion}: {e}")
            self.resultados_consolidados['validaciones'][script_name] = {
                'descripcion': descripcion,
                'exitoso': False,
                'error': str(e)
            }

    def analizar_resultados_consolidados(self):
        """Analiza resultados y genera metricas"""
        print(f"\n{'='*60}")
        print("ANALISIS CONSOLIDADO DE RESULTADOS")
        print(f"{'='*60}")
        
        total_validaciones = len(self.resultados_consolidados['validaciones'])
        validaciones_exitosas = 0
        vulnerabilidades_criticas = 0
        vulnerabilidades_altas = 0
        problemas_escalabilidad = 0
        errores_funcionales = 0
        
        for script, resultado in self.resultados_consolidados['validaciones'].items():
            if resultado.get('exitoso', False):
                validaciones_exitosas += 1
                
                # Analizar datos del reporte si existe
                datos = resultado.get('datos_reporte')
                if datos:
                    errores = datos.get('errores', [])
                    
                    # Clasificar segun tipo de script
                    if 'seguridad' in script:
                        for error in errores:
                            mensaje = error.get('mensaje', '').lower()
                            if 'debug' in mensaje or 'secret' in mensaje:
                                vulnerabilidades_criticas += 1
                            elif 'host' in mensaje or 'csrf' in mensaje:
                                vulnerabilidades_altas += 1
                    
                    elif 'escalabilidad' in script:
                        problemas_escalabilidad += len(errores)
                    
                    elif 'completa' in script:
                        errores_funcionales += len(errores)
            else:
                errores_funcionales += 1
        
        porcentaje_exito = (validaciones_exitosas / total_validaciones * 100) if total_validaciones > 0 else 0
        
        # Determinar estado general
        if vulnerabilidades_criticas > 0:
            estado = "CRITICO"
        elif vulnerabilidades_altas > 2:
            estado = "ALTO RIESGO"
        elif errores_funcionales > 1:
            estado = "OBSERVACIONES"
        else:
            estado = "APROBADO"
        
        # Guardar resumen
        self.resultados_consolidados['resumen_ejecutivo'] = {
            'total_validaciones': total_validaciones,
            'validaciones_exitosas': validaciones_exitosas,
            'porcentaje_exito': porcentaje_exito,
            'vulnerabilidades_criticas': vulnerabilidades_criticas,
            'vulnerabilidades_altas': vulnerabilidades_altas,
            'problemas_escalabilidad': problemas_escalabilidad,
            'errores_funcionales': errores_funcionales
        }
        
        self.resultados_consolidados['estado_general'] = estado
        
        # Mostrar resumen
        print(f"Validaciones exitosas: {validaciones_exitosas}/{total_validaciones}")
        print(f"Porcentaje de exito: {porcentaje_exito:.1f}%")
        print(f"Vulnerabilidades criticas: {vulnerabilidades_criticas}")
        print(f"Vulnerabilidades altas: {vulnerabilidades_altas}")
        print(f"Problemas escalabilidad: {problemas_escalabilidad}")
        print(f"Errores funcionales: {errores_funcionales}")

    def generar_recomendaciones_criticas(self):
        """Genera recomendaciones criticas"""
        print(f"\n{'='*60}")
        print("RECOMENDACIONES CRITICAS")
        print(f"{'='*60}")
        
        resumen = self.resultados_consolidados['resumen_ejecutivo']
        recomendaciones = []
        
        if resumen['vulnerabilidades_criticas'] > 0:
            recomendaciones.append({
                'prioridad': 'CRITICA',
                'categoria': 'Seguridad',
                'descripcion': 'Resolver vulnerabilidades criticas inmediatamente',
                'acciones': [
                    'Cambiar DEBUG=False en produccion',
                    'Generar SECRET_KEY segura',
                    'Configurar ALLOWED_HOSTS',
                    'Implementar HTTPS'
                ]
            })
        
        if resumen['problemas_escalabilidad'] > 0:
            recomendaciones.append({
                'prioridad': 'ALTA',
                'categoria': 'Rendimiento',
                'descripcion': 'Optimizar escalabilidad del sistema',
                'acciones': [
                    'Crear indices en base de datos',
                    'Implementar cache',
                    'Monitorear recursos'
                ]
            })
        
        # Mostrar recomendaciones
        for i, rec in enumerate(recomendaciones, 1):
            print(f"\n{i}. [{rec['prioridad']}] {rec['categoria']}")
            print(f"   {rec['descripcion']}")
            for accion in rec['acciones']:
                print(f"   - {accion}")
        
        self.resultados_consolidados['recomendaciones_criticas'] = recomendaciones

    def generar_reporte_final(self):
        """Genera reporte final consolidado"""
        print(f"\n{'='*60}")
        print("GENERANDO REPORTE FINAL")
        print(f"{'='*60}")
        
        # Guardar reporte
        archivo = f'REPORTE_MAESTRO_FINAL_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        try:
            with open(archivo, 'w', encoding='utf-8') as f:
                json.dump(self.resultados_consolidados, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"Reporte guardado: {archivo}")
            
        except Exception as e:
            print(f"Error guardando reporte: {e}")
        
        # Mostrar resumen final
        resumen = self.resultados_consolidados['resumen_ejecutivo']
        estado = self.resultados_consolidados['estado_general']
        
        print(f"\nESTADO FINAL: {estado}")
        print(f"Exito general: {resumen['porcentaje_exito']:.1f}%")
        
        if resumen['vulnerabilidades_criticas'] > 0:
            print("ACCION REQUERIDA: Resolver vulnerabilidades criticas")
        else:
            print("No se detectaron vulnerabilidades criticas")

    def ejecutar_validacion_maestra(self):
        """Ejecuta toda la suite de validacion"""
        print("VALIDACION MAESTRA FINAL - SISTEMA BODEGA SEREMI")
        print("="*70)
        print(f"Inicio: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("="*70)
        
        # Scripts a ejecutar
        scripts = [
            ('validacion_completa_final.py', 'Validacion Funcional Completa'),
            ('validacion_seguridad.py', 'Auditoria de Seguridad'),
            ('validacion_escalabilidad_simple.py', 'Analisis de Escalabilidad')
        ]
        
        # Ejecutar cada script
        for script, descripcion in scripts:
            if os.path.exists(script):
                self.ejecutar_script_validacion(script, descripcion)
            else:
                print(f"Script no encontrado: {script}")
        
        # Analizar resultados
        self.analizar_resultados_consolidados()
        
        # Generar recomendaciones
        self.generar_recomendaciones_criticas()
        
        # Generar reporte final
        self.generar_reporte_final()
        
        print(f"\nVALIDACION MAESTRA COMPLETADA")
        return self.resultados_consolidados

def main():
    """Funcion principal"""
    validador = ValidadorMaestro()
    try:
        return validador.ejecutar_validacion_maestra()
    except KeyboardInterrupt:
        print("\nValidacion interrumpida por el usuario")
    except Exception as e:
        print(f"\nError fatal: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
