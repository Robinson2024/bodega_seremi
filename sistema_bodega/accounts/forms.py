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

    class Meta:
        model = Producto
        fields = ['codigo_barra', 'descripcion', 'stock', 'categoria', 'rut_proveedor', 'guia_despacho', 'numero_factura', 'orden_compra']

    def clean_rut_proveedor(self):
        rut = self.cleaned_data.get('rut_proveedor')
        if not rut:
            raise ValidationError('El RUT del proveedor es obligatorio.')

        rut = rut.replace('.', '').replace(' ', '').upper()
        print(f"Raw RUT input: {rut}")

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

    observacion = forms.CharField(
        widget=forms.Textarea,
        required=False,
        label='Observación'
    )

    class Meta:
        model = Transaccion
        fields = ['cantidad', 'rut_proveedor', 'guia_despacho', 'numero_factura', 'orden_compra', 'observacion']

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

class SalidaProductoForm(forms.Form):
    codigo_barra = forms.CharField(
        max_length=50,
        widget=forms.HiddenInput(),
        label='Código de Barra'
    )

    numero_siscom = forms.CharField(
        max_length=50,
        validators=[
            RegexValidator(
                regex=r'^\d+$',
                message='El número de Siscom solo puede contener números enteros.'
            )
        ],
        label='Número de Siscom'
    )

    cantidad = forms.IntegerField(
        validators=[
            MinValueValidator(1, message='La cantidad debe ser un número positivo.')
        ],
        label='Cantidad'
    )

    observacion = forms.CharField(
        widget=forms.Textarea,
        max_length=300,
        required=False,
        label='Observación'
    )

    def __init__(self, *args, **kwargs):
        self.producto = kwargs.pop('producto', None)
        super().__init__(*args, **kwargs)

    def clean_cantidad(self):
        cantidad = self.cleaned_data.get('cantidad')
        codigo_barra = self.cleaned_data.get('codigo_barra')
        try:
            producto = Producto.objects.get(codigo_barra=codigo_barra)
            if cantidad > producto.stock:
                raise ValidationError(f'La cantidad a retirar ({cantidad}) no puede superar el stock actual ({producto.stock}).')
        except Producto.DoesNotExist:
            raise ValidationError('Producto no encontrado.')
        return cantidad

class ActaEntregaForm(forms.ModelForm):
    departamento = forms.ChoiceField(
        choices=Funcionario.DEPARTAMENTOS,
        label='Departamento'
    )

    funcionario = forms.ChoiceField(
        label='Funcionario'
    )

    jefe_subdepartamento = forms.ChoiceField(
        choices=[
            ('Jessica Bulnes', 'Jessica Bulnes'),
            ('Isolde Gotschlich', 'Isolde Gotschlich'),
        ],
        label='Jefe del Subdepartamento'
    )

    class Meta:
        model = ActaEntrega
        fields = ['departamento', 'funcionario', 'jefe_subdepartamento']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['funcionario'].choices = [('', 'Seleccione un departamento primero')]
        if 'departamento' in self.data:
            try:
                departamento = self.data.get('departamento')
                funcionarios = Funcionario.objects.filter(departamento=departamento, es_jefe=False)
                self.fields['funcionario'].choices = [(f.nombre, f.nombre) for f in funcionarios]
            except (ValueError, TypeError):
                pass