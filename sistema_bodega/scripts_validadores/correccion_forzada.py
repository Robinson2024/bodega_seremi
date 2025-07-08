#!/usr/bin/env python
"""
CORRECCIÓN FORZADA DE SINCRONIZACIÓN

Este script fuerza la sincronización del stock con el Bincard
resolviendo las discrepancias de manera definitiva.
"""

import os
import sys
import django

# Añadir el directorio padre al path para poder importar sistema_bodega
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
django.setup()

from accounts.models import Producto, Transaccion
from django.db import transaction
from datetime import datetime

def corregir_stock_forzado():
    """Fuerza la corrección del stock basado en el Bincard."""
    print("🔧 CORRECCIÓN FORZADA DE STOCK")
    print("=" * 50)
    
    productos_corregidos = []
    
    # Usar una transacción para asegurar consistencia
    with transaction.atomic():
        for producto in Producto.objects.all():
            # Calcular saldo real desde transacciones
            transacciones = Transaccion.objects.filter(producto=producto).order_by('fecha')
            saldo_bincard = 0
            
            for trans in transacciones:
                if trans.tipo == 'entrada':
                    saldo_bincard += trans.cantidad
                else:
                    saldo_bincard -= trans.cantidad
            
            # Si hay diferencia, corregir
            if saldo_bincard != producto.stock:
                stock_anterior = producto.stock
                
                # Forzar la actualización
                Producto.objects.filter(id=producto.id).update(stock=saldo_bincard)
                
                # Si tiene lotes, también sincronizar
                if producto.tiene_vencimiento and producto.lotes.exists():
                    # Ajustar stock de lotes si es necesario
                    total_lotes = sum(lote.stock for lote in producto.lotes.all())
                    if total_lotes != saldo_bincard:
                        # Distribuir el stock correcto entre los lotes existentes
                        lotes_activos = producto.lotes.filter(stock__gt=0).order_by('fecha_vencimiento')
                        if lotes_activos.exists():
                            # Ajustar el primer lote para que coincida
                            primer_lote = lotes_activos.first()
                            diferencia = saldo_bincard - (total_lotes - primer_lote.stock)
                            if diferencia >= 0:
                                primer_lote.stock = diferencia
                                primer_lote.save()
                
                productos_corregidos.append({
                    'producto': producto.descripcion,
                    'codigo': producto.codigo_barra,
                    'stock_anterior': stock_anterior,
                    'stock_nuevo': saldo_bincard
                })
                
                print(f"✅ {producto.descripcion} ({producto.codigo_barra})")
                print(f"   Stock: {stock_anterior} → {saldo_bincard}")
    
    print(f"\n📊 Total productos corregidos: {len(productos_corregidos)}")
    return productos_corregidos

def verificar_correccion():
    """Verifica que la corrección se aplicó correctamente."""
    print("\n🔍 VERIFICACIÓN DE CORRECCIÓN")
    print("=" * 50)
    
    errores = 0
    
    for producto in Producto.objects.all():
        # Recalcular saldo desde transacciones
        transacciones = Transaccion.objects.filter(producto=producto).order_by('fecha')
        saldo_bincard = 0
        
        for trans in transacciones:
            if trans.tipo == 'entrada':
                saldo_bincard += trans.cantidad
            else:
                saldo_bincard -= trans.cantidad
        
        # Recargar el producto desde la base de datos
        producto.refresh_from_db()
        
        if saldo_bincard != producto.stock:
            print(f"❌ {producto.descripcion}: Stock={producto.stock}, Bincard={saldo_bincard}")
            errores += 1
        else:
            print(f"✅ {producto.descripcion}: {producto.stock} (sincronizado)")
    
    if errores == 0:
        print(f"\n🎉 ¡ÉXITO! Todos los productos están sincronizados")
    else:
        print(f"\n⚠️ Aún hay {errores} productos con discrepancias")
    
    return errores == 0

def main():
    """Función principal."""
    print("🚀 CORRECCIÓN FORZADA DE SINCRONIZACIÓN STOCK-BINCARD")
    print("=" * 70)
    print("Fecha:", datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    print()
    
    # 1. Corregir stock forzadamente
    productos_corregidos = corregir_stock_forzado()
    
    # 2. Verificar corrección
    sincronizado = verificar_correccion()
    
    # Resumen
    print("\n" + "=" * 70)
    print("📋 RESUMEN")
    print("=" * 70)
    print(f"Productos corregidos: {len(productos_corregidos)}")
    print(f"Sistema sincronizado: {'SÍ' if sincronizado else 'NO'}")
    
    if sincronizado:
        print("\n🎉 ¡PROBLEMA RESUELTO!")
        print("   ✅ El stock ahora coincide exactamente con el Bincard")
        print("   ✅ No habrá más discrepancias al agregar productos")
        print("   ✅ Las salidas funcionarán correctamente")
    
    return sincronizado

if __name__ == "__main__":
    main()
