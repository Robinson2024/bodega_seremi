from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

# Funciones para RUT
def clean_rut(rut):
    """Elimina puntos y guiones del RUT."""
    return ''.join(filter(str.isalnum, str(rut)))

def validate_rut(value):
    """Valida el dígito verificador de un RUT chileno."""
    cleaned_rut = clean_rut(value)
    
    if not cleaned_rut.isdigit():
        return  # Ignora validación para RUT no numérico (ej. Auditor2025)

    if len(cleaned_rut) < 2:
        raise ValidationError("RUT debe tener al menos 2 caracteres.")

    body, dv = cleaned_rut[:-1], cleaned_rut[-1].upper()
    if not body.isdigit():
        raise ValidationError("Cuerpo del RUT debe ser numérico.")

    total = 0
    factor = 2
    for digit in reversed(body):
        total += int(digit) * factor
        factor = factor + 1 if factor < 7 else 2
    expected_dv = 11 - (total % 11)
    expected_dv = 'K' if expected_dv == 10 else '0' if expected_dv == 11 else str(expected_dv)

    if dv != expected_dv:
        raise ValidationError("Dígito verificador incorrecto.")

# Modelo de usuario personalizado
class CustomUser(AbstractUser):
    rut = models.CharField(
        max_length=12, 
        unique=True, 
        validators=[validate_rut], 
        help_text="RUT sin puntos ni guiones (ej. 12345678K)"
    )
    nombre = models.CharField(max_length=100, verbose_name="Nombre completo")

    def save(self, *args, **kwargs):
        """Normaliza RUT y asigna username si no existe."""
        self.rut = clean_rut(self.rut)
        if not self.username:
            self.username = self.rut
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} ({self.rut})"

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        permissions = [
            ("can_access_admin", "Acceso al panel de administración"),
            ("can_manage_users", "Gestión de usuarios"),
            ("can_manage_departments", "Gestión de departamentos"),
            ("can_edit", "Edición de registros"),
        ]

# Modelos de inventario
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
    stock = models.IntegerField(default=0, db_index=True)
    categoria = models.CharField(max_length=100, choices=CATEGORIAS, blank=True)
    rut_proveedor = models.CharField(max_length=12, blank=True)
    guia_despacho = models.CharField(max_length=50, blank=True)
    numero_factura = models.CharField(max_length=50, blank=True)
    orden_compra = models.CharField(max_length=50, blank=True)

    def get_stock_category(self):
        """Clasifica stock: Sin Stock, Bajo, Medio, Alto."""
        if self.stock == 0:
            return "Sin Stock"
        elif 1 <= self.stock <= 10:
            return "Bajo"
        elif 11 <= self.stock <= 50:
            return "Medio"
        return "Alto"

    def __str__(self):
        return f"{self.descripcion} ({self.codigo_barra})"

    class Meta:
        indexes = [models.Index(fields=['stock'], name='idx_producto_stock')]

class Transaccion(models.Model):
    TIPO_CHOICES = [('entrada', 'Entrada'), ('salida', 'Salida')]

    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    cantidad = models.IntegerField()
    fecha = models.DateTimeField(auto_now_add=True)
    rut_proveedor = models.CharField(max_length=12, blank=True)
    guia_despacho = models.CharField(max_length=50, blank=True)
    numero_factura = models.CharField(max_length=50, blank=True)
    orden_compra = models.CharField(max_length=50, blank=True)
    observacion = models.TextField(blank=True, null=True)
    acta_entrega = models.ForeignKey('ActaEntrega', on_delete=models.SET_NULL, null=True, blank=True)

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
    numero_acta = models.IntegerField()
    departamento = models.CharField(max_length=100)
    responsable = models.ForeignKey(
        'Responsable', 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='actas_responsable', 
        verbose_name="Responsable"
    )
    fecha = models.DateTimeField(auto_now_add=True)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    generador = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='actas_generadas', 
        verbose_name="Generador"
    )
    numero_siscom = models.CharField(max_length=50, blank=True, null=True)
    observacion = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('numero_acta', 'producto')

    def __str__(self):
        return f"Acta N°{self.numero_acta} - {self.departamento}"

class Departamento(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class Responsable(models.Model):
    TIPO_RESPONSABLE = [
        ('Jefatura', 'Jefatura'),
        ('Jefatura Subrogante', 'Jefatura Subrogante'),
        ('Secretaria', 'Secretaria'),
        ('Secretaria Subrogante', 'Secretaria Subrogante'),
    ]

    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE, related_name='responsables')
    tipo = models.CharField(max_length=50, choices=TIPO_RESPONSABLE)
    nombre = models.CharField(max_length=100)

    class Meta:
        unique_together = ('departamento', 'tipo')

    def __str__(self):
        return f"{self.nombre} ({self.departamento.nombre})"