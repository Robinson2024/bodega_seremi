from django.core.management.base import BaseCommand
from accounts.models import LoteProducto, Producto


class Command(BaseCommand):
    help = 'Limpia automáticamente los lotes con stock = 0 para evitar errores de UNIQUE constraint'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra qué se eliminaría sin realizar cambios',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write(
            self.style.SUCCESS('🧹 Iniciando limpieza de lotes vacíos...')
        )
        
        # Obtener lotes vacíos
        lotes_vacios = LoteProducto.objects.filter(stock=0)
        total_vacios = lotes_vacios.count()
        
        if total_vacios == 0:
            self.stdout.write(
                self.style.SUCCESS('✅ No hay lotes vacíos para eliminar.')
            )
            return
        
        self.stdout.write(f'📊 Se encontraron {total_vacios} lotes vacíos:')
        
        productos_afectados = set()
        for lote in lotes_vacios:
            productos_afectados.add(lote.producto)
            self.stdout.write(
                f'   - {lote.producto.codigo_barra} | Lote #{lote.numero_lote} | Stock: {lote.stock}'
            )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'🔍 DRY RUN: Se eliminarían {total_vacios} lotes de {len(productos_afectados)} productos.')
            )
            return
        
        # Eliminar lotes vacíos
        lotes_eliminados = lotes_vacios.delete()[0]
        self.stdout.write(
            self.style.SUCCESS(f'✅ Se eliminaron {lotes_eliminados} lotes vacíos.')
        )
        
        # Actualizar stock de productos afectados
        self.stdout.write('🔄 Actualizando stock de productos afectados...')
        for producto in productos_afectados:
            try:
                producto.actualizar_stock_total()
                self.stdout.write(f'   ✅ Stock actualizado para {producto.codigo_barra}')
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'   ❌ Error actualizando {producto.codigo_barra}: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'🎉 Limpieza completada! Eliminados: {lotes_eliminados} lotes, '
                f'Productos actualizados: {len(productos_afectados)}'
            )
        )
