#!/usr/bin/env python
"""
CONFIGURADOR DE DEPENDENCIAS PARA VALIDACIÓN
Sistema de Bodega SEREMI

Este script instala y configura las dependencias necesarias
para ejecutar todas las validaciones del sistema.

Autor: Sistema Bodega SEREMI
Fecha: 22 de julio de 2025
"""

import subprocess
import sys
import os

def instalar_dependencia(paquete, nombre_mostrar=None):
    """Instala una dependencia de Python"""
    nombre = nombre_mostrar or paquete
    print(f"📦 Instalando {nombre}...")
    
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', paquete])
        print(f"✅ {nombre} instalado exitosamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando {nombre}: {e}")
        return False
    except Exception as e:
        print(f"💥 Error inesperado instalando {nombre}: {e}")
        return False

def verificar_dependencia(modulo, nombre_mostrar=None):
    """Verifica si una dependencia está disponible"""
    nombre = nombre_mostrar or modulo
    try:
        __import__(modulo)
        print(f"✅ {nombre} ya está disponible")
        return True
    except ImportError:
        print(f"⚠️  {nombre} no está disponible")
        return False

def configurar_entorno():
    """Configura el entorno para las validaciones"""
    print("🔧 CONFIGURANDO ENTORNO DE VALIDACIÓN")
    print("="*50)
    
    dependencias = [
        # Dependencias básicas
        ('openpyxl', 'OpenPyXL (Excel)'),
        ('pandas', 'Pandas (Análisis de datos)'),
        ('requests', 'Requests (HTTP)'),
        
        # Dependencias opcionales para UI
        ('selenium', 'Selenium (Pruebas UI)'),
        
        # Dependencias para reportes
        ('matplotlib', 'Matplotlib (Gráficos)'),
        ('pillow', 'Pillow (Imágenes)'),
    ]
    
    instalaciones_exitosas = 0
    instalaciones_fallidas = 0
    
    for paquete, nombre in dependencias:
        if not verificar_dependencia(paquete.split('[')[0], nombre):
            if instalar_dependencia(paquete, nombre):
                instalaciones_exitosas += 1
            else:
                instalaciones_fallidas += 1
        else:
            instalaciones_exitosas += 1
    
    print(f"\n📊 RESUMEN DE INSTALACIÓN:")
    print(f"✅ Exitosas: {instalaciones_exitosas}")
    print(f"❌ Fallidas: {instalaciones_fallidas}")
    
    # Configurar ChromeDriver para Selenium (opcional)
    configurar_chromedriver()
    
    # Crear directorio de reportes
    crear_directorio_reportes()
    
    return instalaciones_fallidas == 0

def configurar_chromedriver():
    """Configura ChromeDriver para Selenium"""
    print(f"\n🌐 CONFIGURANDO CHROMEDRIVER")
    print("-" * 30)
    
    try:
        # Verificar si Chrome está instalado
        if os.name == 'nt':  # Windows
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
            ]
            chrome_instalado = any(os.path.exists(path) for path in chrome_paths)
        else:
            chrome_instalado = subprocess.run(['which', 'google-chrome'], 
                                            capture_output=True).returncode == 0
        
        if chrome_instalado:
            print("✅ Google Chrome detectado")
            
            # Intentar instalar webdriver-manager
            if instalar_dependencia('webdriver-manager', 'WebDriver Manager'):
                print("✅ ChromeDriver configurado automáticamente")
            else:
                print("⚠️  ChromeDriver manual requerido para pruebas UI completas")
        else:
            print("⚠️  Google Chrome no detectado")
            print("   Las pruebas de UI se saltarán automáticamente")
    
    except Exception as e:
        print(f"⚠️  Error configurando ChromeDriver: {e}")
        print("   Las pruebas de UI se saltarán automáticamente")

def crear_directorio_reportes():
    """Crea directorio para reportes si no existe"""
    try:
        if not os.path.exists('reportes'):
            os.makedirs('reportes')
            print("📁 Directorio de reportes creado")
        else:
            print("📁 Directorio de reportes ya existe")
    except Exception as e:
        print(f"⚠️  Error creando directorio de reportes: {e}")

