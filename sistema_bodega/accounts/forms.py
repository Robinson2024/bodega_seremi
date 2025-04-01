from django import forms
from django.core.validators import RegexValidator, MinValueValidator
from django.core.exceptions import ValidationError
from .models import Producto, Transaccion, ActaEntrega, Funcionario, Departamento, Responsable

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
        label='Código de Barra',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    descripcion = forms.CharField(
        max_length=200,
        label='Descripción',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    stock = forms.IntegerField(
        validators=[
            MinValueValidator(0, message='El stock no puede ser negativo.')
        ],
        label='Stock',
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    guia_despacho = forms.CharField(
        max_length=50,
        validators=[
            RegexValidator(
                regex=r'^\d+$',
                message='La guía de despacho solo puede contener números enteros.'
            )
        ],
        label='Guía de Despacho',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
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
        label='Número de Factura',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    orden_compra = forms.CharField(
        max_length=50,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9\-]+$',
                message='La orden de compra solo puede contener letras, números y guiones.'
            )
        ],
        label='Orden de Compra',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    rut_proveedor = forms.CharField(
        max_length=12,
        label='Rut del Proveedor',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
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
        label='Cantidad',
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    rut_proveedor = forms.CharField(
        max_length=12,
        label='RUT del Proveedor',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
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
        label='Guía de Despacho',
        widget=forms.TextInput(attrs={'class': 'form-control'})
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
        label='Número de Factura',
        widget=forms.TextInput(attrs={'class': 'form-control'})
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
        label='Orden de Compra',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    observacion = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
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

class ActaEntregaForm(forms.ModelForm):
    departamento = forms.ChoiceField(
        choices=[],
        label='Departamento',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    responsable = forms.ChoiceField(
        label='Responsable',
        choices=[],
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    numero_siscom = forms.CharField(
        max_length=50,
        required=False,
        label='Número SISCOM',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    observacion = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False,
        label='Observación'
    )

    class Meta:
        model = ActaEntrega
        fields = ['departamento', 'responsable', 'numero_siscom', 'observacion']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Cargar solo departamentos activos
        departamentos = Departamento.objects.filter(activo=True)
        print("Departamentos cargados en ActaEntregaForm:", list(departamentos))
        self.fields['departamento'].choices = [('', 'Seleccione un departamento')] + [(d.nombre, d.nombre) for d in departamentos]
        self.fields['responsable'].choices = [('', 'Seleccione un departamento primero')]

        if 'departamento' in self.data:
            try:
                departamento_nombre = self.data.get('departamento')
                print(f"Departamento seleccionado en el formulario: {departamento_nombre}")
                departamento = Departamento.objects.get(nombre=departamento_nombre, activo=True)
                responsables = departamento.responsables.all()
                print(f"Responsables cargados para {departamento_nombre}: {[r.nombre for r in responsables]}")
                self.fields['responsable'].choices = [('', 'Seleccione un responsable')] + [(r.nombre, r.nombre) for r in responsables]
            except (ValueError, TypeError, Departamento.DoesNotExist) as e:
                print(f"Error al cargar responsables: {str(e)}")
                self.add_error('departamento', f"El departamento seleccionado no existe o no está activo: {str(e)}")

    def clean(self):
        cleaned_data = super().clean()
        departamento = cleaned_data.get('departamento')
        responsable = cleaned_data.get('responsable')

        print(f"Datos limpiados - Departamento: {departamento}, Responsable: {responsable}")

        if not departamento:
            raise ValidationError('Debe seleccionar un departamento.')

        if not responsable:
            raise ValidationError('Debe seleccionar un responsable.')

        try:
            departamento_obj = Departamento.objects.get(nombre=departamento, activo=True)
            responsables = departamento_obj.responsables.all()
            responsables_nombres = [r.nombre for r in responsables]
            print(f"Responsables disponibles para {departamento}: {responsables_nombres}")
            if responsable not in responsables_nombres:
                raise ValidationError({
                    'responsable': f'Escoja una opción válida. "{responsable}" no es una de las opciones disponibles. Opciones disponibles: {responsables_nombres}'
                })
        except Departamento.DoesNotExist:
            raise ValidationError('El departamento seleccionado no existe o no está activo.')

        return cleaned_data

class DepartamentoForm(forms.ModelForm):
    nombre = forms.CharField(
        max_length=100,
        label='Nombre del Departamento',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    jefatura = forms.CharField(
        max_length=100,
        required=False,
        label='Jefatura',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    jefatura_subrogante = forms.CharField(
        max_length=100,
        required=False,
        label='Jefatura Subrogante',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    secretaria = forms.CharField(
        max_length=100,
        required=False,
        label='Secretaria',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    secretaria_subrogante = forms.CharField(
        max_length=100,
        required=False,
        label='Secretaria Subrogante',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Departamento
        fields = ['nombre']

    def save(self, commit=True):
        departamento = super().save(commit=commit)
        if commit:
            jefatura = self.cleaned_data.get('jefatura') or f"Jefatura {departamento.nombre}"
            jefatura_subrogante = self.cleaned_data.get('jefatura_subrogante') or f"Jefatura {departamento.nombre}(s)"
            secretaria = self.cleaned_data.get('secretaria') or f"Secretaria {departamento.nombre}"
            secretaria_subrogante = self.cleaned_data.get('secretaria_subrogante') or f"Secretaria {departamento.nombre}(s)"

            Responsable.objects.create(departamento=departamento, tipo='Jefatura', nombre=jefatura)
            Responsable.objects.create(departamento=departamento, tipo='Jefatura Subrogante', nombre=jefatura_subrogante)
            Responsable.objects.create(departamento=departamento, tipo='Secretaria', nombre=secretaria)
            Responsable.objects.create(departamento=departamento, tipo='Secretaria Subrogante', nombre=secretaria_subrogante)

        return departamento

class ModificarDepartamentoForm(forms.Form):
    departamento = forms.ChoiceField(
        choices=[],
        label='Departamento a Modificar',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    nuevo_nombre = forms.CharField(
        max_length=100,
        label='Nuevo Nombre del Departamento',
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    jefatura = forms.CharField(
        max_length=100,
        required=False,
        label='Jefatura',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    jefatura_subrogante = forms.CharField(
        max_length=100,
        required=False,
        label='Jefatura Subrogante',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    secretaria = forms.CharField(
        max_length=100,
        required=False,
        label='Secretaria',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    secretaria_subrogante = forms.CharField(
        max_length=100,
        required=False,
        label='Secretaria Subrogante',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Cargar solo departamentos activos
        departamentos = Departamento.objects.filter(activo=True)
        print("Departamentos cargados en ModificarDepartamentoForm:", list(departamentos))
        choices = [('', 'Seleccione un departamento')] + [(d.nombre, d.nombre) for d in departamentos]
        print("Choices generados en ModificarDepartamentoForm:", choices)
        self.fields['departamento'].choices = choices

    def clean(self):
        cleaned_data = super().clean()
        departamento = cleaned_data.get('departamento')
        nuevo_nombre = cleaned_data.get('nuevo_nombre')

        if not departamento:
            raise ValidationError('Debe seleccionar un departamento.')

        if not nuevo_nombre:
            raise ValidationError('Debe ingresar un nuevo nombre para el departamento.')

        if Departamento.objects.exclude(nombre=departamento).filter(nombre=nuevo_nombre, activo=True).exists():
            raise ValidationError('Ya existe un departamento activo con ese nombre.')

        return cleaned_data

class EliminarDepartamentoForm(forms.Form):
    departamento = forms.ChoiceField(
        choices=[],
        label='Departamento a Deshabilitar',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Cargar solo departamentos activos
        departamentos = Departamento.objects.filter(activo=True)
        print("Departamentos cargados en EliminarDepartamentoForm:", list(departamentos))
        choices = [('', 'Seleccione un departamento')] + [(d.nombre, d.nombre) for d in departamentos]
        print("Choices generados en EliminarDepartamentoForm:", choices)
        self.fields['departamento'].choices = choices

    def clean(self):
        cleaned_data = super().clean()
        departamento = cleaned_data.get('departamento')

        if not departamento:
            raise ValidationError('Debe seleccionar un departamento.')

        return cleaned_data