#!/usr/bin/env python
"""
Script para migrar productos existentes al sistema de lotes automático.

Este script:
1. Identifica todos los productos con fecha de vencimiento que no tienen lotes
2. Crea automáticamente un lote inicial para cada producto
3. Transfiere el stock existente al lote creado
4. Mantiene la integridad de los datos existentes

Ejecutar con: python migrar_lotes.py
"""
import os
import sys
import django
from datetime import date, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
django.setup()

from accounts.models import Producto, LoteProducto

def migrar_productos_a_lotes():
    """Migra todos los productos con vencimiento al sistema de lotes."""
    print("=== INICIANDO MIGRACIÓN DE PRODUCTOS A SISTEMA DE LOTES ===\n")
    
    # Obtener productos con vencimiento que no tienen lotes
    productos_con_vencimiento = Producto.objects.filter(
        tiene_vencimiento=True,
        fecha_vencimiento__isnull=False
    )
    
    productos_sin_lotes = []
    productos_con_lotes = []
    
    for producto in productos_con_vencimiento:
        if not producto.lotes.exists():
            productos_sin_lotes.append(producto)
        else:
            productos_con_lotes.append(producto)
    
    print(f"📊 ESTADÍSTICAS INICIALES:")
    print(f"   • Total productos con vencimiento: {productos_con_vencimiento.count()}")
    print(f"   • Productos SIN lotes: {len(productos_sin_lotes)}")
    print(f"   • Productos CON lotes: {len(productos_con_lotes)}")
    print()
    
    if not productos_sin_lotes:
        print("✅ Todos los productos con vencimiento ya tienen lotes asignados.")
        print("   No se requiere migración.")
        return
    
    print(f"🔄 INICIANDO MIGRACIÓN DE {len(productos_sin_lotes)} PRODUCTOS...\n")
    
    productos_migrados = 0
    productos_con_errores = []
    
    for producto in productos_sin_lotes:
        try:
            print(f"⏳ Procesando: {producto.descripcion}")
            print(f"   • Código: {producto.codigo_barra}")
            print(f"   • Stock actual: {producto.stock}")
            print(f"   • Fecha vencimiento: {producto.fecha_vencimiento}")
            
            # Solo crear lote si tiene stock > 0
            if producto.stock > 0:
                # Crear el primer lote con numeración automática
                lote = producto.crear_lote_automatico(
                    cantidad=producto.stock,
                    fecha_vencimiento=producto.fecha_vencimiento
                )
                
                print(f"   ✅ Lote creado: #{lote.numero_lote} con {lote.stock} unidades")
                productos_migrados += 1
            else:
                print(f"   ⚠️  Sin stock - No se crea lote")
                productos_migrados += 1
            
            print()
            
        except Exception as e:
            error_msg = f"Error migrando {producto.descripcion}: {str(e)}"
            print(f"   ❌ {error_msg}")
            productos_con_errores.append({
                'producto': producto,
                'error': str(e)
            })
            print()
    
    # Verificar integridad de datos después de la migración
    print("🔍 VERIFICANDO INTEGRIDAD DE DATOS...\n")
    
    productos_verificados = 0
    productos_con_problemas = []
    
    for producto in productos_con_vencimiento:
        if producto.tiene_vencimiento and producto.stock > 0:
            if not producto.lotes.filter(stock__gt=0).exists():
                productos_con_problemas.append(producto)
            else:
                # Verificar que el stock total coincida
                stock_lotes = sum(lote.stock for lote in producto.lotes.all())
                if stock_lotes != producto.stock:
                    productos_con_problemas.append(producto)
                    print(f"⚠️  Stock inconsistente en {producto.descripcion}: Producto={producto.stock}, Lotes={stock_lotes}")
                else:
                    productos_verificados += 1
    
    # Mostrar resumen final
    print("="*60)
    print("📋 RESUMEN DE MIGRACIÓN")
    print("="*60)
    print(f"✅ Productos migrados exitosamente: {productos_migrados}")
    print(f"✅ Productos verificados: {productos_verificados}")
    
    if productos_con_errores:
        print(f"❌ Productos con errores: {len(productos_con_errores)}")
        for error in productos_con_errores:
            print(f"   • {error['producto'].descripcion}: {error['error']}")
    
    if productos_con_problemas:
        print(f"⚠️  Productos con problemas de integridad: {len(productos_con_problemas)}")
        for producto in productos_con_problemas:
            print(f"   • {producto.descripcion} ({producto.codigo_barra})")
    
    print("\n🎉 MIGRACIÓN COMPLETADA")
    print("\nPróximos pasos:")
    print("1. Verificar que todos los productos tienen lotes correctos")
    print("2. Actualizar formularios para usar el sistema de lotes")
    print("3. Actualizar vistas para mostrar información de lotes")
    print("4. Probar el flujo completo de entrada y salida de stock")

