#!/usr/bin/env python
"""
Script simplificado para identificar vulnerabilidades técnicas reales
Corregido para trabajar con la arquitectura actual del sistema
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db import connection
from django.conf import settings
import sqlite3

def main():
    """Análisis de vulnerabilidades técnicas reales"""
    
    print("🔍 ANÁLISIS DE VULNERABILIDADES TÉCNICAS")
    print("=" * 50)
    
    vulnerabilidades = []
    
    # 1. Verificar configuración de DEBUG
    if settings.DEBUG:
        vulnerabilidades.append({
            'tipo': 'CRÍTICA',
            'categoria': 'Configuración',
            'problema': 'DEBUG=True en producción',
            'impacto': 'Exposición de información sensible',
            'solucion': 'Cambiar DEBUG=False en producción'
        })
    
    # 2. Verificar SECRET_KEY
    if settings.SECRET_KEY == 'django-insecure-tu_clave_secreta_aqui':
        vulnerabilidades.append({
            'tipo': 'CRÍTICA',
            'categoria': 'Seguridad',
            'problema': 'SECRET_KEY por defecto',
            'impacto': 'Sesiones y cookies comprometidas',
            'solucion': 'Generar SECRET_KEY único y seguro'
        })
    
    # 3. Verificar configuración de base de datos
    db_config = settings.DATABASES['default']
    if db_config['ENGINE'] == 'django.db.backends.sqlite3':
        vulnerabilidades.append({
            'tipo': 'MEDIA',
            'categoria': 'Escalabilidad',
            'problema': 'Uso de SQLite en producción',
            'impacto': 'Limitaciones de concurrencia y escalabilidad',
            'solucion': 'Migrar a PostgreSQL o MySQL'
        })
    
    # 4. Verificar modelos disponibles
    from django.apps import apps
    modelos_disponibles = []
    
    try:
        for model in apps.get_models():
            modelos_disponibles.append(model.__name__)
        
        print(f"📊 Modelos disponibles: {', '.join(modelos_disponibles)}")
        
        # Verificar si existen modelos críticos
        modelos_criticos = ['Producto', 'Transaccion', 'LoteProducto', 'CustomUser']
        modelos_faltantes = [m for m in modelos_criticos if m not in modelos_disponibles]
        
        if modelos_faltantes:
            vulnerabilidades.append({
                'tipo': 'CRÍTICA',
                'categoria': 'Arquitectura',
                'problema': f'Modelos faltantes: {modelos_faltantes}',
                'impacto': 'Funcionalidad core comprometida',
                'solucion': 'Implementar modelos faltantes'
            })
            
    except Exception as e:
        vulnerabilidades.append({
            'tipo': 'CRÍTICA',
            'categoria': 'Sistema',
            'problema': f'Error al acceder a modelos: {str(e)}',
            'impacto': 'Sistema no funcional',
            'solucion': 'Revisar configuración de Django'
        })
    
    # 5. Verificar estructura de base de datos
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'django_%' AND name != 'sqlite_sequence'
            """)
            tablas = [row[0] for row in cursor.fetchall()]
            
        print(f"🗄️ Tablas en BD: {', '.join(tablas)}")
        
        # Verificar consistencia
        tablas_esperadas = ['accounts_customuser', 'bodega_producto', 'bodega_transaccion', 'bodega_loteproducto']
        tablas_faltantes = [t for t in tablas_esperadas if t not in tablas]
        
        if tablas_faltantes:
            vulnerabilidades.append({
                'tipo': 'ALTA',
                'categoria': 'Base de Datos',
                'problema': f'Tablas faltantes: {tablas_faltantes}',
                'impacto': 'Datos no pueden almacenarse correctamente',
                'solucion': 'Ejecutar migraciones pendientes'
            })
            
    except Exception as e:
        vulnerabilidades.append({
            'tipo': 'CRÍTICA',
            'categoria': 'Base de Datos',
            'problema': f'Error al acceder a BD: {str(e)}',
            'impacto': 'Base de datos no accesible',
            'solucion': 'Verificar configuración y permisos de BD'
        })
    
    # 6. Verificar archivos críticos
    archivos_criticos = [
        'manage.py',
        'sistema_bodega/settings.py',
        'sistema_bodega/urls.py',
        'accounts/models.py',
        'accounts/views.py'
    ]
    
    for archivo in archivos_criticos:
        ruta_archivo = BASE_DIR / archivo
        if not ruta_archivo.exists():
            vulnerabilidades.append({
                'tipo': 'ALTA',
                'categoria': 'Estructura',
                'problema': f'Archivo faltante: {archivo}',
                'impacto': 'Funcionalidad comprometida',
                'solucion': f'Crear o restaurar {archivo}'
            })
    
    # Mostrar resultados
    print("\n🚨 VULNERABILIDADES ENCONTRADAS:")
    print("=" * 50)
    
    if not vulnerabilidades:
        print("✅ No se encontraron vulnerabilidades técnicas críticas")
        return
    
    # Agrupar por tipo
    criticas = [v for v in vulnerabilidades if v['tipo'] == 'CRÍTICA']
    altas = [v for v in vulnerabilidades if v['tipo'] == 'ALTA']
    medias = [v for v in vulnerabilidades if v['tipo'] == 'MEDIA']
    
    for tipo, lista in [('CRÍTICAS', criticas), ('ALTAS', altas), ('MEDIAS', medias)]:
        if lista:
            print(f"\n🔴 VULNERABILIDADES {tipo}:")
            for i, vuln in enumerate(lista, 1):
                print(f"\n{i}. {vuln['categoria']}: {vuln['problema']}")
                print(f"   💥 Impacto: {vuln['impacto']}")
                print(f"   🔧 Solución: {vuln['solucion']}")
    
    # Resumen final
    total = len(vulnerabilidades)
    print(f"\n📊 RESUMEN:")
    print(f"Total vulnerabilidades: {total}")
    print(f"Críticas: {len(criticas)}")
    print(f"Altas: {len(altas)}")
    print(f"Medias: {len(medias)}")
    
    if criticas:
        print("\n⚠️ ACCIÓN REQUERIDA: Hay vulnerabilidades críticas que requieren atención inmediata")
    else:
        print("\n✅ No hay vulnerabilidades críticas detectadas")

if __name__ == "__main__":
    main()
