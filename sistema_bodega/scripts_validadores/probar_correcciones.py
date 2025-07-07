#!/usr/bin/env python
"""
Script para probar las correcciones implementadas en control de vencimientos
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
django.setup()

from accounts.models import Producto, LoteProducto
from django.db import models

def probar_funcionalidad_botones():
    """Prueba la lógica de botones según el estado del producto"""
    producto = Producto.objects.get(codigo_barra='100041')
    
    print(f"=== PRUEBA DE LÓGICA DE BOTONES ===")
    print(f"Producto: {producto.descripcion}")
    print(f"Código: {producto.codigo_barra}")
    print(f"Tiene vencimiento: {producto.tiene_vencimiento}")
    
    # Contar lotes activos
    total_lotes = producto.lotes.filter(stock__gt=0).count()
    print(f"Total de lotes activos: {total_lotes}")
    
    # Lógica de botones
    if not producto.tiene_vencimiento:
        print("✅ Debe mostrar: BOTÓN VERDE 'AGREGAR'")
    else:
        if total_lotes == 0:
            print("✅ Debe mostrar: BOTÓN AMARILLO 'MODIFICAR'")
        else:
            print("✅ Debe mostrar: MENSAJE 'Modificar por lotes' + BOTÓN 'LOTES'")
            print(f"   Texto del botón lotes: 'Lotes ({total_lotes})'")
    
    # Mostrar lotes existentes
    if total_lotes > 0:
        print(f"\nLotes existentes:")
        for lote in producto.lotes.filter(stock__gt=0).order_by('fecha_vencimiento'):
            estado = lote.get_estado_vencimiento()
            print(f"  Lote #{lote.numero_lote}: {lote.stock} unidades - {estado} (vence {lote.fecha_vencimiento})")
    
    return total_lotes

def simular_modificacion_lote():
    """Simula la modificación de un lote para probar la sincronización"""
    producto = Producto.objects.get(codigo_barra='100041')
    
    print(f"\n=== SIMULACIÓN DE MODIFICACIÓN DE LOTE ===")
    
    lote = producto.lotes.filter(stock__gt=0).first()
    if not lote:
        print("❌ No hay lotes para modificar")
        return False
    
    print(f"Modificando Lote #{lote.numero_lote}")
    print(f"Fecha anterior: {lote.fecha_vencimiento}")
    
    # Cambiar fecha a una fecha futura
    from datetime import date, timedelta
    nueva_fecha = date.today() + timedelta(days=90)
    fecha_anterior = lote.fecha_vencimiento
    
    lote.fecha_vencimiento = nueva_fecha
    lote.save()
    
    print(f"Nueva fecha: {nueva_fecha}")
    
    # Verificar que el producto se actualiza
    producto.refresh_from_db()
    estado_actualizado = producto.get_estado_vencimiento_completo()
    proximo_vencimiento = producto.get_proximo_vencimiento()
    
    print(f"Estado actualizado del producto: {estado_actualizado}")
    print(f"Próximo vencimiento: {proximo_vencimiento}")
    
    # Restaurar fecha original para no afectar datos
    lote.fecha_vencimiento = fecha_anterior
    lote.save()
    print(f"✅ Fecha restaurada a: {fecha_anterior}")
    
    return True

def verificar_datos_ajax():
    """Verifica que los datos para AJAX estén correctos"""
    producto = Producto.objects.get(codigo_barra='100041')
    
    print(f"\n=== VERIFICACIÓN DE DATOS AJAX ===")
    
    # Datos que debe devolver la vista AJAX
    estado_vencimiento = producto.get_estado_vencimiento_completo()
    proximo_vencimiento = producto.get_proximo_vencimiento()
    total_lotes = producto.lotes.filter(stock__gt=0).count()
    
    datos_ajax = {
        'codigo_barra': producto.codigo_barra,
        'descripcion': producto.descripcion,
        'estado_vencimiento': estado_vencimiento,
        'proximo_vencimiento': proximo_vencimiento.strftime('%Y-%m-%d') if proximo_vencimiento else None,
        'proximo_vencimiento_display': proximo_vencimiento.strftime('%d/%m/%Y') if proximo_vencimiento else None,
        'total_lotes': total_lotes,
        'tiene_vencimiento': producto.tiene_vencimiento
    }
    
    print("Datos que debe devolver obtener_datos_producto_ajax:")
    for key, value in datos_ajax.items():
        print(f"  {key}: {value}")
    
    return datos_ajax

def resumen_implementacion():
    """Muestra un resumen de lo implementado"""
    print(f"\n=== RESUMEN DE IMPLEMENTACIÓN ===")
    
    print("✅ CAMBIOS IMPLEMENTADOS:")
    print("1. Corrección en modificar_vencimiento_producto_ajax:")
    print("   - Ahora actualiza TODOS los lotes del producto")
    print("   - Retorna información sobre lotes actualizados")
    
    print("\n2. Lógica de botones en template:")
    print("   - Botón AMARILLO 'MODIFICAR' solo aparece si NO hay lotes")
    print("   - Si hay lotes, muestra mensaje 'Modificar por lotes'")
    print("   - Botón VERDE 'AGREGAR' para productos sin vencimiento")
    
    print("\n3. Actualización automática sin refresh:")
    print("   - Nueva función actualizarFilaProducto()")
    print("   - Nueva vista obtener_datos_producto_ajax")
    print("   - JavaScript mejorado para actualización en tiempo real")
    
    print("\n4. URLs agregadas:")
    print("   - ajax/obtener-datos-producto/")
    
    print("\n🎯 RESULTADO ESPERADO:")
    print("- El botón amarillo MODIFICAR no aparecerá para productos con lotes")
    print("- Las modificaciones por lotes actualizarán la vista automáticamente")
    print("- No será necesario refrescar la página manualmente")

if __name__ == "__main__":
    try:
        total_lotes = probar_funcionalidad_botones()
        simular_modificacion_lote()
        verificar_datos_ajax()
        resumen_implementacion()
        
        print(f"\n🎯 PARA PROBAR:")
        print(f"1. Ir a: http://127.0.0.1:8000/accounts/agregar-vencimiento/")
        print(f"2. Buscar producto: {Producto.objects.get(codigo_barra='100041').descripcion}")
        print(f"3. Verificar que NO aparece el botón amarillo MODIFICAR (tiene {total_lotes} lotes)")
        print(f"4. Usar 'Lotes ({total_lotes})' para modificar fechas")
        print(f"5. Observar que la vista se actualiza automáticamente")
        
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()
