# Generated by Django 5.1.7 on 2025-03-18 16:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='producto',
            name='codigo_barra',
            field=models.CharField(error_messages={'unique': 'Este Código de Barra ya existe. Por favor, ingrese un valor diferente.'}, max_length=50, unique=True, verbose_name='Código de Barra'),
        ),
    ]
