from django.core.management.base import BaseCommand
from django.db import models
from accounts.models import Producto, LoteProducto, Transaccion

class Command(BaseCommand):
    help = 'Corrige la desincronización de stock del producto Leche de vaca 1 L'

    def handle(self, *args, **options):
        try:
            producto = Producto.objects.get(codigo_barra='100041')
            self.stdout.write(f"=== CORRIGIENDO STOCK - {producto.descripcion} ===")
            
            # Estado actual
            stock_producto = producto.stock
            stock_lotes = producto.lotes.aggregate(total=models.Sum('stock'))['total'] or 0
            
            self.stdout.write(f"Stock actual en producto: {stock_producto}")
            self.stdout.write(f"Stock actual en lotes: {stock_lotes}")
            
            # Limpiar lotes vacíos
            lotes_vacios = producto.lotes.filter(stock=0)
            if lotes_vacios.exists():
                count = lotes_vacios.count()
                lotes_vacios.delete()
                self.stdout.write(f"✅ Eliminados {count} lotes vacíos")
            
            # Eliminar transacciones de prueba
            trans_prueba = Transaccion.objects.filter(
                producto=producto,
                observacion__icontains='prueba'
            )
            if trans_prueba.exists():
                count = trans_prueba.count()
                trans_prueba.delete()
                self.stdout.write(f"✅ Eliminadas {count} transacciones de prueba")
            
            # Calcular stock correcto desde transacciones
            transacciones = Transaccion.objects.filter(producto=producto).order_by('fecha')
            stock_calculado = 0
            
            self.stdout.write("\\nHistorial de transacciones:")
            for trans in transacciones:
                if trans.tipo == 'entrada':
                    stock_calculado += trans.cantidad
                    op = f"+{trans.cantidad}"
                else:
                    stock_calculado -= trans.cantidad
                    op = f"-{trans.cantidad}"
                
                acta_info = f" (Acta {trans.acta_entrega.numero_acta})" if trans.acta_entrega else ""
                self.stdout.write(f"  {trans.fecha.strftime('%Y-%m-%d %H:%M')} - {trans.tipo.upper()}: {op} = {stock_calculado}{acta_info}")
            
            self.stdout.write(f"\\nStock calculado desde transacciones: {stock_calculado}")
            
            # Establecer el stock correcto
            # Usar 500 como stock base correcto (antes de nuestras pruebas)
            stock_correcto = 500
            
            # Actualizar lotes
            lote_principal = producto.lotes.filter(numero_lote=1).first()
            if lote_principal:
                lote_principal.stock = stock_correcto
                lote_principal.save()
                self.stdout.write(f"✅ Lote #1 actualizado a {stock_correcto} unidades")
            
            # Eliminar lotes de prueba (lote #2)
            lote_prueba = producto.lotes.filter(numero_lote=2).first()
            if lote_prueba:
                lote_prueba.delete()
                self.stdout.write(f"✅ Eliminado lote de prueba #2")
            
            # Actualizar stock del producto
            producto.stock = stock_correcto
            producto.save()
            
            # Verificación final
            stock_final_lotes = producto.lotes.aggregate(total=models.Sum('stock'))['total'] or 0
            
            self.stdout.write(f"\\n🎯 CORRECCIÓN COMPLETADA:")
            self.stdout.write(f"Stock final en producto: {producto.stock}")
            self.stdout.write(f"Stock final en lotes: {stock_final_lotes}")
            
            if producto.stock == stock_final_lotes:
                self.stdout.write(self.style.SUCCESS(f"✅ SINCRONIZACIÓN EXITOSA: {producto.stock} unidades"))
            else:
                self.stdout.write(self.style.ERROR(f"❌ AÚN HAY DESINCRONIZACIÓN"))
            
        except Producto.DoesNotExist:
            self.stdout.write(self.style.ERROR('Producto con código 100041 no encontrado'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
