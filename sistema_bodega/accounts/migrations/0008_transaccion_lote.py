import re

from django.db import migrations, models
import django.db.models.deletion


def backfill_lote_transacciones(apps, schema_editor):
    Transaccion = apps.get_model('accounts', 'Transaccion')
    LoteProducto = apps.get_model('accounts', 'LoteProducto')

    for transaccion in Transaccion.objects.filter(tipo='entrada', lote__isnull=True).iterator():
        observacion = transaccion.observacion or ''
        match = re.search(r'Lote\s*#\s*(\d+)', observacion)
        lote = None
        if match:
            lote = LoteProducto.objects.filter(
                producto_id=transaccion.producto_id,
                numero_lote=int(match.group(1)),
            ).first()
        if lote is None:
            lotes = list(LoteProducto.objects.filter(producto_id=transaccion.producto_id))
            if len(lotes) == 1:
                lote = lotes[0]
        if lote is not None:
            transaccion.lote = lote
            transaccion.save(update_fields=['lote'])


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_alter_loteproducto_numero_lote_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaccion',
            name='lote',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='transacciones',
                to='accounts.loteproducto',
                verbose_name='Lote asociado',
            ),
        ),
        migrations.RunPython(backfill_lote_transacciones, migrations.RunPython.noop),
    ]
