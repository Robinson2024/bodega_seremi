import os
import sys
import django
import random
from faker import Faker
from django.utils.text import slugify

# Configurar el entorno de Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
django.setup()

from accounts.models import Producto

# Inicializar Faker
fake = Faker('es_CL')  # Usamos Faker en español (Chile) para datos más realistas

# Definir las categorías disponibles (basado en tu modelo Producto)
CATEGORIAS = [
    'Insumos de Aseo',
    'Insumos de Escritorio',
    'EPP',
    'Emergencias y Desastres',
    'Folletería',
    'Otros',
]

# Listas de palabras para generar descripciones de productos según la categoría
DESCRIPCIONES_POR_CATEGORIA = {
    'Insumos de Aseo': [
        'Detergente líquido', 'Jabón en barra', 'Esponja de limpieza', 'Desinfectante multiusos',
        'Toallas de papel', 'Bolsas de basura', 'Cloro en gel', 'Limpiavidrios',
        'Escoba de cerdas duras', 'Trapero de microfibra', 'Guantes de limpieza', 'Ambientador',
    ],
    'Insumos de Escritorio': [
        'Lápiz grafito', 'Bolígrafo azul', 'Cuaderno de 100 hojas', 'Carpeta de archivo',
        'Resma de papel A4', 'Marcador permanente', 'Cinta adhesiva', 'Tijeras de punta fina',
        'Clips de papel', 'Post-it 3x3', 'Grapadora pequeña', 'Perforadora de 2 agujeros',
    ],
    'EPP': [
        'Mascarilla N95', 'Guantes de nitrilo', 'Lentes de seguridad', 'Casco de protección',
        'Zapatos de seguridad', 'Chaleco reflectante', 'Protectores auditivos', 'Mascarilla KN95',
        'Traje de bioseguridad', 'Alcohol gel 70%', 'Escudo facial', 'Guantes quirúrgicos',
    ],
    'Emergencias y Desastres': [
        'Linterna LED', 'Botiquín de primeros auxilios', 'Manta térmica', 'Agua embotellada 1L',
        'Ración de comida de emergencia', 'Radio portátil', 'Silbato de emergencia', 'Cuerda de rescate',
        'Máscara de gas', 'Batería externa', 'Kit de herramientas básico', 'Carpa de emergencia',
    ],
    'Folletería': [
        'Folleto informativo A5', 'Tríptico de campaña', 'Afiche A3', 'Volante publicitario',
        'Manual de procedimientos', 'Guía de prevención', 'Cartilla educativa', 'Brochure institucional',
        'Tarjeta de presentación', 'Sticker informativo', 'Catálogo de servicios', 'Póster de sensibilización',
    ],
    'Otros': [
        'Caja de almacenamiento', 'Etiqueta adhesiva', 'Candado de seguridad', 'Pila AA',
        'Cable USB', 'Mouse óptico', 'Teclado USB', 'Botella reutilizable',
        'Taza personalizada', 'Llavero institucional', 'Pendrive 16GB', 'Calculadora básica',
    ],
}

def calcular_dv(rut):
    """Calcula el dígito verificador de un RUT chileno."""
    rut = str(rut)
    reversed_digits = map(int, reversed(rut))
    factors = [2, 3, 4, 5, 6, 7] * (len(rut) // 6 + 1)
    s = sum(d * f for d, f in zip(reversed_digits, factors))
    dv = 11 - (s % 11)
    if dv == 11:
        return '0'
    elif dv == 10:
        return 'K'
    return str(dv)

def generar_rut():
    """Genera un RUT chileno válido (sin puntos ni guión)."""
    numero = random.randint(5000000, 25000000)
    dv = calcular_dv(numero)
    return f"{numero}{dv}"

def generar_codigo_barra(existentes):
    """Genera un código de barra único de 5 dígitos."""
    while True:
        codigo = str(random.randint(10000, 99999))
        if codigo not in existentes:
            existentes.add(codigo)
            return codigo

def generar_producto(codigos_existentes):
    """Genera un producto aleatorio."""
    categoria = random.choice(CATEGORIAS)
    descripcion_base = random.choice(DESCRIPCIONES_POR_CATEGORIA[categoria])
    descripcion = f"{descripcion_base} {fake.word().capitalize()}"

    producto = {
        'codigo_barra': generar_codigo_barra(codigos_existentes),
        'descripcion': descripcion[:100],  # Limitar a 100 caracteres (ajusta según tu modelo)
        'stock': random.randint(10, 500),
        'categoria': categoria,
        'rut_proveedor': generar_rut() if random.random() > 0.2 else '',  # 80% de probabilidad de tener RUT
        'guia_despacho': str(random.randint(1000, 9999)) if random.random() > 0.3 else '',  # 70% de probabilidad
        'numero_factura': str(random.randint(10000, 99999)) if random.random() > 0.3 else '',  # 70% de probabilidad
        'orden_compra': f"OC-{random.randint(100, 999)}-{fake.year()}" if random.random() > 0.3 else '',  # 70% de probabilidad
    }
    return producto

def main():
    print("Iniciando la generación de productos...")

    # Obtener códigos de barra existentes para evitar duplicados
    codigos_existentes = set(Producto.objects.values_list('codigo_barra', flat=True))

    # Generar 500 productos
    productos = []
    for _ in range(500):
        producto_data = generar_producto(codigos_existentes)
        productos.append(producto_data)

    # Insertar los productos en la base de datos
    try:
        for producto_data in productos:
            producto = Producto(
                codigo_barra=producto_data['codigo_barra'],
                descripcion=producto_data['descripcion'],
                stock=producto_data['stock'],
                categoria=producto_data['categoria'],
                rut_proveedor=producto_data['rut_proveedor'],
                guia_despacho=producto_data['guia_despacho'],
                numero_factura=producto_data['numero_factura'],
                orden_compra=producto_data['orden_compra'],
            )
            producto.save()
        print(f"¡Éxito! Se han añadido {len(productos)} productos a la base de datos.")
    except Exception as e:
        print(f"Error al añadir productos: {str(e)}")

if __name__ == "__main__":
    main()