def verificar_django():
    """Verifica que Django esté configurado correctamente"""
    print(f"\n🔧 VERIFICANDO CONFIGURACIÓN DJANGO")
    print("-" * 40)
    
    try:
        import django
        print(f"✅ Django {django.get_version()} detectado")
        
        # Verificar configuración
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
        django.setup()
        
        print("✅ Configuración Django cargada correctamente")
        
        # Verificar modelos
        from accounts.models import Producto, MovimientoStock, LoteVencimiento
        print("✅ Modelos de aplicación accesibles")
        
        return True
        
    except Exception as e:
        print(f"❌ Error configurando Django: {e}")
        print("   Asegúrese de estar en el directorio correcto del proyecto")
        return False

def generar_documentacion():
    """Genera documentación de uso"""
    documentacion = """
# GUÍA DE VALIDACIÓN DEL SISTEMA BODEGA SEREMI

## Archivos de Validación Creados:

1. **analisis_escalabilidad.py** - Validación completa del sistema
   - Flujo completo de productos
   - Pruebas de escalabilidad
   - Validación de seguridad

2. **validador_bincard.py** - Validación específica de bincard
   - Sincronización stock vs movimientos
   - Lógica FIFO de lotes
   - Consistencia de datos

3. **validador_dashboard.py** - Validación de dashboard
   - Métricas en tiempo real
   - Exportaciones Excel
   - Gráficos y visualizaciones

4. **validacion_maestra.py** - Script maestro
   - Ejecuta todas las validaciones
   - Genera reporte consolidado
   - Evaluación final del sistema

## Cómo ejecutar las validaciones:

### Opción 1: Script maestro (Recomendado)
```bash
python validacion_maestra.py
```

### Opción 2: Scripts individuales
```bash
python analisis_escalabilidad.py
python validador_bincard.py
python validador_dashboard.py
```

### Opción 3: Corrección automática de bincard
```bash
python validador_bincard.py --corregir
```

## Reportes generados:

- `REPORTE_FINAL_SISTEMA_YYYYMMDD_HHMMSS.json` - Reporte consolidado
- `reporte_validacion_YYYYMMDD_HHMMSS.json` - Validación general
- `reporte_bincard_YYYYMMDD_HHMMSS.json` - Validación bincard
- `reporte_dashboard_YYYYMMDD_HHMMSS.json` - Validación dashboard

## Estados del sistema:

- 🟢 **EXCELENTE**: Sistema listo para producción
- 🟡 **BUENO**: Errores menores, revisión recomendada
- 🟠 **REGULAR**: Problemas moderados, corrección necesaria
- 🔴 **CRÍTICO**: Problemas graves, NO desplegar

## Dependencias instaladas:

- openpyxl: Exportaciones Excel
- pandas: Análisis de datos
- selenium: Pruebas de UI (opcional)
- matplotlib: Gráficos (opcional)

¡El sistema está listo para validación completa!
"""
    
    try:
        with open('GUIA_VALIDACION.md', 'w', encoding='utf-8') as f:
            f.write(documentacion)
        print("📖 Guía de validación creada: GUIA_VALIDACION.md")
    except Exception as e:
        print(f"⚠️  Error creando documentación: {e}")

def main():
    """Función principal de configuración"""
    print("🚀 CONFIGURADOR DE VALIDACIÓN - Sistema Bodega SEREMI")
    print("="*60)
    print("Este script preparará el entorno para ejecutar validaciones completas")
    print("="*60)
    
    # Verificar Django primero
    if not verificar_django():
        print("\n❌ No se puede continuar sin Django configurado correctamente")
        return False
    
    # Configurar dependencias
    if configurar_entorno():
        print("\n✅ Entorno configurado exitosamente")
    else:
        print("\n⚠️  Entorno configurado con algunas dependencias faltantes")
        print("   Las validaciones básicas funcionarán, algunas características avanzadas podrían no estar disponibles")
    
    # Generar documentación
    generar_documentacion()
    
    print("\n" + "="*60)
    print("🎉 CONFIGURACIÓN COMPLETADA")
    print("="*60)
    print("\nPuede ejecutar las validaciones con:")
    print("  python validacion_maestra.py")
    print("\nO revisar la guía completa en: GUIA_VALIDACION.md")
    print("="*60)
    
    return True

if __name__ == "__main__":
    main()
