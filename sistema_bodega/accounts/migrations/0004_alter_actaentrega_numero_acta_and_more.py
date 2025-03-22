# Generated by Django 5.1.7 on 2025-03-22 22:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_actaentrega_numero_siscom_actaentrega_observacion'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actaentrega',
            name='numero_acta',
            field=models.IntegerField(),
        ),
        migrations.AlterUniqueTogether(
            name='actaentrega',
            unique_together={('numero_acta', 'producto')},
        ),
    ]
