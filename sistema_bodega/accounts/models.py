from django.db import models

# Modelo para los productos en la bodega
class Producto(models.Model):
    CATEGORIAS = (
        ('Insumos_Aseo', 'Insumos Aseo'),
        ('Insumos_Escritorio', 'Insumos Escritorio'),
        ('EPP', 'EPP'),
        ('Emergencias_y_Desastres', 'Emergencias y Desastres'),
        ('Folletoria', 'Folletoría'),
        ('Otros', 'Otros'),
    )
    codigo_barra = models.CharField(max_length=50, unique=True, verbose_name="Código de Barra")
    descripcion = models.CharField(max_length=200, verbose_name="Descripción")
    stock = models.IntegerField(default=0, verbose_name="Stock")
    categoria = models.CharField(max_length=50, choices=CATEGORIAS, verbose_name="Categoría")
    rut_proveedor = models.CharField(max_length=12, verbose_name="Rut del Proveedor")
    guia_despacho = models.CharField(max_length=50, verbose_name="Guía de Despacho")
    numero_factura = models.CharField(max_length=50, blank=True, null=True, verbose_name="Número de Factura")
    orden_compra = models.CharField(max_length=50, verbose_name="Orden de Compra")
    fecha_ingreso = models.DateField(auto_now_add=True, verbose_name="Fecha de Ingreso")

    def __str__(self):
        return f"{self.descripcion} (Código: {self.codigo_barra})"

# Modelo para registrar transacciones (entradas y salidas)
class Transaccion(models.Model):
    TIPO_TRANSACCION = (
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
    )
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, verbose_name="Producto")
    tipo = models.CharField(max_length=10, choices=TIPO_TRANSACCION, verbose_name="Tipo de Transacción")
    cantidad = models.IntegerField(verbose_name="Cantidad")
    rut_proveedor = models.CharField(max_length=12, blank=True, null=True, verbose_name="Rut del Proveedor")
    guia_despacho = models.CharField(max_length=50, blank=True, null=True, verbose_name="Guía de Despacho")
    numero_factura = models.CharField(max_length=50, blank=True, null=True, verbose_name="Número de Factura")
    orden_compra = models.CharField(max_length=50, blank=True, null=True, verbose_name="Orden de Compra")
    fecha = models.DateField(auto_now_add=True, verbose_name="Fecha")
    observacion = models.TextField(blank=True, null=True, verbose_name="Observación")

    def __str__(self):
        return f"{self.tipo} - {self.producto.descripcion} ({self.cantidad})"

# Modelo para las actas de entrega
class ActaEntrega(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, verbose_name="Producto")
    numero_acta = models.IntegerField(verbose_name="Número de Acta")
    fecha_entrega = models.DateField(auto_now_add=True, verbose_name="Fecha de Entrega")
    departamento = models.CharField(max_length=100, verbose_name="Departamento")
    funcionario = models.CharField(max_length=100, verbose_name="Funcionario")
    jefe_subdepartamento = models.CharField(max_length=100, verbose_name="Jefe del Subdepartamento")
    cantidad = models.IntegerField(verbose_name="Cantidad Entregada")
    responsable = models.CharField(max_length=100, verbose_name="Responsable del Acta")

    def __str__(self):
        return f"Acta {self.numero_acta} - {self.producto.descripcion}"

# Modelo para los funcionarios
class Funcionario(models.Model):
    DEPARTAMENTOS = (
        ('Administracion_y_Finanzas', 'Departamento de Administración y Finanzas'),
        ('Accion_Sanitaria', 'Departamento de Acción Sanitaria'),
        ('Juridico', 'Departamento Jurídico'),
        ('Salud_Publica', 'Departamento de Salud Pública'),
        ('Compin_Cautin', 'Compin Cautín'),
        ('Compin_Malleco', 'Compin Malleco'),
        ('Seremi_de_Salud', 'Seremi de Salud'),
        ('Gestion_y_Desarrollo_Personas', 'Departamento de Gestión y Desarrollo de Personas'),
        ('Bodega', 'Departamento de Bodega'),
    )
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    departamento = models.CharField(max_length=50, choices=DEPARTAMENTOS, verbose_name="Departamento")
    es_jefe = models.BooleanField(default=False, verbose_name="Es Jefe")

    def __str__(self):
        return f"{self.nombre} - {self.departamento}"