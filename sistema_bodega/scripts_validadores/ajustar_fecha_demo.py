#!/usr/bin/env python
"""
Script para ajustar la fecha de vencimiento del producto de prueba
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
django.setup()

from accounts.models import Producto, LoteProducto
from datetime import date, timedelta

def ajustar_fecha_vencimiento():
    """Ajusta la fecha de vencimiento para que esté más cerca y se vea el cambio de estado"""
    producto = Producto.objects.get(codigo_barra='100041')
    
    print(f"=== AJUSTANDO FECHA DE VENCIMIENTO PARA DEMOSTRACIÓN ===")
    print(f"Producto: {producto.descripcion}")
    
    # Obtener el lote actual
    lote = producto.lotes.filter(stock__gt=0).first()
    if lote:
        fecha_actual = lote.fecha_vencimiento
        print(f"Fecha actual del lote #{lote.numero_lote}: {fecha_actual}")
        print(f"Estado actual: {lote.get_estado_vencimiento()}")
        
        # Cambiar a una fecha que esté en "Precaución" (próximos 30 días)
        nueva_fecha = date.today() + timedelta(days=25)
        
        # Actualizar lote
        lote.fecha_vencimiento = nueva_fecha
        lote.save()
        
        # Actualizar producto
        producto.fecha_vencimiento = nueva_fecha
        producto.save()
        
        print(f"Nueva fecha: {nueva_fecha}")
        print(f"Nuevo estado: {lote.get_estado_vencimiento()}")
        print(f"Días para vencer: {lote.get_dias_para_vencer()}")
        
        print(f"\n✅ Ahora el producto mostrará estado 'Precaución' en la interfaz")
        print(f"   Esto permitirá ver mejor los cambios de estado al modificar fechas")
    else:
        print("❌ No se encontró lote activo")

if __name__ == "__main__":
    ajustar_fecha_vencimiento()
