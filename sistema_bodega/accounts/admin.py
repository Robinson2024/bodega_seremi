from django.contrib import admin
from .models import Producto, Transaccion, ActaEntrega, Funcionario

# Personalizar la vista de Producto en el panel de administración
class ProductoAdmin(admin.ModelAdmin):
    # Define los campos que se mostrarán en la lista de productos en el panel de administración
    list_display = ('codigo_barra', 'descripcion', 'stock', 'categoria', 'rut_proveedor', 'guia_despacho', 'numero_factura', 'orden_compra')
    # Agrega un filtro lateral para la categoría, permitiendo filtrar productos por este campo
    list_filter = ('categoria',)  # Eliminamos 'fecha_ingreso' porque no existe
    # Habilita la búsqueda por código de barras y descripción del producto
    search_fields = ('codigo_barra', 'descripcion')
    # Establece el orden por defecto de los productos según el código de barras
    ordering = ('codigo_barra',)

# Personalizar la vista de Transaccion
class TransaccionAdmin(admin.ModelAdmin):
    # Define los campos que se mostrarán en la lista de transacciones, incluyendo observación para mayor claridad
    list_display = ('producto', 'tipo', 'cantidad', 'fecha', 'observacion')
    # Permite filtrar transacciones por tipo y fecha en el panel de administración
    list_filter = ('tipo', 'fecha')
    # Habilita la búsqueda por descripción y código de barras del producto asociado
    search_fields = ('producto__descripcion', 'producto__codigo_barra')
    # Ordena las transacciones por fecha en orden descendente (más recientes primero)
    ordering = ('-fecha',)

# Personalizar la vista de ActaEntrega
class ActaEntregaAdmin(admin.ModelAdmin):
    # Define los campos que se mostrarán en la lista de actas de entrega, usando 'responsable' y 'fecha' para consistencia
    list_display = ('numero_acta', 'producto', 'departamento', 'responsable', 'fecha', 'generador')
    # Permite filtrar actas por departamento y fecha en el panel de administración
    list_filter = ('departamento', 'fecha')  # Reemplazamos 'fecha_entrega' por 'fecha'
    # Habilita la búsqueda por número de acta, descripción del producto, departamento y responsable
    search_fields = ('numero_acta', 'producto__descripcion', 'departamento', 'responsable')
    # Ordena las actas por fecha en orden descendente (más recientes primero)
    ordering = ('-fecha',)  # Reemplazamos 'fecha_entrega' por 'fecha'

# Personalizar la vista de Funcionario
class FuncionarioAdmin(admin.ModelAdmin):
    # Define los campos que se mostrarán en la lista de funcionarios (nombre, departamento y si es jefe)
    list_display = ('nombre', 'departamento', 'es_jefe')
    # Permite filtrar funcionarios por departamento y si son jefes
    list_filter = ('departamento', 'es_jefe')
    # Habilita la búsqueda por nombre y departamento del funcionario
    search_fields = ('nombre', 'departamento')
    # Ordena los funcionarios alfabéticamente por nombre
    ordering = ('nombre',)

# Registrar los modelos con sus configuraciones personalizadas en el panel de administración de Django
admin.site.register(Producto, ProductoAdmin)
admin.site.register(Transaccion, TransaccionAdmin)
admin.site.register(ActaEntrega, ActaEntregaAdmin)
admin.site.register(Funcionario, FuncionarioAdmin)