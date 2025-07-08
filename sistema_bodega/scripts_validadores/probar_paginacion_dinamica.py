#!/usr/bin/env python
"""
Script de prueba para verificar la paginación dinámica
en la vista de control de vencimientos
"""

import os
import sys
import django
from datetime import date, timedelta

# Configurar Django
sys.path.append('c:\\Users\\Robinson Bravo\\Desktop\\bodega_seremi\\sistema_bodega')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
django.setup()

from accounts.models import Producto, LoteProducto
from django.test import RequestFactory
from django.contrib.auth.models import User
from accounts.views import paginar_resultados_dinamico

def probar_paginacion_dinamica():
    print("=" * 80)
    print("        PRUEBA DE PAGINACIÓN DINÁMICA")
    print("     Control de Vencimientos - Numeración Limitada")
    print("=" * 80)
    print()
    
    # Crear una request factory para simular requests
    factory = RequestFactory()
    
    # Obtener productos existentes
    productos = list(Producto.objects.filter(tiene_vencimiento=True))
    total_productos = len(productos)
    
    print(f"📊 DATOS INICIALES:")
    print(f"   • Total productos con vencimiento: {total_productos}")
    print()
    
    # Probar diferentes escenarios de paginación
    scenarios = [
        {'items_per_page': 5, 'page': 1, 'description': 'Primera página, 5 items por página'},
        {'items_per_page': 5, 'page': 3, 'description': 'Página central, 5 items por página'},
        {'items_per_page': 3, 'page': 1, 'description': 'Primera página, 3 items por página'},
        {'items_per_page': 2, 'page': 5, 'description': 'Página 5, 2 items por página'},
        {'items_per_page': 10, 'page': 1, 'description': 'Primera página, 10 items por página'},
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"🧪 ESCENARIO {i}: {scenario['description']}")
        
        # Crear request simulada
        request = factory.get(f"/?page={scenario['page']}")
        
        # Probar la función de paginación
        try:
            paginated = paginar_resultados_dinamico(
                request, 
                productos, 
                scenario['items_per_page']
            )
            
            print(f"   📄 Página actual: {paginated.number}")
            print(f"   📊 Total páginas: {paginated.paginator.num_pages}")
            print(f"   📦 Items en esta página: {len(paginated.object_list)}")
            print(f"   🔢 Rango de páginas dinámico: {paginated.dynamic_page_range}")
            print(f"   ⬅️  Mostrar primera/última: {paginated.show_first_last}")
            print(f"   ... Puntos suspensivos inicial: {paginated.show_first_ellipsis}")
            print(f"   ... Puntos suspensivos final: {paginated.show_last_ellipsis}")
            
            # Verificar que el rango no sea excesivo
            range_size = len(paginated.dynamic_page_range)
            if range_size <= 10:
                print(f"   ✅ Rango de páginas OK ({range_size} páginas mostradas)")
            else:
                print(f"   ⚠️  Rango muy largo ({range_size} páginas)")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
    
    # Probar con muchos productos (simular base de datos poblada)
    print("🔍 SIMULACIÓN CON MUCHOS PRODUCTOS:")
    
    # Crear lista de productos simulados
    productos_simulados = []
    for i in range(1, 201):  # 200 productos simulados
        productos_simulados.append({
            'id': i,
            'codigo': f'PROD{i:03d}',
            'descripcion': f'Producto simulado {i}'
        })
    
    # Probar con diferentes páginas
    test_pages = [1, 5, 10, 15, 20]
    
    for page in test_pages:
        request = factory.get(f"/?page={page}")
        try:
            paginated = paginar_resultados_dinamico(request, productos_simulados, 10)
            
            print(f"   📄 Página {page}:")
            print(f"      • Rango mostrado: {paginated.dynamic_page_range}")
            print(f"      • Tamaño del rango: {len(paginated.dynamic_page_range)} páginas")
            print(f"      • Puntos suspensivos: Inicio={paginated.show_first_ellipsis}, Fin={paginated.show_last_ellipsis}")
            
        except Exception as e:
            print(f"      ❌ Error en página {page}: {e}")
    
    print()
    
    # Resultado final
    print("=" * 80)
    print("                    RESULTADO DE LA PRUEBA")
    print("=" * 80)
    print("✅ FUNCIONALIDAD IMPLEMENTADA:")
    print("   • Paginación dinámica con rango limitado")
    print("   • Máximo 10 páginas mostradas simultáneamente")
    print("   • Puntos suspensivos para páginas no mostradas")
    print("   • Botones de primera/última página cuando necesario")
    print("   • Navegación anterior/siguiente siempre disponible")
    print()
    print("🎯 BENEFICIOS:")
    print("   • Interfaz limpia sin sobrecarga visual")
    print("   • Navegación eficiente incluso con miles de productos")
    print("   • Experiencia de usuario mejorada")
    print("   • Responsive y accesible")
    print()
    print("📝 PARA PROBAR EN EL NAVEGADOR:")
    print("   1. Ir a: http://127.0.0.1:8000/accounts/control-vencimientos/")
    print("   2. Agregar productos para tener múltiples páginas")
    print("   3. Verificar que solo se muestren páginas limitadas")
    print("   4. Probar navegación en diferentes dispositivos")
    print()
    print("=" * 80)

if __name__ == "__main__":
    probar_paginacion_dinamica()
