#!/usr/bin/env python
"""
Script para verificar errores de sintaxis en templates Django
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
django.setup()

from django.template import Template, Context, TemplateSyntaxError
from django.template.loader import get_template

def verificar_templates():
    """Verifica errores de sintaxis en templates críticos"""
    print("🔍 VERIFICACIÓN DE TEMPLATES DJANGO")
    print("=" * 50)
    
    templates_criticos = [
        'accounts/agregar_stock_detalle.html',
        'accounts/detalle_lotes_producto.html',
        'accounts/control_vencimientos.html',
    ]
    
    print("\n📋 Verificando templates críticos...")
    
    for template_name in templates_criticos:
        try:
            template = get_template(template_name)
            print(f"✅ {template_name} - Sintaxis correcta")
        except TemplateSyntaxError as e:
            print(f"❌ {template_name} - Error de sintaxis: {e}")
        except Exception as e:
            print(f"⚠️  {template_name} - Error: {e}")
    
    print("\n🎯 VERIFICACIÓN DE FILTROS PROBLEMÁTICOS...")
    
    # Patrones problemáticos comunes
    patrones_problematicos = [
        r'timeuntil).split|first',
        r'|split|first',
        r'proximo_vencimiento||timeuntil',
        r').split',
    ]
    
    import re
    templates_dir = 'accounts/templates/accounts/'
    
    if os.path.exists(templates_dir):
        for filename in os.listdir(templates_dir):
            if filename.endswith('.html'):
                filepath = os.path.join(templates_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    for pattern in patrones_problematicos:
                        if re.search(pattern, content):
                            print(f"⚠️  {filename} - Contiene patrón problemático: {pattern}")
                        else:
                            continue
                    else:
                        print(f"✅ {filename} - Sin patrones problemáticos")
                except Exception as e:
                    print(f"❌ Error leyendo {filename}: {e}")
    
    print("\n" + "=" * 50)
    print("✅ VERIFICACIÓN COMPLETADA")
    print("=" * 50)

if __name__ == "__main__":
    try:
        verificar_templates()
    except Exception as e:
        print(f"❌ Error durante verificación: {e}")
        import traceback
        traceback.print_exc()
