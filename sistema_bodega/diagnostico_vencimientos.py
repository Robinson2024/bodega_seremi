#!/usr/bin/env python
"""
Script para diagnosticar el problema de sincronización entre el dashboard y control de vencimientos.
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
django.setup()

from accounts.models import Producto, LoteProducto
from datetime import date, timedelta

def diagnosticar_productos_vencimiento():
    """Diagnostica los productos con vencimiento y sus lotes."""
    print("🔍 DIAGNÓSTICO DE PRODUCTOS CON VENCIMIENTO")
    print("=" * 50)
    
    hoy = date.today()
    
    # Obtener todos los productos con vencimiento
    productos_con_vencimiento = Producto.objects.filter(tiene_vencimiento=True)
    print(f"📊 Total productos con tiene_vencimiento=True: {productos_con_vencimiento.count()}")
    
    productos_con_stock = productos_con_vencimiento.filter(stock__gt=0)
    print(f"📊 Productos con vencimiento Y stock > 0: {productos_con_stock.count()}")
    
    print("\n📋 DETALLE DE PRODUCTOS CON VENCIMIENTO:")
    print("-" * 50)
    
    for i, producto in enumerate(productos_con_vencimiento, 1):
        print(f"\n{i}. {producto.descripcion}")
        print(f"   • Código: {producto.codigo_barra}")
        print(f"   • Stock: {producto.stock}")
        print(f"   • Categoría: {producto.categoria.nombre if producto.categoria else 'Sin categoría'}")
        print(f"   • Fecha vencimiento (producto): {producto.fecha_vencimiento}")
        print(f"   • Tiene vencimiento: {producto.tiene_vencimiento}")
        
        # Información de lotes
        lotes = producto.lotes.all().order_by('fecha_vencimiento')
        print(f"   • Total lotes: {lotes.count()}")
        
        if lotes.exists():
            print(f"   • Lotes detalle:")
            for lote in lotes:
                dias_restantes = (lote.fecha_vencimiento - hoy).days
                estado = lote.get_estado_vencimiento()
                print(f"     - Lote #{lote.numero_lote}: {lote.stock} unidades, vence {lote.fecha_vencimiento} ({dias_restantes} días) [{estado}]")
        else:
            print(f"   • ⚠️  Sin lotes creados")
        
        # Usar métodos del modelo
        try:
            estado_completo = producto.get_estado_vencimiento_completo()
            proximo_vencimiento = producto.get_proximo_vencimiento()
            lotes_detalle = producto.get_lotes_detalle()
            
            print(f"   • Estado completo: {estado_completo}")
            print(f"   • Próximo vencimiento: {proximo_vencimiento}")
            print(f"   • Lotes con stock: {len(lotes_detalle)}")
            
        except Exception as e:
            print(f"   • ❌ Error al obtener métodos: {e}")

def verificar_vista_control_vencimientos():
    """Simula la lógica de la vista de control de vencimientos."""
    print("\n\n🔍 SIMULACIÓN DE VISTA CONTROL_VENCIMIENTOS")
    print("=" * 50)
    
    from datetime import date
    hoy = date.today()
    
    # Replicar la lógica exacta de la vista
    productos_base = Producto.objects.filter(
        tiene_vencimiento=True,
        stock__gt=0
    ).select_related('categoria').prefetch_related('lotes')
    
    print(f"📊 Productos encontrados: {productos_base.count()}")
    
    productos_info = []
    for producto in productos_base:
        try:
            estado_vencimiento = producto.get_estado_vencimiento_completo()
            proximo_vencimiento = producto.get_proximo_vencimiento()
            lotes_detalle = producto.get_lotes_detalle()
            
            dias_restantes = None
            if proximo_vencimiento:
                dias_restantes = (proximo_vencimiento - hoy).days
            
            productos_info.append({
                'producto': producto,
                'estado_vencimiento': estado_vencimiento,
                'proximo_vencimiento': proximo_vencimiento,
                'dias_restantes': dias_restantes,
                'lotes_detalle': lotes_detalle,
                'total_lotes': len(lotes_detalle)
            })
            
            print(f"\n✅ {producto.descripcion}:")
            print(f"   • Estado: {estado_vencimiento}")
            print(f"   • Próximo vencimiento: {proximo_vencimiento}")
            print(f"   • Días restantes: {dias_restantes}")
            print(f"   • Total lotes: {len(lotes_detalle)}")
            
        except Exception as e:
            print(f"\n❌ Error procesando {producto.descripcion}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n📊 Total productos_info creados: {len(productos_info)}")
    
    # Calcular estadísticas
    estadisticas = {'vencidos': 0, 'criticos': 0, 'precaucion': 0, 'normal': 0}
    for producto in productos_base:
        try:
            estado = producto.get_estado_vencimiento_completo()
            if estado == 'Vencido':
                estadisticas['vencidos'] += 1
            elif estado in ['Vence Hoy', 'Crítico']:
                estadisticas['criticos'] += 1
            elif estado == 'Precaución':
                estadisticas['precaucion'] += 1
            else:
                estadisticas['normal'] += 1
        except Exception as e:
            print(f"❌ Error calculando estadísticas para {producto.descripcion}: {e}")
    
    print(f"\n📊 ESTADÍSTICAS CALCULADAS:")
    print(f"   • Vencidos: {estadisticas['vencidos']}")
    print(f"   • Críticos: {estadisticas['criticos']}")
    print(f"   • Precaución: {estadisticas['precaucion']}")
    print(f"   • Normal: {estadisticas['normal']}")

if __name__ == "__main__":
    try:
        diagnosticar_productos_vencimiento()
        verificar_vista_control_vencimientos()
    except Exception as e:
        print(f"\n❌ Error en diagnóstico: {e}")
        import traceback
        traceback.print_exc()
