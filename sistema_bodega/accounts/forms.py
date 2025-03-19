from django import forms
from django.core.validators import RegexValidator, MinValueValidator
from django.core.exceptions import ValidationError
from .models import Producto, Transaccion  # Añadimos Transaccion

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
        max_length=12,  # Para permitir formato con puntos (12.345.678-K)
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

        # Normalizar el formato: eliminar puntos, espacios y convertir a mayúsculas
        rut = rut.replace('.', '').replace(' ', '').upper()
        print(f"Raw RUT input: {rut}")  # Depuración: mostrar el RUT crudo

        parts = rut.split('-')
        if len(parts) != 2:
            raise ValidationError('El RUT debe incluir un guion (formato XXXXXXXX-X).')
        body = parts[0]
        dv = parts[1]

        # Validar longitud del cuerpo (1 a 8 dígitos)
        if not body.isdigit() or len(body) < 1 or len(body) > 8:
            raise ValidationError('El cuerpo del RUT debe contener entre 1 y 8 dígitos.')

        # Validar dígito verificador
        calculated_dv = calcularDigitoVerificador(body)
        print(f"Body: {body}, Calculated DV: {calculated_dv}, Input DV: {dv}")  # Depuración
        if dv not in '0123456789K' or dv != calculated_dv:
            raise ValidationError('El dígito verificador no es válido para este RUT.')

        return rut  # Devolvemos el RUT sin puntos, como XXXXXXXX-X

class TransaccionForm(forms.ModelForm):
    cantidad = forms.IntegerField(
        validators=[
            MinValueValidator(1, message='La cantidad debe ser un número positivo.')
        ],
        label='Cantidad'
    )

    rut_proveedor = forms.CharField(
        max_length=12,  # Para permitir formato con puntos (12.345.678-K)
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
            return rut  # Campo opcional, devolvemos vacío si no se ingresó

        # Normalizar el formato: eliminar puntos, espacios y convertir a mayúsculas
        rut = rut.replace('.', '').replace(' ', '').upper()
        print(f"Raw RUT input (TransaccionForm): {rut}")  # Depuración

        parts = rut.split('-')
        if len(parts) != 2:
            raise ValidationError('El RUT debe incluir un guion (formato XXXXXXXX-X).')
        body = parts[0]
        dv = parts[1]

        # Validar longitud del cuerpo (1 a 8 dígitos)
        if not body.isdigit() or len(body) < 1 or len(body) > 8:
            raise ValidationError('El cuerpo del RUT debe contener entre 1 y 8 dígitos.')

        # Validar dígito verificador
        calculated_dv = calcularDigitoVerificador(body)
        print(f"Body: {body}, Calculated DV: {calculated_dv}, Input DV: {dv}")  # Depuración
        if dv not in '0123456789K' or dv != calculated_dv:
            raise ValidationError('El dígito verificador no es válido para este RUT.')

        return rut  # Devolvemos el RUT sin puntos, como XXXXXXXX-X