from django import forms
from django.core.validators import RegexValidator, MinValueValidator
from django.core.exceptions import ValidationError
from .models import Producto, Transaccion, ActaEntrega, Funcionario

def calcularDigitoVerificador(rut):
    cuerpo = rut
    suma = 0
    multiplo = 2
    for i in range(len(cuerpo) - 1, -1, -1):
        suma += int(cuerpo[i]) * multiplo
        multiplo = multiplo + 1 if multiplo < 7 else 2
    resto = suma % 11
    dv = 11 - resto
    if dv == 10:
        return 'K'
    elif dv == 11:
        return '0'
    return str(dv)

class ProductoForm(forms.ModelForm):
    codigo_barra = forms.CharField(
        max_length=50,
        validators=[
            RegexValidator(
                regex=r'^\d+$',
                message='El código de barra solo puede contener números enteros.'
            )
        ],
        label='Código de Barra'
    )

    stock = forms.IntegerField(
        validators=[
            MinValueValidator(0, message='El stock no puede ser negativo.')
        ],
        label='Stock'
    )

    guia_despacho = forms.CharField(
        max_length=50,
        validators=[
            RegexValidator(
                regex=r'^\d+$',
                message='La guía de despacho solo puede contener números enteros.'
            )
        ],
        label='Guía de Despacho'
    )

    numero_factura = forms.CharField(
        max_length=50,
        required=False,
        validators=[
            RegexValidator(
                regex=r'^\d+$',
                message='El número de factura solo puede contener números enteros.'
            )
        ],
        label='Número de Factura'
    )

    orden_compra = forms.CharField(
        max_length=50,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9\-]+$',
                message='La orden de compra solo puede contener letras, números y guiones.'
            )
        ],
        label='Orden de Compra'
    )

    rut_proveedor = forms.CharField(
        max_length=12,
        label='Rut del Proveedor',
        required=True
    )

    categoria = forms.ChoiceField(
        choices=[('', 'Seleccione una categoría')] + Producto.CATEGORIAS,
        label='Categoría',
        required=True,
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'})
    )

    class Meta:
        model = Producto
        fields = ['codigo_barra', 'descripcion', 'stock', 'categoria', 'rut_proveedor', 'guia_despacho', 'numero_factura', 'orden_compra']

    def clean_categoria(self):
        categoria = self.cleaned_data.get('categoria')
        if not categoria:
            raise ValidationError('Debe seleccionar una categoría.')
        return categoria

class TransaccionForm(forms.ModelForm):
    cantidad = forms.IntegerField(
        validators=[
            MinValueValidator(1, message='La cantidad debe ser un número positivo.')
        ],
        label='Cantidad'
    )

    rut_proveedor = forms.CharField(
        max_length=12,
        label='RUT del Proveedor',
        required=False
    )

    guia_despacho = forms.CharField(
        max_length=50,
        required=False,
        validators=[
            RegexValidator(
                regex=r'^\d+$',
                message='La guía de despacho solo puede contener números enteros.'
            )
        ],
        label='Guía de Despacho'
    )

    numero_factura = forms.CharField(
        max_length=50,
        required=False,
        validators=[
            RegexValidator(
                regex=r'^\d+$',
                message='El número de factura solo puede contener números enteros.'
            )
        ],
        label='Número de Factura'
    )

    orden_compra = forms.CharField(
        max_length=50,
        required=False,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9\-]+$',
                message='La orden de compra solo puede contener letras, números y guiones.'
            )
        ],
        label='Orden de Compra'
    )

    class Meta:
        model = Transaccion
        fields = ['cantidad', 'rut_proveedor', 'guia_despacho', 'numero_factura', 'orden_compra']

    def clean_rut_proveedor(self):
        rut = self.cleaned_data.get('rut_proveedor')
        if not rut:
            return rut

        rut = rut.replace('.', '').replace(' ', '').upper()
        print(f"Raw RUT input (TransaccionForm): {rut}")

        parts = rut.split('-')
        if len(parts) != 2:
            raise ValidationError('El RUT debe incluir un guion (formato XXXXXXXX-X).')
        body = parts[0]
        dv = parts[1]

        if not body.isdigit() or len(body) < 1 or len(body) > 8:
            raise ValidationError('El cuerpo del RUT debe contener entre 1 y 8 dígitos.')

        calculated_dv = calcularDigitoVerificador(body)
        print(f"Body: {body}, Calculated DV: {calculated_dv}, Input DV: {dv}")
        if dv not in '0123456789K' or dv != calculated_dv:
            raise ValidationError('El dígito verificador no es válido para este RUT.')

        return rut

