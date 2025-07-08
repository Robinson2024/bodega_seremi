#!/usr/bin/env python
"""
Corrección automática del Bincard del producto 100047
Corrige la transacción duplicada sin confirmación manual
"""

import os
import sys
import django

# Configurar Django
sys.path.append('c:\\Users\\Robinson Bravo\\Desktop\\bodega_seremi\\sistema_bodega')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
django.setup()

from accounts.models import Producto, LoteProducto, Transaccion
from django.db import models, transaction

def corregir_bincard_automatico():
    print("=" * 70)
    print("   CORRECCIÓN AUTOMÁTICA DEL BINCARD - PRODUCTO 100047")
    print("=" * 70)
    print()
    
    try:
        producto = Producto.objects.get(codigo_barra='100047')
        print(f"📦 PRODUCTO: {producto.descripcion}")
        
        # Obtener estado actual
        transacciones = Transaccion.objects.filter(producto=producto).order_by('fecha')
        total_entradas_bincard = sum(t.cantidad for t in transacciones if t.tipo == 'entrada')
        discrepancia = total_entradas_bincard - producto.stock
        
        print(f"📊 ESTADO ANTES DE LA CORRECCIÓN:")
        print(f"   • Stock real: {producto.stock}")
        print(f"   • Total Bincard: {total_entradas_bincard}")
        print(f"   • Discrepancia: {discrepancia}")
        
        if discrepancia > 0:
            print(f"\n🔧 APLICANDO CORRECCIÓN AUTOMÁTICA:")
            
            # Buscar la primera entrada (la problemática)
            primera_entrada = transacciones.filter(tipo='entrada').first()
            
            if primera_entrada:
                cantidad_original = primera_entrada.cantidad
                cantidad_correcta = cantidad_original - discrepancia
                
                print(f"   • Corrigiendo transacción del {primera_entrada.fecha.strftime('%Y-%m-%d %H:%M')}")
                print(f"   • Cantidad: {cantidad_original} → {cantidad_correcta}")
                
                with transaction.atomic():
                    # Actualizar la transacción
                    primera_entrada.cantidad = cantidad_correcta
                    primera_entrada.observacion = f"AUTO-CORREGIDO: Eliminada duplicación de {discrepancia} unidades. Original: {cantidad_original}"
                    primera_entrada.save()
                    
                    print(f"   ✅ Transacción corregida exitosamente")
                
                # Verificar resultado
                transacciones_actualizadas = Transaccion.objects.filter(producto=producto)
                nuevo_total = sum(t.cantidad for t in transacciones_actualizadas if t.tipo == 'entrada')
                nueva_discrepancia = nuevo_total - producto.stock
                
                print(f"\n📊 RESULTADO DESPUÉS DE LA CORRECCIÓN:")
                print(f"   • Stock real: {producto.stock}")
                print(f"   • Nuevo total Bincard: {nuevo_total}")
                print(f"   • Nueva discrepancia: {nueva_discrepancia}")
                
                if nueva_discrepancia == 0:
                    print(f"\n🎉 ¡ÉXITO TOTAL!")
                    print(f"   ✅ Bincard sincronizado perfectamente con stock real")
                    print(f"   ✅ No hay más discrepancias")
                    print(f"   ✅ La trazabilidad se mantiene intacta")
                else:
                    print(f"\n⚠️  Aún hay discrepancia residual: {nueva_discrepancia}")
                
                # Mostrar transacciones actualizadas
                print(f"\n📋 HISTORIAL CORREGIDO:")
                for i, trans in enumerate(transacciones_actualizadas.order_by('fecha'), 1):
                    tipo_icon = "📥" if trans.tipo == "entrada" else "📤"
                    print(f"   {i}. {tipo_icon} {trans.fecha.strftime('%Y-%m-%d %H:%M')}: {trans.cantidad} unidades")
                    if trans.observacion and "AUTO-CORREGIDO" in trans.observacion:
                        print(f"      └─ {trans.observacion}")
                        
            else:
                print("   ❌ No se encontró transacción para corregir")
        else:
            print(f"   ✅ No hay discrepancias - Bincard ya está correcto")
        
    except Producto.DoesNotExist:
        print("❌ Producto 100047 no encontrado")
    except Exception as e:
        print(f"❌ Error durante la corrección: {e}")
    
    print()
    print("=" * 70)
    print("          CORRECCIÓN AUTOMÁTICA COMPLETADA")
    print("=" * 70)

if __name__ == "__main__":
    corregir_bincard_automatico()
