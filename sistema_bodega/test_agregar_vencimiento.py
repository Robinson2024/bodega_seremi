#!/usr/bin/env python
"""
Script de prueba para verificar la corrección del error de agregar vencimiento.
Ejecutar desde el directorio sistema_bodega con: python test_agregar_vencimiento.py
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
django.setup()

from accounts.models import Producto, LoteProducto
from datetime import date, timedelta

def test_agregar_vencimiento():
    """Prueba la funcionalidad de agregar vencimiento a un producto."""
    
    print("🧪 INICIANDO PRUEBA: Agregar vencimiento a producto sin vencimiento")
    print("=" * 60)
    
    # 1. Crear un producto de prueba sin vencimiento
    try:
        # Buscar o crear un producto de prueba
        producto, created = Producto.objects.get_or_create(
            codigo_barra='999999',
            defaults={
                'descripcion': 'Producto de Prueba - Agregar Vencimiento',
                'stock': 50,
                'tiene_vencimiento': False,
                'fecha_vencimiento': None
            }
        )
        
        if not created:
            # Si ya existe, asegurar que no tiene vencimiento para la prueba
            producto.tiene_vencimiento = False
            producto.fecha_vencimiento = None
            producto.stock = 50
            producto.save()
            # Eliminar lotes existentes para la prueba
            producto.lotes.all().delete()
        
        print(f"✅ Producto de prueba creado/actualizado:")
        print(f"   - Código: {producto.codigo_barra}")
        print(f"   - Descripción: {producto.descripcion}")
        print(f"   - Stock inicial: {producto.stock}")
        print(f"   - Tiene vencimiento: {producto.tiene_vencimiento}")
        print(f"   - Lotes existentes: {producto.lotes.count()}")
        
    except Exception as e:
        print(f"❌ Error al crear producto de prueba: {e}")
        return
    
    # 2. Simular el proceso de agregar vencimiento
    try:
        print(f"\n🔄 SIMULANDO: Agregar vencimiento al producto...")
        
        # Fecha de vencimiento: 3 meses en el futuro
        fecha_vencimiento = date.today() + timedelta(days=90)
        print(f"   - Fecha de vencimiento a asignar: {fecha_vencimiento}")
        
        # Activar vencimiento en el producto
        producto.tiene_vencimiento = True
        producto.fecha_vencimiento = fecha_vencimiento
        producto.save()
        
        print(f"✅ Vencimiento activado en el producto")
        
        # Si el producto tiene stock, crear un lote inicial (lógica corregida)
        if producto.stock > 0:
            stock_inicial = producto.stock  # Guardar el stock actual
            print(f"   - Stock inicial a transferir al lote: {stock_inicial}")
            
            lote = LoteProducto.objects.create(
                producto=producto,
                numero_lote=producto.get_proximo_numero_lote(),
                fecha_vencimiento=fecha_vencimiento,
                stock=stock_inicial
            )
            
            print(f"✅ Lote creado:")
            print(f"   - Número de lote: {lote.numero_lote}")
            print(f"   - Stock del lote: {lote.stock}")
            print(f"   - Fecha de vencimiento: {lote.fecha_vencimiento}")
            
            # Sincronizar stock para asegurar consistencia
            resultado_sync = producto.sincronizar_stock_con_lotes()
            print(f"✅ Sincronización ejecutada: {resultado_sync}")
            
            # Recargar producto desde BD
            producto.refresh_from_db()
            
        print(f"\n📊 ESTADO FINAL DEL PRODUCTO:")
        print(f"   - Stock del producto: {producto.stock}")
        print(f"   - Tiene vencimiento: {producto.tiene_vencimiento}")
        print(f"   - Fecha de vencimiento: {producto.fecha_vencimiento}")
        print(f"   - Total de lotes: {producto.lotes.count()}")
        
        # Verificar lotes
        print(f"\n📋 LOTES DEL PRODUCTO:")
        for lote in producto.lotes.all():
            print(f"   - Lote #{lote.numero_lote}: {lote.stock} unidades, vence {lote.fecha_vencimiento}")
        
        # Verificar consistencia
        stock_en_lotes = sum(lote.stock for lote in producto.lotes.all())
        print(f"\n🔍 VERIFICACIÓN DE CONSISTENCIA:")
        print(f"   - Stock del producto: {producto.stock}")
        print(f"   - Stock total en lotes: {stock_en_lotes}")
        print(f"   - ¿Están sincronizados?: {'✅ SÍ' if producto.stock == stock_en_lotes else '❌ NO'}")
        
        if producto.stock == stock_en_lotes:
            print(f"\n🎉 PRUEBA EXITOSA: El vencimiento se agregó correctamente sin errores")
        else:
            print(f"\n⚠️  ADVERTENCIA: Hay inconsistencia en el stock")
            
    except Exception as e:
        print(f"❌ ERROR durante la prueba: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Limpiar: eliminar el producto de prueba
        try:
            producto.delete()
            print(f"\n🧹 Producto de prueba eliminado")
        except:
            pass

if __name__ == "__main__":
    test_agregar_vencimiento()