class ActaEntregaForm(forms.ModelForm):
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

    departamento = forms.ChoiceField(
        choices=DEPARTAMENTOS,
        label='Departamento'
    )

    responsable = forms.ChoiceField(
        label='Responsable',
        choices=[]  # Inicialmente vacío, se llenará dinámicamente
    )

    class Meta:
        model = ActaEntrega
        fields = ['departamento', 'responsable']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inicialmente, el campo responsable tiene una opción por defecto
        self.fields['responsable'].choices = [('', 'Seleccione un departamento primero')]

        # Si se ha enviado un departamento (en un POST), generamos las opciones de responsable
        if 'departamento' in self.data:
            try:
                departamento = self.data.get('departamento')
                # Generamos las opciones de responsable dinámicamente
                responsables = [
                    ('Jefatura ' + departamento, 'Jefatura ' + departamento),
                    ('Jefatura ' + departamento + '(s)', 'Jefatura ' + departamento + '(s)'),
                    ('Secretaria ' + departamento, 'Secretaria ' + departamento),
                    ('Secretaria ' + departamento + '(s)', 'Secretaria ' + departamento + '(s)'),
                ]

                # Ajustes específicos para el Departamento de Salud Pública
                if departamento == 'Departamento de Salud Pública':
                    responsables = [
                        ('Jefe Salud Pública', 'Jefe Salud Pública'),
                        ('Jefe Salud Pública(s)', 'Jefe Salud Pública(s)'),
                        ('Secretaria Subrogante Salud Pública', 'Secretaria Subrogante Salud Pública'),
                        ('Secretaria Subrogante Salud Pública(s)', 'Secretaria Subrogante Salud Pública(s)'),
                    ]

                self.fields['responsable'].choices = responsables
            except (ValueError, TypeError):
                pass

    def clean(self):
        cleaned_data = super().clean()
        departamento = cleaned_data.get('departamento')
        responsable = cleaned_data.get('responsable')

        if not departamento:
            raise ValidationError('Debe seleccionar un departamento.')

        if not responsable:
            raise ValidationError('Debe seleccionar un responsable.')

        # Validamos que el responsable sea una opción válida para el departamento seleccionado
        responsables = [
            ('Jefatura ' + departamento, 'Jefatura ' + departamento),
            ('Jefatura ' + departamento + '(s)', 'Jefatura ' + departamento + '(s)'),
            ('Secretaria ' + departamento, 'Secretaria ' + departamento),
            ('Secretaria ' + departamento + '(s)', 'Secretaria ' + departamento + '(s)'),
        ]

        if departamento == 'Departamento de Salud Pública':
            responsables = [
                ('Jefe Salud Pública', 'Jefe Salud Pública'),
                ('Jefe Salud Pública(s)', 'Jefe Salud Pública(s)'),
                ('Secretaria Subrogante Salud Pública', 'Secretaria Subrogante Salud Pública'),
                ('Secretaria Subrogante Salud Pública(s)', 'Secretaria Subrogante Salud Pública(s)'),
            ]

        # Verificamos que el responsable esté en la lista de opciones válidas
        if responsable and (responsable, responsable) not in responsables:
            raise ValidationError({
                'responsable': f'Escoja una opción válida. "{responsable}" no es una de las opciones disponibles.'
            })

        return cleaned_data