#!/usr/bin/env python
"""
Script de prueba para verificar las correcciones en la gestión de vencimientos.
Ejecutar desde el directorio sistema_bodega con: python test_lotes_activos.py
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

def test_lotes_activos():
    """Prueba la funcionalidad de mostrar solo lotes activos en gestión de vencimientos."""
    
    print("🧪 INICIANDO PRUEBA: Gestión de lotes activos vs históricos")
    print("=" * 65)
    
    # 1. Crear producto de prueba con lotes
    try:
        # Crear producto con vencimiento
        producto, created = Producto.objects.get_or_create(
            codigo_barra='888888',
            defaults={
                'descripcion': 'Producto de Prueba - Lotes Activos',
                'stock': 100,
                'tiene_vencimiento': True,
                'fecha_vencimiento': date.today() + timedelta(days=60)
            }
        )
        
        if not created:
            # Limpiar lotes existentes para la prueba
            producto.lotes.all().delete()
            producto.stock = 100
            producto.save()
        
        print(f"✅ Producto de prueba creado/actualizado:")
        print(f"   - Código: {producto.codigo_barra}")
        print(f"   - Stock inicial: {producto.stock}")
        
        # 2. Crear varios lotes con diferentes estados
        print(f"\n🔄 CREANDO LOTES DE PRUEBA...")
        
        # Lote 1: Con stock (activo)
        lote1 = LoteProducto.objects.create(
            producto=producto,
            numero_lote=1,
            fecha_vencimiento=date.today() + timedelta(days=30),
            stock=40
        )
        print(f"   ✅ Lote 1 creado: {lote1.stock} unidades (ACTIVO)")
        
        # Lote 2: Con stock (activo)
        lote2 = LoteProducto.objects.create(
            producto=producto,
            numero_lote=2,
            fecha_vencimiento=date.today() + timedelta(days=60),
            stock=30
        )
        print(f"   ✅ Lote 2 creado: {lote2.stock} unidades (ACTIVO)")
        
        # Lote 3: Sin stock (histórico)
        lote3 = LoteProducto.objects.create(
            producto=producto,
            numero_lote=3,
            fecha_vencimiento=date.today() + timedelta(days=90),
            stock=0
        )
        print(f"   ✅ Lote 3 creado: {lote3.stock} unidades (HISTÓRICO)")
        
        # Lote 4: Sin stock (histórico)
        lote4 = LoteProducto.objects.create(
            producto=producto,
            numero_lote=4,
            fecha_vencimiento=date.today() + timedelta(days=45),
            stock=0
        )
        print(f"   ✅ Lote 4 creado: {lote4.stock} unidades (HISTÓRICO)")
        
        # Sincronizar stock del producto
        producto.stock = 30  # Simular stock restante después de salidas
        producto.save()
        
        print(f"\n📊 ESTADO INICIAL DEL PRODUCTO:")
        print(f"   - Stock del producto: {producto.stock}")
        print(f"   - Total lotes creados: {producto.lotes.count()}")
        print(f"   - Lotes con stock > 0: {producto.lotes.filter(stock__gt=0).count()}")
        print(f"   - Lotes con stock = 0: {producto.lotes.filter(stock=0).count()}")
        
        # 3. Probar métodos de lotes activos vs todos los lotes
        print(f"\n🔍 PROBANDO MÉTODOS DE GESTIÓN DE LOTES:")
        
        # Método original (todos los lotes)
        todos_lotes = producto.get_lotes_detalle()
        print(f"   📋 get_lotes_detalle() (todos): {len(todos_lotes)} lotes")
        for lote in todos_lotes:
            print(f"      - Lote #{lote['numero_lote']}: {lote['stock']} unidades ({'VACÍO' if lote['esta_vacio'] else 'ACTIVO'})")
        
        # Método nuevo (solo lotes activos)
        lotes_activos = producto.get_lotes_activos_detalle()
        print(f"   📋 get_lotes_activos_detalle() (solo activos): {len(lotes_activos)} lotes")
        for lote in lotes_activos:
            print(f"      - Lote #{lote['numero_lote']}: {lote['stock']} unidades (ACTIVO)")
        
        # Método nuevo (contador de lotes activos)
        total_activos = producto.get_total_lotes_activos()
        print(f"   📋 get_total_lotes_activos(): {total_activos} lotes")
        
        # 4. Verificar comportamiento esperado
        print(f"\n✅ VERIFICACIÓN DE COMPORTAMIENTO:")
        
        # Verificación 1: Todos los lotes incluye vacíos
        if len(todos_lotes) == 4:
            print(f"   ✅ get_lotes_detalle() incluye todos los lotes (4)")
        else:
            print(f"   ❌ get_lotes_detalle() debería incluir 4 lotes, pero incluye {len(todos_lotes)}")
        
        # Verificación 2: Solo lotes activos excluye vacíos
        if len(lotes_activos) == 2:
            print(f"   ✅ get_lotes_activos_detalle() incluye solo lotes activos (2)")
        else:
            print(f"   ❌ get_lotes_activos_detalle() debería incluir 2 lotes, pero incluye {len(lotes_activos)}")
        
        # Verificación 3: Contador coincide
        if total_activos == len(lotes_activos):
            print(f"   ✅ get_total_lotes_activos() coincide con lotes activos ({total_activos})")
        else:
            print(f"   ❌ get_total_lotes_activos() no coincide: {total_activos} vs {len(lotes_activos)}")
        
        # Verificación 4: Lotes activos no incluyen vacíos
        lotes_vacios_en_activos = [l for l in lotes_activos if l['stock'] == 0]
        if len(lotes_vacios_en_activos) == 0:
            print(f"   ✅ get_lotes_activos_detalle() no incluye lotes vacíos")
        else:
            print(f"   ❌ get_lotes_activos_detalle() incluye {len(lotes_vacios_en_activos)} lotes vacíos")
        
        # 5. Simular producto sin lotes activos
        print(f"\n🔄 SIMULANDO PRODUCTO SIN LOTES ACTIVOS...")
        
        # Vaciar todos los lotes
        for lote in producto.lotes.all():
            lote.stock = 0
            lote.save()
        
        producto.stock = 0
        producto.save()
        
        lotes_activos_vacios = producto.get_lotes_activos_detalle()
        total_activos_vacios = producto.get_total_lotes_activos()
        
        print(f"   📊 Después de vaciar todos los lotes:")
        print(f"   - Stock del producto: {producto.stock}")
        print(f"   - Lotes activos: {len(lotes_activos_vacios)}")
        print(f"   - Total lotes activos: {total_activos_vacios}")
        
        if len(lotes_activos_vacios) == 0 and total_activos_vacios == 0:
            print(f"   ✅ Producto sin stock no muestra lotes activos (correcto)")
        else:
            print(f"   ❌ Producto sin stock aún muestra lotes activos (incorrecto)")
        
        print(f"\n🎉 RESULTADO DE LA PRUEBA:")
        
        if (len(todos_lotes) == 4 and 
            len(lotes_activos) == 2 and 
            total_activos == 2 and 
            len(lotes_vacios_en_activos) == 0 and 
            len(lotes_activos_vacios) == 0):
            print(f"   ✅ TODAS LAS VERIFICACIONES PASARON")
            print(f"   ✅ La gestión de lotes activos funciona correctamente")
            print(f"   ✅ Los lotes vacíos se preservan para historial pero no aparecen en gestión")
        else:
            print(f"   ❌ ALGUNAS VERIFICACIONES FALLARON")
            print(f"   ❌ Revisar la implementación de los métodos")
            
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
    test_lotes_activos()
