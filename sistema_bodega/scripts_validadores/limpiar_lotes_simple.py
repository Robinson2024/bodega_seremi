from accounts.models import LoteProducto, Producto

def verificar_y_limpiar_lotes():
    """Función para verificar y limpiar lotes vacíos desde Django shell"""
    
    print("🔍 Verificando lotes vacíos...")
    
    # Obtener lotes vacíos
    lotes_vacios = LoteProducto.objects.filter(stock=0)
    total_vacios = lotes_vacios.count()
    
    print(f"📊 Lotes vacíos encontrados: {total_vacios}")
    
    if total_vacios > 0:
        print("\n📋 Detalles de lotes vacíos:")
        for lote in lotes_vacios:
            print(f"   - {lote.producto.codigo_barra} | Lote #{lote.numero_lote} | Stock: {lote.stock}")
        
        # Eliminar lotes vacíos
        print(f"\n🗑️ Eliminando {total_vacios} lotes vacíos...")
        lotes_vacios.delete()
        print("✅ Lotes vacíos eliminados exitosamente.")
        
        # Actualizar stock de productos afectados
        print("🔄 Actualizando stock de productos...")
        for producto in Producto.objects.filter(tiene_vencimiento=True):
            producto.actualizar_stock_total()
        
        print("✅ Stock de productos actualizado.")
    else:
        print("✅ No hay lotes vacíos para eliminar.")
    
    print("\n🎉 Proceso completado. Ahora puede agregar stock sin errores.")

# Ejecutar la función
if __name__ == "__main__":
    verificar_y_limpiar_lotes()