def mostrar_estadisticas_lotes():
    """Muestra estadísticas detalladas del sistema de lotes."""
    print("\n" + "="*60)
    print("📊 ESTADÍSTICAS DEL SISTEMA DE LOTES")
    print("="*60)
    
    # Productos con y sin vencimiento
    total_productos = Producto.objects.all().count()
    productos_con_vencimiento = Producto.objects.filter(tiene_vencimiento=True).count()
    productos_sin_vencimiento = total_productos - productos_con_vencimiento
    
    print(f"📦 PRODUCTOS:")
    print(f"   • Total: {total_productos}")
    print(f"   • Con vencimiento: {productos_con_vencimiento}")
    print(f"   • Sin vencimiento: {productos_sin_vencimiento}")
    print()
    
    # Lotes por estado
    hoy = date.today()
    
    total_lotes = LoteProducto.objects.all().count()
    lotes_con_stock = LoteProducto.objects.filter(stock__gt=0).count()
    lotes_sin_stock = total_lotes - lotes_con_stock
    
    print(f"📊 LOTES:")
    print(f"   • Total lotes: {total_lotes}")
    print(f"   • Con stock: {lotes_con_stock}")
    print(f"   • Sin stock: {lotes_sin_stock}")
    print()
    
    # Análisis de vencimientos
    lotes_activos = LoteProducto.objects.filter(stock__gt=0)
    vencidos = lotes_activos.filter(fecha_vencimiento__lt=hoy).count()
    vencen_hoy = lotes_activos.filter(fecha_vencimiento=hoy).count()
    criticos = lotes_activos.filter(
        fecha_vencimiento__gt=hoy,
        fecha_vencimiento__lte=hoy + timedelta(days=7)
    ).count()
    
    print(f"⚠️  ANÁLISIS DE VENCIMIENTOS (Lotes con stock):")
    print(f"   • Vencidos: {vencidos}")
    print(f"   • Vencen hoy: {vencen_hoy}")
    print(f"   • Críticos (≤7 días): {criticos}")
    print()

def crear_productos_ejemplo():
    """Crea algunos productos de ejemplo para pruebas (opcional)."""
    print("\n🧪 ¿Quieres crear productos de ejemplo para pruebas? (s/n): ", end="")
    try:
        respuesta = input().strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\nSaltando creación de productos de ejemplo...")
        return
    
    if respuesta not in ['s', 'si', 'y', 'yes']:
        return
    
    ejemplos = [
        {
            'codigo_barra': 'TEST001',
            'descripcion': 'Alcohol Gel 500ml (EJEMPLO)',
            'stock': 25,
            'fecha_vencimiento': date.today() + timedelta(days=15),  # Vence en 15 días (crítico)
        },
        {
            'codigo_barra': 'TEST002',
            'descripcion': 'Mascarillas N95 (EJEMPLO)',
            'stock': 100,
            'fecha_vencimiento': date.today() + timedelta(days=3),   # Vence en 3 días (crítico)
        },
        {
            'codigo_barra': 'TEST003',
            'descripcion': 'Guantes Nitrilo (EJEMPLO)',
            'stock': 50,
            'fecha_vencimiento': date.today() + timedelta(days=60),  # Vence en 60 días (normal)
        }
    ]
    
    print("\n🔄 Creando productos de ejemplo...")
    for ejemplo in ejemplos:
        try:
            producto, created = Producto.objects.get_or_create(
                codigo_barra=ejemplo['codigo_barra'],
                defaults={
                    'descripcion': ejemplo['descripcion'],
                    'stock': ejemplo['stock'],
                    'tiene_vencimiento': True,
                    'fecha_vencimiento': ejemplo['fecha_vencimiento']
                }
            )
            
            if created:
                # Crear lote automáticamente
                lote = producto.crear_lote_automatico(
                    cantidad=ejemplo['stock'],
                    fecha_vencimiento=ejemplo['fecha_vencimiento']
                )
                print(f"✅ Producto ejemplo creado: {producto.descripcion} (Lote {lote.numero_lote})")
            else:
                print(f"⚠️  Producto ejemplo ya existe: {producto.descripcion}")
                
        except Exception as e:
            print(f"❌ Error al crear producto ejemplo {ejemplo['descripcion']}: {e}")

def main():
    """Función principal del script de migración."""
    print("🚀 MIGRACIÓN AL SISTEMA DE LOTES AUTOMÁTICOS")
    print("=" * 50)
    
    try:
        # Paso 1: Migrar productos existentes
        migrar_productos_a_lotes()
        
        # Paso 2: Mostrar estadísticas
        mostrar_estadisticas_lotes()
        
        # Paso 3: Crear productos de ejemplo (opcional)
        crear_productos_ejemplo()
        
        print("\n" + "=" * 50)
        print("🎉 ¡PROCESO COMPLETADO EXITOSAMENTE!")
        print("   El sistema de lotes automáticos está listo para usar.")
        
    except KeyboardInterrupt:
        print("\n❌ Proceso cancelado por el usuario.")
        return False
    except Exception as e:
        print(f"\n❌ Error durante el proceso: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    main()
