from django.core.management.base import BaseCommand
from accounts.models import Producto
from django.db import models

class Command(BaseCommand):
    help = 'Sincroniza el stock de todos los productos con vencimiento con sus lotes correspondientes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--codigo',
            type=str,
            help='Código de barra específico para sincronizar. Si no se proporciona, sincroniza todos los productos con vencimiento.'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar qué se haría sin hacer cambios reales.'
        )

    def handle(self, *args, **options):
        codigo_especifico = options.get('codigo')
        dry_run = options.get('dry_run', False)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN: No se harán cambios reales'))
        
        if codigo_especifico:
            try:
                productos = [Producto.objects.get(codigo_barra=codigo_especifico)]
                self.stdout.write(f'Procesando producto específico: {codigo_especifico}')
            except Producto.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Producto con código {codigo_especifico} no encontrado'))
                return
        else:
            productos = Producto.objects.filter(tiene_vencimiento=True)
            self.stdout.write(f'Procesando {productos.count()} productos con vencimiento')
        
        productos_sincronizados = 0
        problemas_encontrados = 0
        
        for producto in productos:
            self.stdout.write(f'\n--- Procesando: {producto.descripcion} ({producto.codigo_barra}) ---')
            
            # Stock actual del producto
            stock_producto = producto.stock
            
            # Limpiar lotes vacíos
            if not dry_run:
                producto.limpiar_lotes_vacios()
            
            # Stock desde lotes
            stock_lotes = producto.lotes.aggregate(total=models.Sum('stock'))['total'] or 0
            
            self.stdout.write(f'Stock en producto: {stock_producto}')
            self.stdout.write(f'Stock en lotes: {stock_lotes}')
            
            if stock_producto != stock_lotes:
                self.stdout.write(self.style.WARNING(f'⚠️  DESINCRONIZACIÓN detectada: {stock_producto} vs {stock_lotes}'))
                
                if not dry_run:
                    producto.stock = stock_lotes
                    producto.save()
                    self.stdout.write(self.style.SUCCESS(f'✅ Sincronizado: {producto.stock} unidades'))
                    productos_sincronizados += 1
                else:
                    self.stdout.write(f'[DRY-RUN] Se corregiría a: {stock_lotes} unidades')
                    productos_sincronizados += 1
                    
                problemas_encontrados += 1
            else:
                self.stdout.write(self.style.SUCCESS('✅ Stock ya sincronizado'))
            
            # Mostrar lotes activos
            lotes_activos = producto.lotes.filter(stock__gt=0)
            if lotes_activos.exists():
                self.stdout.write('Lotes activos:')
                for lote in lotes_activos:
                    estado = lote.get_estado_vencimiento()
                    self.stdout.write(f'  Lote #{lote.numero_lote}: {lote.stock} unidades - {estado} (vence {lote.fecha_vencimiento})')
            else:
                self.stdout.write('Sin lotes activos')
        
        # Resumen final
        self.stdout.write(f'\n=== RESUMEN ===')
        self.stdout.write(f'Productos procesados: {len(productos)}')
        self.stdout.write(f'Problemas encontrados: {problemas_encontrados}')
        
        if dry_run:
            self.stdout.write(f'Productos que se sincronizarían: {productos_sincronizados}')
            self.stdout.write(self.style.WARNING('Para aplicar los cambios, ejecute sin --dry-run'))
        else:
            self.stdout.write(f'Productos sincronizados: {productos_sincronizados}')
            if productos_sincronizados > 0:
                self.stdout.write(self.style.SUCCESS('✅ Sincronización completada'))
            else:
                self.stdout.write(self.style.SUCCESS('✅ Todos los productos ya estaban sincronizados'))
