from accounts.models import Producto, LoteProducto, Transaccion

# Obtener producto
producto = Producto.objects.get(codigo_barra='100041')

print("=== DIAGNÓSTICO PRODUCTO LECHE DE VACA ===")
print(f"Descripción: {producto.descripcion}")
print(f"Stock actual: {producto.stock}")
print(f"Tiene vencimiento: {producto.tiene_vencimiento}")
print(f"Fecha vencimiento: {producto.fecha_vencimiento}")

# Verificar lotes
lotes = producto.lotes.all()
print(f"\nLotes total: {lotes.count()}")
if lotes:
    for lote in lotes:
        print(f"  Lote #{lote.numero_lote}: {lote.stock} unidades - Vence: {lote.fecha_vencimiento}")
else:
    print("  No hay lotes")

# Verificar transacciones recientes
transacciones = Transaccion.objects.filter(producto=producto).order_by('-fecha')[:5]
print(f"\nÚltimas 5 transacciones:")
for trans in transacciones:
    print(f"  {trans.fecha.strftime('%d/%m/%Y %H:%M')} - {trans.tipo.upper()}: {trans.cantidad} unidades")
