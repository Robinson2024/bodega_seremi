#!/usr/bin/env python
"""
DEMO DE VALIDACIÓN DEL SISTEMA
Sistema de Bodega SEREMI

Este script demuestra cómo usar el sistema de validación
y muestra ejemplos de ejecución.

Autor: Sistema Bodega SEREMI
Fecha: 22 de julio de 2025
"""

import os
import sys
import subprocess
import time

def mostrar_banner():
    """Muestra el banner del demo"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║    🔍 DEMO DEL SISTEMA DE VALIDACIÓN BODEGA SEREMI           ║
    ║                                                              ║
    ║    Este demo le guiará a través del proceso completo        ║
    ║    de validación del sistema.                               ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def pausa_demo(mensaje="Presione Enter para continuar..."):
    """Pausa el demo para interacción del usuario"""
    input(f"\n{mensaje}")

def ejecutar_paso(titulo, comando, descripcion=""):
    """Ejecuta un paso del demo"""
    print(f"\n{'='*60}")
    print(f"🚀 {titulo}")
    print(f"{'='*60}")
    
    if descripcion:
        print(f"📝 {descripcion}")
    
    print(f"💻 Comando: {comando}")
    pausa_demo("¿Ejecutar este paso? (Enter para continuar)")
    
    try:
        if comando.startswith('python'):
            # Ejecutar comando Python
            resultado = subprocess.run(comando.split(), capture_output=True, text=True)
            
            if resultado.returncode == 0:
                print("✅ Comando ejecutado exitosamente")
                
                # Mostrar últimas líneas de salida
                if resultado.stdout:
                    lineas = resultado.stdout.split('\n')
                    print("\n📄 Últimas líneas de salida:")
                    for linea in lineas[-5:]:
                        if linea.strip():
                            print(f"   {linea}")
            else:
                print("❌ Error en la ejecución:")
                print(resultado.stderr)
        else:
            # Comando informativo
            print(f"ℹ️  {comando}")
    
    except Exception as e:
        print(f"💥 Error: {e}")

def demo_completo():
    """Ejecuta el demo completo"""
    mostrar_banner()
    
    print("\n🎯 Este demo cubrirá:")
    print("   1. Configuración inicial del entorno")
    print("   2. Validación completa del sistema")
    print("   3. Validaciones específicas")
    print("   4. Interpretación de resultados")
    
    pausa_demo()
    
    # Paso 1: Configuración
    ejecutar_paso(
        "PASO 1: CONFIGURACIÓN DEL ENTORNO",
        "python configurar_validacion.py",
        "Instala dependencias y prepara el entorno para validaciones"
    )
    
    # Paso 2: Validación maestra
    ejecutar_paso(
        "PASO 2: VALIDACIÓN COMPLETA DEL SISTEMA",
        "python validacion_maestra.py",
        "Ejecuta todas las validaciones y genera reporte consolidado"
    )
    
    # Paso 3: Validación específica (bincard)
    ejecutar_paso(
        "PASO 3: VALIDACIÓN ESPECÍFICA - BINCARD",
        "python validador_bincard.py",
        "Valida sincronización de stock y lógica FIFO"
    )
    
    # Paso 4: Mostrar reportes
    ejecutar_paso(
        "PASO 4: REVISAR REPORTES GENERADOS",
        "Revisar archivos REPORTE_*.json en el directorio actual",
        "Los reportes contienen análisis detallado del sistema"
    )
    
    # Resumen final
    print(f"\n{'🎉'*60}")
    print("DEMO COMPLETADO")
    print(f"{'🎉'*60}")
    
    print("\n📊 Reportes generados:")
    print("   • REPORTE_FINAL_SISTEMA_*.json - Evaluación consolidada")
    print("   • reporte_validacion_*.json - Validación general")
    print("   • reporte_bincard_*.json - Estado del bincard")
    print("   • reporte_dashboard_*.json - Funcionalidades dashboard")
    
    print("\n📖 Documentación:")
    print("   • README_VALIDACION.md - Guía completa")
    print("   • GUIA_VALIDACION.md - Instrucciones de uso")
    
    print("\n💡 Próximos pasos:")
    print("   1. Revisar los reportes JSON generados")
    print("   2. Corregir cualquier error detectado")
    print("   3. Ejecutar validaciones periódicamente")
    print("   4. Documentar configuración actual")

def demo_rapido():
    """Demo rápido sin pausas"""
    print("🚀 DEMO RÁPIDO - VALIDACIÓN AUTOMÁTICA")
    print("="*50)
    
    comandos = [
        ("Configuración", "python configurar_validacion.py"),
        ("Validación Bincard", "python validador_bincard.py"),
        ("Validación Dashboard", "python validador_dashboard.py")
    ]
    
    for nombre, comando in comandos:
        print(f"\n▶️  Ejecutando: {nombre}")
        try:
            subprocess.run(comando.split(), check=True, capture_output=True)
            print(f"✅ {nombre} completado")
        except subprocess.CalledProcessError:
            print(f"❌ Error en {nombre}")
        except Exception as e:
            print(f"💥 Error: {e}")
    
    print("\n🏁 Demo rápido completado")

def mostrar_menu():
    """Muestra el menú principal del demo"""
    while True:
        print("\n" + "="*50)
        print("🔍 DEMO SISTEMA DE VALIDACIÓN")
        print("="*50)
        print("1. 📋 Demo completo (interactivo)")
        print("2. ⚡ Demo rápido (automático)")
        print("3. 🔧 Solo configuración")
        print("4. 📊 Solo validación maestra")
        print("5. 📖 Ver documentación")
        print("6. 🚪 Salir")
        print("="*50)
        
        try:
            opcion = input("Seleccione una opción (1-6): ").strip()
            
            if opcion == "1":
                demo_completo()
            elif opcion == "2":
                demo_rapido()
            elif opcion == "3":
                ejecutar_paso(
                    "CONFIGURACIÓN DEL ENTORNO",
                    "python configurar_validacion.py",
                    "Prepara el entorno para validaciones"
                )
            elif opcion == "4":
                ejecutar_paso(
                    "VALIDACIÓN MAESTRA",
                    "python validacion_maestra.py",
                    "Ejecuta todas las validaciones del sistema"
                )
            elif opcion == "5":
                print("\n📖 Documentación disponible:")
                print("   • README_VALIDACION.md - Guía completa del sistema")
                print("   • GUIA_VALIDACION.md - Instrucciones específicas")
                if os.path.exists("README_VALIDACION.md"):
                    print("   ✅ README_VALIDACION.md encontrado")
                else:
                    print("   ⚠️  README_VALIDACION.md no encontrado")
            elif opcion == "6":
                print("\n👋 ¡Gracias por usar el demo del sistema de validación!")
                break
            else:
                print("\n❌ Opción no válida. Seleccione 1-6.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Demo interrumpido. ¡Hasta luego!")
            break
        except Exception as e:
            print(f"\n💥 Error: {e}")

def main():
    """Función principal del demo"""
    print("Sistema de Validación Bodega SEREMI - Demo v1.0")
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists("manage.py"):
        print("⚠️  Advertencia: No se encontró manage.py")
        print("   Asegúrese de estar en el directorio sistema_bodega/")
        pausa_demo("¿Continuar de todas formas?")
    
    # Verificar archivos de validación
    archivos_validacion = [
        "configurar_validacion.py",
        "validacion_maestra.py", 
        "analisis_escalabilidad.py",
        "validador_bincard.py",
        "validador_dashboard.py"
    ]
    
    archivos_faltantes = [f for f in archivos_validacion if not os.path.exists(f)]
    
    if archivos_faltantes:
        print("❌ Archivos de validación faltantes:")
        for archivo in archivos_faltantes:
            print(f"   - {archivo}")
        print("\n💡 Asegúrese de haber ejecutado la configuración completa primero")
        return
    
    print("✅ Todos los archivos de validación encontrados")
    
    # Ejecutar menú principal
    mostrar_menu()

if __name__ == "__main__":
    main()
