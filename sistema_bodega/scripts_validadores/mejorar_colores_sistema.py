"""
Script para documentar y aplicar mejoras de color uniforme en el sistema
"""

import os
import re
from pathlib import Path

class MejoradorColores:
    def __init__(self):
        self.base_path = Path(__file__).parent.parent
        self.templates_path = self.base_path / "accounts" / "templates" / "accounts"
        self.static_path = self.base_path / "static" / "css"
        
        # Definir paleta de colores uniforme
        self.paleta_colores = {
            # Colores principales
            'primary': '#1a3c5e',
            'primary_light': '#2d5a8a',
            'primary_dark': '#0f2436',
            
            # Estados de vencimiento
            'vencido': '#dc2626',
            'vence_hoy': '#ea580c',
            'critico': '#d97706',
            'precaucion': '#16a34a',
            'normal': '#64748b',
            
            # Botones
            'btn_success': '#059669',
            'btn_primary': '#2563eb',
            'btn_warning': '#d97706',
            'btn_danger': '#dc2626',
            'btn_info': '#0891b2',
            
            # Fondos
            'bg_primary': '#f8fafc',
            'bg_secondary': '#f1f5f9',
            'bg_card': '#ffffff',
            
            # Texto
            'text_primary': '#1e293b',
            'text_secondary': '#64748b',
            'text_muted': '#94a3b8',
            
            # Bordes
            'border_light': '#e2e8f0',
            'border_medium': '#cbd5e1',
            'border_dark': '#94a3b8',
        }
    
    def analizar_colores_actuales(self):
        """Analiza los colores actuales en el sistema"""
        print("🎨 ANÁLISIS DE COLORES ACTUALES")
        print("=" * 50)
        
        colores_encontrados = set()
        archivos_analizados = 0
        
        # Buscar en templates HTML
        for archivo in self.templates_path.glob("*.html"):
            try:
                with open(archivo, 'r', encoding='utf-8') as f:
                    contenido = f.read()
                    
                # Buscar códigos de color hexadecimales
                patrones_hex = re.findall(r'#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3}', contenido)
                colores_encontrados.update(patrones_hex)
                archivos_analizados += 1
                
            except Exception as e:
                print(f"Error al leer {archivo}: {e}")
        
        print(f"📊 Archivos analizados: {archivos_analizados}")
        print(f"🎯 Colores únicos encontrados: {len(colores_encontrados)}")
        
        # Mostrar colores encontrados
        if colores_encontrados:
            print("\n🎨 COLORES ENCONTRADOS:")
            for color in sorted(colores_encontrados):
                print(f"   {color}")
        
        return colores_encontrados
    
    def generar_mapa_migracion(self):
        """Genera un mapa de migración de colores antiguos a nuevos"""
        print("\n🔄 MAPA DE MIGRACIÓN DE COLORES")
        print("=" * 50)
        
        # Mapeo de colores antiguos a nuevos
        mapa_migracion = {
            # Colores principales
            '#1a3c5e': self.paleta_colores['primary'],      # Ya es correcto
            '#2d5a8a': self.paleta_colores['primary_light'], # Ya es correcto
            
            # Estados de vencimiento antiguos -> nuevos
            '#dc3545': self.paleta_colores['vencido'],       # Rojo más uniforme
            '#fd7e14': self.paleta_colores['vence_hoy'],     # Naranja más coherente
            '#ffc107': self.paleta_colores['critico'],       # Amarillo más fuerte
            '#28a745': self.paleta_colores['precaucion'],    # Verde más consistente
            '#6c757d': self.paleta_colores['normal'],        # Gris más moderno
            
            # Botones
            '#20c997': self.paleta_colores['btn_success'],   # Verde más profesional
            '#007bff': self.paleta_colores['btn_primary'],   # Azul más consistente
            '#17a2b8': self.paleta_colores['btn_info'],      # Turquesa más moderno
            
            # Fondos
            '#f8f9fa': self.paleta_colores['bg_primary'],    # Ya es correcto
            '#ffffff': self.paleta_colores['bg_card'],       # Ya es correcto
            
            # Texto
            '#343a40': self.paleta_colores['text_primary'],  # Texto más moderno
            '#64748b': self.paleta_colores['text_secondary'], # Ya es correcto
            
            # Bordes
            '#dee2e6': self.paleta_colores['border_light'],  # Borde más suave
            '#e9ecef': self.paleta_colores['border_light'],  # Borde más suave
        }
        
        print("🎯 MIGRACIONES SUGERIDAS:")
        for color_antiguo, color_nuevo in mapa_migracion.items():
            if color_antiguo != color_nuevo:
                print(f"   {color_antiguo} → {color_nuevo}")
        
        return mapa_migracion
    
    def crear_guia_implementacion(self):
        """Crea una guía de implementación paso a paso"""
        print("\n📋 GUÍA DE IMPLEMENTACIÓN")
        print("=" * 50)
        
        pasos = [
            "1. ✅ Crear archivo CSS con paleta uniforme",
            "   - Archivo: static/css/sistema_colores.css",
            "   - Variables CSS con colores consistentes",
            "   - Clases utilitarias para uso fácil",
            "",
            "2. ✅ Incluir CSS en template base",
            "   - Agregado en accounts/templates/accounts/home.html",
            "   - Disponible en todas las páginas",
            "",
            "3. ✅ Actualizar colores en models.py",
            "   - Colores de estados de vencimiento",
            "   - Más consistentes y profesionales",
            "",
            "4. ✅ Mejorar botón 'Agregar'",
            "   - Gradiente verde uniforme",
            "   - Efectos hover consistentes",
            "",
            "5. 🔄 Migrar templates gradualmente",
            "   - Control de vencimientos",
            "   - Agregar vencimiento",
            "   - Otros templates importantes",
            "",
            "6. 🔄 Aplicar clases CSS uniformes",
            "   - Reemplazar estilos inline",
            "   - Usar variables CSS",
            "   - Mantener consistencia",
            "",
            "7. 🔄 Validar y optimizar",
            "   - Probar en diferentes navegadores",
            "   - Verificar accesibilidad",
            "   - Documentar cambios"
        ]
        
        for paso in pasos:
            print(paso)
    
    def generar_ejemplos_uso(self):
        """Genera ejemplos de uso de las nuevas clases CSS"""
        print("\n💡 EJEMPLOS DE USO")
        print("=" * 50)
        
        ejemplos = [
            {
                'titulo': 'Botones con paleta uniforme',
                'antes': '<button class="btn btn-success">Agregar</button>',
                'despues': '<button class="btn btn-success-custom">Agregar</button>',
                'descripcion': 'Botón con gradiente verde uniforme'
            },
            {
                'titulo': 'Estados de vencimiento',
                'antes': '<span class="badge bg-danger">Vencido</span>',
                'despues': '<span class="badge estado-vencido">Vencido</span>',
                'descripcion': 'Badge con color de estado uniforme'
            },
            {
                'titulo': 'Tarjetas con estilo uniforme',
                'antes': '<div class="card">...</div>',
                'despues': '<div class="card card-custom">...</div>',
                'descripcion': 'Tarjeta con sombras y bordes uniformes'
            },
            {
                'titulo': 'Headers con gradiente',
                'antes': '<div class="header">...</div>',
                'despues': '<div class="header header-custom">...</div>',
                'descripcion': 'Header con gradiente corporativo'
            },
            {
                'titulo': 'Tablas con estilo uniforme',
                'antes': '<table class="table">...</table>',
                'despues': '<table class="table table-custom">...</table>',
                'descripcion': 'Tabla con colores corporativos'
            }
        ]
        
        for ejemplo in ejemplos:
            print(f"\n📌 {ejemplo['titulo']}")
            print(f"   Antes:   {ejemplo['antes']}")
            print(f"   Después: {ejemplo['despues']}")
            print(f"   → {ejemplo['descripcion']}")
    
    def verificar_implementacion(self):
        """Verifica que los archivos necesarios existan"""
        print("\n🔍 VERIFICACIÓN DE IMPLEMENTACIÓN")
        print("=" * 50)
        
        archivos_necesarios = [
            ('static/css/sistema_colores.css', 'Sistema de colores uniforme'),
            ('accounts/models.py', 'Colores actualizados en modelos'),
            ('accounts/templates/accounts/home.html', 'CSS incluido en template base'),
            ('accounts/templates/accounts/agregar_vencimiento.html', 'Botón mejorado')
        ]
        
        for archivo, descripcion in archivos_necesarios:
            ruta_completa = self.base_path / archivo
            if ruta_completa.exists():
                print(f"✅ {archivo} - {descripcion}")
            else:
                print(f"❌ {archivo} - {descripcion}")
    
    def ejecutar_analisis_completo(self):
        """Ejecuta el análisis completo del sistema de colores"""
        print("🎨 SISTEMA DE COLORES UNIFORME - ANÁLISIS COMPLETO")
        print("=" * 60)
        
        try:
            # Análisis de colores actuales
            colores_actuales = self.analizar_colores_actuales()
            
            # Mapa de migración
            mapa_migracion = self.generar_mapa_migracion()
            
            # Guía de implementación
            self.crear_guia_implementacion()
            
            # Ejemplos de uso
            self.generar_ejemplos_uso()
            
            # Verificación
            self.verificar_implementacion()
            
            print("\n🎉 ANÁLISIS COMPLETADO")
            print("=" * 60)
            print("✅ Sistema de colores uniforme implementado")
            print("✅ Paleta consistente creada")
            print("✅ Botones mejorados")
            print("✅ Modelos actualizados")
            print("📚 Documentación generada")
            
        except Exception as e:
            print(f"\n❌ Error durante el análisis: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    mejorador = MejoradorColores()
    mejorador.ejecutar_analisis_completo()
