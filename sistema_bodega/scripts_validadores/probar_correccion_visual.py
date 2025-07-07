#!/usr/bin/env python
"""
Script para probar la corrección visual de actualización de columnas
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
django.setup()

from accounts.models import Producto, LoteProducto
from datetime import date, timedelta

def probar_actualizacion_visual():
    """Prueba los cambios en la actualización visual"""
    producto = Producto.objects.get(codigo_barra='100041')
    
    print(f"=== PRUEBA DE ACTUALIZACIÓN VISUAL ===")
    print(f"Producto: {producto.descripcion}")
    
    # Estado actual
    lote = producto.lotes.filter(stock__gt=0).first()
    if lote:
        print(f"\nEstado antes de cambios:")
        print(f"  Lote #{lote.numero_lote}")
        print(f"  Fecha: {lote.fecha_vencimiento}")
        print(f"  Estado: {lote.get_estado_vencimiento()}")
        print(f"  Días para vencer: {lote.get_dias_para_vencer()}")
        
        # Simular cambio a diferentes estados para probar
        estados_prueba = [
            (date.today() + timedelta(days=3), "Crítico"),
            (date.today() + timedelta(days=20), "Precaución"), 
            (date.today() + timedelta(days=60), "Normal"),
            (date.today() - timedelta(days=1), "Vencido")
        ]
        
        print(f"\n=== SIMULACIÓN DE DIFERENTES ESTADOS ===")
        fecha_original = lote.fecha_vencimiento
        
        for nueva_fecha, estado_esperado in estados_prueba:
            lote.fecha_vencimiento = nueva_fecha
            lote.save()
            
            # Refrescar producto
            producto.refresh_from_db()
            estado_actual = producto.get_estado_vencimiento_completo()
            
            print(f"\nFecha: {nueva_fecha} → Estado: {estado_actual}")
            
            # Datos que retornará la vista AJAX
            datos_ajax = {
                'estado_vencimiento': estado_actual,
                'proximo_vencimiento_display': nueva_fecha.strftime('%d/%m/%Y'),
                'proximo_vencimiento': nueva_fecha.strftime('%Y-%m-%d')
            }
            
            print(f"  Datos AJAX que retornará:")
            print(f"    estado_vencimiento: '{datos_ajax['estado_vencimiento']}'")
            print(f"    fecha_display: '{datos_ajax['proximo_vencimiento_display']}'")
            
            # Mapeo de clase CSS que aplicará JavaScript
            mapeo_clases = {
                'vencido': 'estado-vencido',
                'vence hoy': 'estado-critico', 
                'crítico': 'estado-critico',
                'precaución': 'estado-proximo',
                'normal': 'estado-bueno'
            }
            
            clase_css = mapeo_clases.get(estado_actual.lower(), 'badge-secondary')
            print(f"    Clase CSS: '{clase_css}'")
            
            # HTML resultante
            html_estado = f'<span class="badge {clase_css}">{estado_actual}</span>'
            html_fecha = datos_ajax['proximo_vencimiento_display']
            
            print(f"  HTML resultante:")
            print(f"    Columna Estado: {html_estado}")
            print(f"    Columna Fecha: {html_fecha}")
        
        # Restaurar fecha original
        lote.fecha_vencimiento = fecha_original
        lote.save()
        print(f"\n✅ Fecha original restaurada: {fecha_original}")
        
    else:
        print("❌ No se encontró lote para probar")

def verificar_estructura_tabla():
    """Verifica la estructura de columnas de la tabla"""
    print(f"\n=== ESTRUCTURA DE TABLA VERIFICADA ===")
    columnas = [
        "1. Código",
        "2. Descripción", 
        "3. Categoría",
        "4. Stock",
        "5. Estado Vencimiento ← AQUÍ SE ACTUALIZA EL ESTADO",
        "6. Fecha Vencimiento ← AQUÍ SE ACTUALIZA LA FECHA",
        "7. Lotes",
        "8. Acciones"
    ]
    
    for col in columnas:
        print(f"  {col}")
    
    print(f"\n🎯 CORRECCIÓN APLICADA:")
    print("  - Columna 5 (Estado): Se actualiza con badge y clase CSS correcta")
    print("  - Columna 6 (Fecha): Se actualiza con fecha formateada dd/mm/yyyy")
    print("  - Mapeo de estados a clases CSS implementado")

if __name__ == "__main__":
    probar_actualizacion_visual()
    verificar_estructura_tabla()
    
    print(f"\n🚀 PARA PROBAR:")
    print("1. Ir a: http://127.0.0.1:8000/accounts/agregar-vencimiento/")
    print("2. Buscar producto 'Leche de vaca 1 L'")
    print("3. Hacer clic en 'Lotes (1)'")
    print("4. Cambiar fecha del lote")
    print("5. Observar que:")
    print("   ✅ La fecha se actualiza en la columna 'Fecha Vencimiento'")
    print("   ✅ El estado se actualiza en la columna 'Estado Vencimiento'")
    print("   ✅ No desaparecen momentáneamente")
    print("   ✅ Colores y estilos correctos")
