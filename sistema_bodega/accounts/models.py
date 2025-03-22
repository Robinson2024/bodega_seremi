from django.db import models

class Producto(models.Model):
    CATEGORIAS = [
        ('Insumos de Aseo', 'Insumos de Aseo'),
        ('Insumos de Escritorio', 'Insumos de Escritorio'),
        ('EPP', 'EPP'),
        ('Emergencias y Desastres', 'Emergencias y Desastres'),
        ('Folletería', 'Folletería'),
        ('Otros', 'Otros'),
    ]

    codigo_barra = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=200)
    stock = models.IntegerField(default=0)
    categoria = models.CharField(max_length=100, choices=CATEGORIAS, blank=True)
    rut_proveedor = models.CharField(max_length=12, blank=True)
    guia_despacho = models.CharField(max_length=50, blank=True)
    numero_factura = models.CharField(max_length=50, blank=True)
    orden_compra = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.descripcion} ({self.codigo_barra})"

class Transaccion(models.Model):
    TIPO_CHOICES = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
    ]

    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    cantidad = models.IntegerField()
    fecha = models.DateTimeField(auto_now_add=True)
    rut_proveedor = models.CharField(max_length=12, blank=True)
    guia_despacho = models.CharField(max_length=50, blank=True)
    numero_factura = models.CharField(max_length=50, blank=True)
    orden_compra = models.CharField(max_length=50, blank=True)
    observacion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.tipo} - {self.producto.descripcion} - {self.cantidad}"

class Funcionario(models.Model):
    DEPARTAMENTOS = [
        ('Seremi de Salud', 'Seremi de Salud'),
        ('Gabinete', 'Gabinete'),
        ('Departamento Jurídico', 'Departamento Jurídico'),
        ('Compin Cautín', 'Compin Cautín'),
        ('Departamento de Acción Sanitaria (DAS)', 'Departamento de Acción Sanitaria (DAS)'),
        ('Departamento de Administración y Finanzas (DAF)', 'Departamento de Administración y Finanzas (DAF)'),
        ('Departamento de Gestión y Desarrollo de Personas', 'Departamento de Gestión y Desarrollo de Personas'),
        ('Departamento de Salud Pública', 'Departamento de Salud Pública'),
        ('Oficina Provincial Malleco (OPM)', 'Oficina Provincial Malleco (OPM)'),
    ]

    nombre = models.CharField(max_length=100)
    departamento = models.CharField(max_length=100, choices=DEPARTAMENTOS)
    es_jefe = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.nombre} - {self.departamento}"

class ActaEntrega(models.Model):
    numero_acta = models.IntegerField()  # Eliminamos unique=True
    departamento = models.CharField(max_length=100)
    responsable = models.CharField(max_length=100)
    fecha = models.DateTimeField(auto_now_add=True)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    generador = models.CharField(max_length=100)
    numero_siscom = models.CharField(max_length=50, blank=True, null=True)
    observacion = models.TextField(blank=True, null=True)

    class Meta:
        # Añadimos una restricción de unicidad combinada entre numero_acta y producto
        unique_together = ('numero_acta', 'producto')

    def __str__(self):
        return f"Acta N°{self.numero_acta} - {self.departamento}"