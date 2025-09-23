#!/usr/bin/env python3
"""
Script para limpiar lotes vacíos existentes en la base de datos.
Este script soluciona el problema de lotes con stock = 0 que causan conflictos de UNIQUE constraint.
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
django.setup()

from accounts.models import LoteProducto, Producto

def limpiar_lotes_vacios():
    """Limpia todos los lotes con stock = 0 de la base de datos."""
    print("🧹 Iniciando limpieza de lotes vacíos...")
    
    try:
        # Obtener todos los lotes vacíos
        lotes_vacios = LoteProducto.objects.filter(stock=0)
        total_lotes_vacios = lotes_vacios.count()
        
        if total_lotes_vacios == 0:
            print("✅ No hay lotes vacíos para eliminar.")
            return
        
        print(f"📊 Se encontraron {total_lotes_vacios} lotes vacíos.")
        
        # Mostrar detalles de los lotes que se van a eliminar
        productos_afectados = set()
        for lote in lotes_vacios:
            productos_afectados.add(lote.producto.codigo_barra)
            print(f"   - Producto: {lote.producto.codigo_barra} | Lote: #{lote.numero_lote} | Stock: {lote.stock}")
        
        # Confirmar eliminación
        respuesta = input(f"\n❓ ¿Desea eliminar estos {total_lotes_vacios} lotes vacíos? (s/N): ").lower().strip()
        
        if respuesta in ['s', 'si', 'sí', 'y', 'yes']:
            # Eliminar lotes vacíos
            lotes_eliminados = lotes_vacios.delete()[0]
            print(f"✅ Se eliminaron {lotes_eliminados} lotes vacíos exitosamente.")
            
            # Actualizar stock total de productos afectados
            print("🔄 Actualizando stock total de productos afectados...")
            for codigo_barra in productos_afectados:
                try:
                    producto = Producto.objects.get(codigo_barra=codigo_barra)
                    producto.actualizar_stock_total()
                    print(f"   ✅ Stock actualizado para {codigo_barra}")
                except Producto.DoesNotExist:
                    print(f"   ⚠️  Producto {codigo_barra} no encontrado")
                except Exception as e:
                    print(f"   ❌ Error actualizando {codigo_barra}: {e}")
            
            print(f"\n🎉 Limpieza completada exitosamente!")
            print(f"📈 Productos afectados: {len(productos_afectados)}")
            print(f"🗑️  Lotes eliminados: {lotes_eliminados}")
            
        else:
            print("❌ Operación cancelada por el usuario.")
            
    except Exception as e:
        print(f"❌ Error durante la limpieza: {e}")
        return False
    
    return True

def verificar_problemas_duplicados():
    """Verifica si existen problemas de lotes duplicados."""
    print("\n🔍 Verificando problemas de lotes duplicados...")
    
    try:
        # Buscar productos con lotes duplicados
        from django.db.models import Count
        productos_con_duplicados = (
            Producto.objects
            .annotate(
                lotes_count=Count('lotes__numero_lote')
            )
            .filter(lotes_count__gt=1)
        )
        
        problemas_encontrados = False
        
        for producto in productos_con_duplicados:
            # Verificar si hay números de lote repetidos
            from collections import Counter
            numeros_lotes = list(producto.lotes.values_list('numero_lote', flat=True))
            contador_lotes = Counter(numeros_lotes)
            
            for numero_lote, cantidad in contador_lotes.items():
                if cantidad > 1:
                    problemas_encontrados = True
                    print(f"⚠️  Producto {producto.codigo_barra} tiene {cantidad} lotes con número #{numero_lote}")
        
        if not problemas_encontrados:
            print("✅ No se encontraron problemas de lotes duplicados.")
        else:
            print("\n💡 Recomendación: Ejecute la limpieza de lotes vacíos para resolver estos problemas.")
            
    except Exception as e:
        print(f"❌ Error verificando duplicados: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 HERRAMIENTA DE LIMPIEZA DE LOTES VACÍOS")
    print("=" * 60)
    print("Este script soluciona el error:")
    print("'UNIQUE constraint failed: accounts_loteproducto.producto_id, accounts_loteproducto.numero_lote'")
    print("=" * 60)
    
    # Verificar problemas primero
    verificar_problemas_duplicados()
    
    # Ejecutar limpieza
    limpiar_lotes_vacios()
    
    print("\n" + "=" * 60)
    print("🏁 Proceso completado.")
    print("Ahora puede intentar agregar stock nuevamente sin errores.")
    print("=" * 60)
