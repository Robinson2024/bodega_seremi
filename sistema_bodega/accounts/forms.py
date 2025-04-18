from django import forms
from django.core.validators import RegexValidator, MinValueValidator
from django.core.exceptions import ValidationError
from .models import Producto, Transaccion, ActaEntrega, Funcionario, Departamento, Responsable, CustomUser, clean_rut, validate_rut
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import Group

# Formularios para la gestión de usuarios
class SearchUserForm(forms.Form):
    rut = forms.CharField(
        label='RUT',
        max_length=12,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Buscar por RUT...', 'class': 'form-control'}),
    )
    nombre = forms.CharField(
        label='Nombre',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Buscar por nombre...', 'class': 'form-control'}),
    )
    rol = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        label='Rol',
        required=False,
        empty_label='Todos los roles',
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_rol'}),
    )

    def clean_rol(self):
        """Convierte el valor del campo rol en el nombre del grupo (str) o None si no se seleccionó."""
        rol = self.cleaned_data.get('rol')
        return rol.name if rol else None

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        label='Email',
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )
    grupo = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        label="Rol",
        help_text="Seleccione el rol del usuario (Administrador, Usuario de Bodega, Auditor).",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_grupo'}),
    )

    class Meta:
        model = CustomUser
        fields = ('rut', 'nombre', 'email', 'grupo', 'password1', 'password2')
        labels = {
            'rut': 'RUT',
            'nombre': 'Nombre completo',
        }
        widgets = {
            'rut': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
        }

    def clean_rut(self):
        rut = self.cleaned_data.get('rut')
        cleaned_rut = clean_rut(rut)
        validate_rut(cleaned_rut)
        if CustomUser.objects.filter(rut=cleaned_rut).exists():
            raise forms.ValidationError("Este RUT ya está registrado.")
        return cleaned_rut

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            # Asignar el grupo seleccionado al usuario
            grupo = self.cleaned_data.get('grupo')
            if grupo:
                user.groups.add(grupo)
        return user

class CustomUserEditForm(UserChangeForm):
    # Eliminamos 'password = None' para permitir manejar contraseñas
    email = forms.EmailField(
        label='Email',
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )
    grupo = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        label="Rol",
        help_text="Seleccione el rol del usuario (Administrador, Usuario de Bodega, Auditor).",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_grupo'}),
    )
    # Nuevos campos para la contraseña
    password = forms.CharField(
        label="Nueva Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text="Deje en blanco si no desea cambiar la contraseña."
    )
    password_confirm = forms.CharField(
        label="Confirmar Nueva Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text="Repita la nueva contraseña para confirmar."
    )

    class Meta:
        model = CustomUser
        fields = ('rut', 'nombre', 'email', 'grupo', 'is_active')
        labels = {
            'rut': 'RUT',
            'nombre': 'Nombre completo',
            'is_active': 'Activo',
        }
        widgets = {
            'rut': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_rut(self):
        rut = self.cleaned_data.get('rut')
        cleaned_rut = clean_rut(rut)
        validate_rut(cleaned_rut)
        # Verificar si el RUT ya existe para otro usuario
        current_user = self.instance
        if CustomUser.objects.exclude(pk=current_user.pk).filter(rut=cleaned_rut).exists():
            raise forms.ValidationError("Este RUT ya está registrado por otro usuario.")
        return cleaned_rut

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        # Validar que las contraseñas coincidan si se proporciona una nueva contraseña
        if password or password_confirm:
            if password != password_confirm:
                self.add_error('password_confirm', "Las contraseñas no coinciden.")
            elif len(password) < 8:
                self.add_error('password', "La contraseña debe tener al menos 8 caracteres.")
        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Establecer el grupo inicial del usuario
        if self.instance and self.instance.pk:
            groups = self.instance.groups.all()
            if groups.exists():
                self.fields['grupo'].initial = groups.first()

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            # Actualizar el grupo del usuario
            grupo = self.cleaned_data.get('grupo')
            if grupo:
                # Limpiar los grupos existentes y asignar el nuevo
                user.groups.clear()
                user.groups.add(grupo)
        return user

# Formularios existentes
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

    responsable = forms.ModelChoiceField(
        queryset=Responsable.objects.all(),
        label='Responsable',
        empty_label='Seleccione un responsable',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = ActaEntrega
        fields = ['departamento', 'responsable']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Cargar solo departamentos activos
        departamentos = Departamento.objects.filter(activo=True)
        print("Departamentos cargados en ActaEntregaForm:", list(departamentos))
        self.fields['departamento'].choices = [('', 'Seleccione un departamento')] + [(d.nombre, d.nombre) for d in departamentos]

        # Filtrar responsables según el departamento seleccionado (si hay datos en POST)
        if 'departamento' in self.data:
            try:
                departamento_nombre = self.data.get('departamento')
                if departamento_nombre:
                    departamento_obj = Departamento.objects.get(nombre=departamento_nombre, activo=True)
                    self.fields['responsable'].queryset = Responsable.objects.filter(departamento=departamento_obj)
                else:
                    self.fields['responsable'].queryset = Responsable.objects.none()
            except Departamento.DoesNotExist:
                self.fields['responsable'].queryset = Responsable.objects.none()
        else:
            self.fields['responsable'].queryset = Responsable.objects.none()

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
        except Departamento.DoesNotExist:
            raise ValidationError('El departamento seleccionado no existe o no está activo.')

        # Validar que el responsable pertenece al departamento seleccionado
        if responsable and responsable.departamento.nombre != departamento:
            raise ValidationError('El responsable seleccionado no pertenece al departamento.')

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