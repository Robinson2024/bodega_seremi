from accounts.models import Producto, LoteProducto

def sincronizar_stock_leche():
    """Sincroniza el stock del producto Leche de vaca 1 L"""
    
    try:
        # Buscar el producto de leche de vaca
        producto = Producto.objects.get(codigo_barra='100041')
        
        print(f"🥛 Producto encontrado: {producto.descripcion}")
        print(f"📊 Stock actual en base de datos: {producto.stock}")
        
        if producto.tiene_vencimiento:
            print(f"📅 Producto con vencimiento: {producto.fecha_vencimiento}")
            
            # Mostrar lotes actuales
            lotes = producto.lotes.all().order_by('numero_lote')
            print(f"\n📦 Lotes actuales:")
            total_stock_lotes = 0
            
            for lote in lotes:
                print(f"   - Lote #{lote.numero_lote}: {lote.stock} unidades (Vence: {lote.fecha_vencimiento})")
                total_stock_lotes += lote.stock
            
            print(f"\n📊 Stock total calculado desde lotes: {total_stock_lotes}")
            
            if producto.stock != total_stock_lotes:
                print(f"❌ DESINCRONIZACIÓN DETECTADA!")
                print(f"   Stock en producto: {producto.stock}")
                print(f"   Stock en lotes: {total_stock_lotes}")
                print(f"   Diferencia: {producto.stock - total_stock_lotes}")
                
                # Corregir sincronización
                print(f"🔄 Sincronizando stock...")
                producto.stock = total_stock_lotes
                producto.save()
                print(f"✅ Stock sincronizado a: {producto.stock}")
                
                # Limpiar lotes vacíos si existen
                lotes_vacios = producto.lotes.filter(stock=0)
                if lotes_vacios.exists():
                    cantidad_vacios = lotes_vacios.count()
                    lotes_vacios.delete()
                    print(f"🗑️ Eliminados {cantidad_vacios} lotes vacíos")
                
            else:
                print(f"✅ Stock sincronizado correctamente")
        else:
            print(f"📄 Producto sin vencimiento")
            
    except Producto.DoesNotExist:
        print(f"❌ Producto con código 100041 (Leche de vaca 1 L) no encontrado")
    except Exception as e:
        print(f"❌ Error: {e}")

def verificar_todas_las_transacciones():
    """Verifica las últimas transacciones del producto"""
    try:
        from accounts.models import Transaccion
        producto = Producto.objects.get(codigo_barra='100041')
        
        transacciones = Transaccion.objects.filter(producto=producto).order_by('-fecha')[:10]
        
        print(f"\n📋 Últimas 10 transacciones de {producto.descripcion}:")
        for trans in transacciones:
            tipo_icon = "📥" if trans.tipo == "entrada" else "📤"
            print(f"   {tipo_icon} {trans.fecha.strftime('%d/%m/%Y %H:%M')} - {trans.tipo.title()}: {trans.cantidad} unidades")
            
    except Exception as e:
        print(f"❌ Error verificando transacciones: {e}")

if __name__ == "__main__":
    print("🔧 SINCRONIZACIÓN DE STOCK - LECHE DE VACA 1L")
    print("=" * 50)
    
    sincronizar_stock_leche()
    verificar_todas_las_transacciones()
    
    print("\n" + "=" * 50)
    print("✅ Proceso completado")
