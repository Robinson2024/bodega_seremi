#!/usr/bin/env python
"""
Script de prueba para verificar el comportamiento de las vistas de control de vencimientos.
Ejecutar desde el directorio sistema_bodega con: python test_vistas_vencimientos.py
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
django.setup()

from accounts.models import Producto, LoteProducto
from accounts.views import control_vencimientos, agregar_vencimiento_producto
from datetime import date, timedelta
from django.test import RequestFactory
from django.contrib.auth import get_user_model

def test_vistas_vencimientos():
    """Prueba el comportamiento de las vistas con productos que tienen lotes vacíos."""
    
    print("🧪 INICIANDO PRUEBA: Vistas de control de vencimientos")
    print("=" * 60)
    
    # Crear usuario de prueba
    User = get_user_model()
    try:
        user = User.objects.get(username='test_user')
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='test_user',
            rut='123456789',
            nombre='Usuario de Prueba'
        )
    
    # Factory para crear requests simulados
    factory = RequestFactory()
    
    try:
        # 1. Crear productos de prueba
        print(f"🔄 CREANDO PRODUCTOS DE PRUEBA...")
        
        # Producto 1: Con lotes activos
        producto1, _ = Producto.objects.get_or_create(
            codigo_barra='111111',
            defaults={
                'descripcion': 'Producto con Lotes Activos',
                'stock': 50,
                'tiene_vencimiento': True,
                'fecha_vencimiento': date.today() + timedelta(days=30)
            }
        )
        producto1.lotes.all().delete()
        
        # Crear lotes para producto1
        LoteProducto.objects.create(
            producto=producto1,
            numero_lote=1,
            fecha_vencimiento=date.today() + timedelta(days=30),
            stock=30
        )
        LoteProducto.objects.create(
            producto=producto1,
            numero_lote=2,
            fecha_vencimiento=date.today() + timedelta(days=60),
            stock=20
        )
        print(f"   ✅ Producto 1: {producto1.descripcion} (con lotes activos)")
        
        # Producto 2: Solo con lotes vacíos
        producto2, _ = Producto.objects.get_or_create(
            codigo_barra='222222',
            defaults={
                'descripcion': 'Producto Solo con Lotes Vacíos',
                'stock': 0,
                'tiene_vencimiento': True,
                'fecha_vencimiento': date.today() + timedelta(days=30)
            }
        )
        producto2.lotes.all().delete()
        
        # Crear lotes vacíos para producto2
        LoteProducto.objects.create(
            producto=producto2,
            numero_lote=1,
            fecha_vencimiento=date.today() + timedelta(days=30),
            stock=0
        )
        LoteProducto.objects.create(
            producto=producto2,
            numero_lote=2,
            fecha_vencimiento=date.today() + timedelta(days=60),
            stock=0
        )
        print(f"   ✅ Producto 2: {producto2.descripcion} (solo lotes vacíos)")
        
        # Producto 3: Mixto (lotes activos y vacíos)
        producto3, _ = Producto.objects.get_or_create(
            codigo_barra='333333',
            defaults={
                'descripcion': 'Producto Mixto',
                'stock': 25,
                'tiene_vencimiento': True,
                'fecha_vencimiento': date.today() + timedelta(days=30)
            }
        )
        producto3.lotes.all().delete()
        
        # Crear lotes mixtos para producto3
        LoteProducto.objects.create(
            producto=producto3,
            numero_lote=1,
            fecha_vencimiento=date.today() + timedelta(days=30),
            stock=25
        )
        LoteProducto.objects.create(
            producto=producto3,
            numero_lote=2,
            fecha_vencimiento=date.today() + timedelta(days=60),
            stock=0
        )
        LoteProducto.objects.create(
            producto=producto3,
            numero_lote=3,
            fecha_vencimiento=date.today() + timedelta(days=90),
            stock=0
        )
        print(f"   ✅ Producto 3: {producto3.descripcion} (lotes mixtos)")
        
        # 2. Probar vista control_vencimientos
        print(f"\n🔍 PROBANDO VISTA control_vencimientos...")
        
        request = factory.get('/accounts/control-vencimientos/')
        request.user = user
        
        # Simular la lógica de la vista
        productos_base = Producto.objects.filter(
            tiene_vencimiento=True,
            stock__gt=0
        ).select_related('categoria').prefetch_related('lotes')
        
        # Filtrar productos que tienen al menos un lote con stock > 0
        productos_con_lotes_activos = []
        for producto in productos_base:
            if producto.get_total_lotes_activos() > 0:
                productos_con_lotes_activos.append(producto)
        
        print(f"   📊 Productos encontrados antes del filtro: {productos_base.count()}")
        print(f"   📊 Productos con lotes activos: {len(productos_con_lotes_activos)}")
        
        for producto in productos_con_lotes_activos:
            lotes_activos = producto.get_total_lotes_activos()
            print(f"      - {producto.descripcion}: {lotes_activos} lotes activos")
        
        # Verificación: Producto2 NO debe aparecer
        producto2_en_lista = any(p.codigo_barra == '222222' for p in productos_con_lotes_activos)
        if not producto2_en_lista:
            print(f"   ✅ Producto con solo lotes vacíos NO aparece en control de vencimientos")
        else:
            print(f"   ❌ Producto con solo lotes vacíos SÍ aparece (incorrecto)")
        
        # 3. Probar vista agregar_vencimiento_producto
        print(f"\n🔍 PROBANDO VISTA agregar_vencimiento_producto...")
        
        request = factory.get('/accounts/agregar-vencimiento/')
        request.user = user
        
        # Simular la lógica de preparar información de productos
        productos = Producto.objects.filter(tiene_vencimiento=True).select_related('categoria').prefetch_related('lotes')
        
        productos_info = []
        for producto in productos:
            info = {
                'producto': producto,
                'lotes_detalle': [],
                'total_lotes': 0,
                'proximo_vencimiento': None,
                'estado_vencimiento': 'Sin Vencimiento'
            }
            
            if producto.tiene_vencimiento:
                info['lotes_detalle'] = producto.get_lotes_activos_detalle()  # Solo lotes activos
                info['total_lotes'] = len(info['lotes_detalle'])  # Solo contar lotes activos
                info['proximo_vencimiento'] = producto.get_proximo_vencimiento()
                info['estado_vencimiento'] = producto.get_estado_vencimiento_completo()
            
            productos_info.append(info)
        
        print(f"   📊 Información de productos para gestión:")
        for info in productos_info:
            print(f"      - {info['producto'].descripcion}: {info['total_lotes']} lotes activos para gestión")
        
        # Verificación: Producto2 debe tener 0 lotes activos para gestión
        producto2_info = next((info for info in productos_info if info['producto'].codigo_barra == '222222'), None)
        if producto2_info and producto2_info['total_lotes'] == 0:
            print(f"   ✅ Producto con solo lotes vacíos muestra 0 lotes para gestión")
        elif producto2_info:
            print(f"   ❌ Producto con solo lotes vacíos muestra {producto2_info['total_lotes']} lotes (incorrecto)")
        
        # Verificación: Producto3 debe mostrar solo 1 lote activo
        producto3_info = next((info for info in productos_info if info['producto'].codigo_barra == '333333'), None)
        if producto3_info and producto3_info['total_lotes'] == 1:
            print(f"   ✅ Producto mixto muestra solo lotes activos (1 de 3 lotes)")
        elif producto3_info:
            print(f"   ❌ Producto mixto muestra {producto3_info['total_lotes']} lotes (debería ser 1)")
        
        # 4. Verificación de comportamiento de botones
        print(f"\n🔘 VERIFICANDO LÓGICA DE BOTONES:")
        
        # Producto1: Debe mostrar botón "Lotes (2)"
        p1_lotes_activos = producto1.get_total_lotes_activos()
        if p1_lotes_activos > 0:
            print(f"   ✅ Producto 1: Debe mostrar botón 'Lotes ({p1_lotes_activos})'")
        
        # Producto2: Debe volver a mostrar botón "Agregar" (como si no tuviera lotes)
        p2_lotes_activos = producto2.get_total_lotes_activos()
        if p2_lotes_activos == 0:
            print(f"   ✅ Producto 2: Debe mostrar botón 'Agregar' (sin lotes activos)")
        
        # Producto3: Debe mostrar botón "Lotes (1)"
        p3_lotes_activos = producto3.get_total_lotes_activos()
        if p3_lotes_activos == 1:
            print(f"   ✅ Producto 3: Debe mostrar botón 'Lotes ({p3_lotes_activos})'")
        
        print(f"\n🎉 RESUMEN DE COMPORTAMIENTO ESPERADO:")
        print(f"   🔹 Control de Vencimientos:")
        print(f"     - Solo productos con lotes activos aparecen")
        print(f"     - Productos sin stock no aparecen")
        print(f"   🔹 Gestionar Vencimientos:")
        print(f"     - Productos sin lotes activos muestran botón 'Agregar'")
        print(f"     - Productos con lotes activos muestran botón 'Lotes (N)'")
        print(f"     - Lotes vacíos no se cuentan para gestión")
        print(f"   🔹 Modal de Lotes:")
        print(f"     - Solo muestra lotes con stock > 0")
        print(f"     - Permite modificar fechas solo de lotes activos")
        
    except Exception as e:
        print(f"❌ ERROR durante la prueba: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Limpiar: eliminar productos de prueba
        try:
            Producto.objects.filter(codigo_barra__in=['111111', '222222', '333333']).delete()
            user.delete()
            print(f"\n🧹 Productos y usuario de prueba eliminados")
        except Exception as e:
            print(f"⚠️ Error al limpiar: {e}")

if __name__ == "__main__":
    test_vistas_vencimientos()
