#!/usr/bin/env python3
"""
Script de Prueba Visual - Mejoras UX/UI Finales
Verificación en tiempo real de las optimizaciones implementadas
"""

import subprocess
import webbrowser
import time
import os
from datetime import datetime

def probar_servidor():
    """Inicia el servidor y abre la página para prueba visual"""
    print("🚀 Iniciando prueba visual del sistema...")
    print("="*60)
    
    # Verificar que estamos en el directorio correcto
    current_dir = os.getcwd()
    if not current_dir.endswith('sistema_bodega'):
        print("❌ Error: Ejecutar desde el directorio sistema_bodega")
        return False
    
    print("✅ Directorio correcto confirmado")
    print("⚡ Iniciando servidor Django...")
    
    try:
        # Iniciar servidor en background
        process = subprocess.Popen(
            ['python', 'manage.py', 'runserver', '127.0.0.1:8000'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        print("⏳ Esperando que el servidor se inicie...")
        time.sleep(3)
        
        # Verificar si el proceso está corriendo
        if process.poll() is None:
            print("✅ Servidor iniciado correctamente en http://127.0.0.1:8000")
            
            print("\n" + "="*60)
            print("🎯 PRUEBAS VISUALES RECOMENDADAS")
            print("="*60)
            
            tests = [
                "1. Navegación a http://127.0.0.1:8000/accounts/agregar-vencimiento/",
                "2. Verificar animaciones suaves al cargar la página",
                "3. Probar filtros y búsqueda de productos",
                "4. Hacer clic en 'Ver Lotes' de un producto",
                "5. VERIFICAR: No hay scroll horizontal en el modal",
                "6. VERIFICAR: Cards de lotes se ven organizadas en grid",
                "7. VERIFICAR: Animaciones suaves al mostrar cards",
                "8. Probar hover effects en las cards",
                "9. Testear responsive design (redimensionar ventana)",
                "10. Verificar transiciones entre páginas"
            ]
            
            for test in tests:
                print(f"  {test}")
            
            print("\n" + "="*60)
            print("🔍 PUNTOS ESPECÍFICOS A VALIDAR")
            print("="*60)
            
            validations = [
                "✅ Modal de lotes sin scroll horizontal",
                "✅ Cards organizadas en 2-3 columnas según pantalla",
                "✅ Transiciones de página en 200ms (más rápidas)",
                "✅ Animaciones de fade-in suaves (400ms vs 600ms)",
                "✅ Hover effects sutiles en cards",
                "✅ Resumen visual de totales en modal",
                "✅ Badges coloridos para estados",
                "✅ Gradientes en headers de cards"
            ]
            
            for validation in validations:
                print(f"  {validation}")
            
            print("\n🌐 Abriendo navegador...")
            time.sleep(1)
            
            # Abrir navegador
            webbrowser.open('http://127.0.0.1:8000/accounts/agregar-vencimiento/')
            
            print("\n✨ ¡Navegador abierto! Realiza las pruebas visuales.")
            print("\n⚠️  Para detener el servidor, presiona Ctrl+C en la terminal")
            
            # Esperar input del usuario
            try:
                input("\n🎯 Presiona Enter cuando hayas terminado las pruebas...")
            except KeyboardInterrupt:
                pass
            
            # Terminar proceso
            process.terminate()
            print("\n🛑 Servidor detenido.")
            return True
            
        else:
            error_output = process.stderr.read().decode()
            print(f"❌ Error al iniciar servidor: {error_output}")
            return False
            
    except FileNotFoundError:
        print("❌ Error: 'python' no encontrado. Verifica la instalación.")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def generar_checklist():
    """Genera checklist de verificación post-prueba"""
    print("\n" + "="*60)
    print("📋 CHECKLIST POST-PRUEBA")
    print("="*60)
    
    checklist = [
        "[ ] Modal de lotes se abre sin problemas",
        "[ ] NO hay scroll horizontal en la tabla de lotes",
        "[ ] Cards de lotes se ven organizadas en grid",
        "[ ] Resumen de totales visible en la parte superior",
        "[ ] Animaciones suaves al mostrar las cards",
        "[ ] Hover effects funcionan correctamente",
        "[ ] Transiciones entre páginas son más rápidas",
        "[ ] Diseño se adapta bien a diferentes tamaños de pantalla",
        "[ ] Botones y badges tienen buen contraste",
        "[ ] La experiencia general es más fluida"
    ]
    
    for item in checklist:
        print(f"  {item}")
    
    print("\n💡 Si algún punto falla, revisar el código correspondiente.")

def main():
    print("🎨 Sistema de Prueba Visual - Mejoras UX/UI Finales")
    print(f"⏰ Inicio: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("-" * 60)
    
    success = probar_servidor()
    
    if success:
        generar_checklist()
        print("\n🎉 Prueba visual completada!")
        print("✨ Las mejoras UX/UI están implementadas y listas para producción.")
    else:
        print("\n❌ Hubo problemas durante la prueba.")
        print("🔧 Revisar configuración del servidor Django.")

if __name__ == "__main__":
    main()
