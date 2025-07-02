from django.core.management.base import BaseCommand
from accounts.models import Producto, LoteProducto, Transaccion


class Command(BaseCommand):
    help = 'Diagnostica y corrige problemas de sincronización de stock'

    def add_arguments(self, parser):
        parser.add_argument(
            '--codigo',
            type=str,
            help='Código de barra del producto a diagnosticar',
            default='100041'
        )
        parser.add_argument(
            '--corregir',
            action='store_true',
            help='Corrige automáticamente los problemas encontrados',
        )

    def handle(self, *args, **options):
        codigo = options['codigo']
        corregir = options['corregir']
        
        try:
            producto = Producto.objects.get(codigo_barra=codigo)
            
            self.stdout.write(f"=== DIAGNÓSTICO PRODUCTO {codigo} ===")
            self.stdout.write(f"Descripción: {producto.descripcion}")
            self.stdout.write(f"Stock actual: {producto.stock}")
            self.stdout.write(f"Tiene vencimiento: {producto.tiene_vencimiento}")
            self.stdout.write(f"Fecha vencimiento: {producto.fecha_vencimiento}")
            
            # Verificar lotes
            lotes = producto.lotes.all()
            self.stdout.write(f"\nLotes encontrados: {lotes.count()}")
            
            total_stock_lotes = 0
            for lote in lotes:
                self.stdout.write(f"  Lote #{lote.numero_lote}: {lote.stock} unidades - Vence: {lote.fecha_vencimiento}")
                total_stock_lotes += lote.stock
            
            # Verificar transacciones recientes
            transacciones = Transaccion.objects.filter(producto=producto).order_by('-fecha')[:5]
            self.stdout.write(f"\nÚltimas 5 transacciones:")
            for trans in transacciones:
                tipo_icon = "📥" if trans.tipo == "entrada" else "📤"
                self.stdout.write(f"  {tipo_icon} {trans.fecha.strftime('%d/%m/%Y %H:%M')} - {trans.tipo.upper()}: {trans.cantidad}")
            
            # Detectar problemas
            problemas = []
            
            if producto.tiene_vencimiento and producto.stock > 0 and lotes.count() == 0:
                problemas.append("❌ Producto con vencimiento tiene stock pero no tiene lotes")
            
            if producto.tiene_vencimiento and producto.stock != total_stock_lotes:
                problemas.append(f"❌ Desincronización: Stock producto ({producto.stock}) ≠ Stock lotes ({total_stock_lotes})")
            
            if not problemas:
                self.stdout.write(self.style.SUCCESS("\n✅ No se encontraron problemas"))
                return
            
            # Mostrar problemas
            self.stdout.write(self.style.ERROR("\n🚨 PROBLEMAS DETECTADOS:"))
            for problema in problemas:
                self.stdout.write(self.style.ERROR(problema))
            
            if corregir:
                self.stdout.write(self.style.WARNING("\n🔧 APLICANDO CORRECCIONES..."))
                
                if producto.tiene_vencimiento and producto.stock > 0 and lotes.count() == 0:
                    # El producto debería tener lotes pero no los tiene
                    # Esto puede suceder si se agregó stock sin crear lotes apropiadamente
                    self.stdout.write("Recreando lote con el stock actual...")
                    
                    # Crear un lote con todo el stock actual
                    lote = LoteProducto.objects.create(
                        producto=producto,
                        numero_lote=1,
                        fecha_vencimiento=producto.fecha_vencimiento,
                        stock=producto.stock
                    )
                    self.stdout.write(f"✅ Lote #{lote.numero_lote} creado con {lote.stock} unidades")
                
                elif producto.tiene_vencimiento and producto.stock != total_stock_lotes:
                    # Sincronizar stock
                    producto.stock = total_stock_lotes
                    producto.save()
                    self.stdout.write(f"✅ Stock sincronizado a {producto.stock}")
                
                self.stdout.write(self.style.SUCCESS("🎉 Correcciones aplicadas exitosamente"))
                
            else:
                self.stdout.write(self.style.WARNING("\n💡 Para corregir automáticamente, use: --corregir"))
                
        except Producto.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"❌ Producto con código {codigo} no encontrado")
            )
