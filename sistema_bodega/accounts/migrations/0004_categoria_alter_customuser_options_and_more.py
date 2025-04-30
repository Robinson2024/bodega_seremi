from django.db import migrations, models
import django.db.models.deletion

# Lista de categorías estáticas originales
CATEGORIAS_ESTATICAS = [
    ('Insumos de Aseo', 'Insumos de Aseo'),
    ('Insumos de Escritorio', 'Insumos de Escritorio'),
    ('EPP', 'EPP'),
    ('Emergencias y Desastres', 'Emergencias y Desastres'),
    ('Folletería', 'Folletería'),
    ('Otros', 'Otros'),
]

def transferir_categorias(apps, schema_editor):
    # Obtener los modelos históricos
    Categoria = apps.get_model('accounts', 'Categoria')
    Producto = apps.get_model('accounts', 'Producto')

    # Crear un diccionario para mapear nombres de categorías estáticas a sus nuevos IDs
    categoria_mapping = {}

    # Crear registros en Categoria para cada categoría estática
    for nombre, _ in CATEGORIAS_ESTATICAS:
        categoria = Categoria.objects.create(nombre=nombre, activo=True)
        categoria_mapping[nombre] = categoria.id

    # Obtener el ID de la categoría 'Otros' como valor por defecto
    otros_id = categoria_mapping.get('Otros')

    # Actualizar los productos existentes usando SQL crudo
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        # Obtener todos los productos con sus valores actuales de 'categoria'
        cursor.execute("SELECT id, categoria FROM accounts_producto")
        productos = cursor.fetchall()

        for producto_id, categoria_nombre in productos:
            # Obtener el ID de la categoría correspondiente
            categoria_id = categoria_mapping.get(categoria_nombre, otros_id)
            # Actualizar directamente la columna 'categoria' con el ID de la categoría
            cursor.execute(
                "UPDATE accounts_producto SET categoria = %s WHERE id = %s",
                [categoria_id, producto_id]
            )

def revertir_categorias(apps, schema_editor):
    # Obtener los modelos históricos
    Categoria = apps.get_model('accounts', 'Categoria')
    Producto = apps.get_model('accounts', 'Producto')

    # Revertir los productos a los valores originales (como CharField)
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        # Obtener todos los productos y sus categorías actuales
        cursor.execute("SELECT id, categoria FROM accounts_producto")
        productos = cursor.fetchall()

        for producto_id, categoria_id in productos:
            if categoria_id:
                try:
                    categoria = Categoria.objects.get(id=categoria_id)
                    cursor.execute(
                        "UPDATE accounts_producto SET categoria = %s WHERE id = %s",
                        [categoria.nombre, producto_id]
                    )
                except Categoria.DoesNotExist:
                    # Si la categoría no existe, asignar 'Otros'
                    cursor.execute(
                        "UPDATE accounts_producto SET categoria = %s WHERE id = %s",
                        ['Otros', producto_id]
                    )

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_alter_actaentrega_responsable'),
    ]

    operations = [
        migrations.CreateModel(
            name='Categoria',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100, unique=True)),
                ('activo', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Categoría',
                'verbose_name_plural': 'Categorías',
                'permissions': [('can_manage_categories', 'Can manage categories')],
            },
        ),
        migrations.RunPython(
            transferir_categorias,
            reverse_code=revertir_categorias,
        ),
        migrations.AlterField(
            model_name='Producto',
            name='categoria',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounts.Categoria'),
        ),
        # Operaciones adicionales que estaban en 0005_...
        migrations.AlterModelOptions(
            name='CustomUser',
            options={'ordering': ['nombre'], 'verbose_name': 'Usuario', 'verbose_name_plural': 'Usuarios'},
        ),
        migrations.AlterField(
            model_name='Categoria',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='CustomUser',
            name='rut',
            field=models.CharField(max_length=12, unique=True, verbose_name='RUT'),
        ),
        migrations.AlterField(
            model_name='Producto',
            name='stock',
            field=models.IntegerField(default=0, verbose_name='Stock'),
        ),
        migrations.AddIndex(
            model_name='Producto',
            index=models.Index(fields=['stock'], name='idx_producto_stock'),
        ),
    ]