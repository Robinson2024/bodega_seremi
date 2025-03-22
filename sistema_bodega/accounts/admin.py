from django.contrib import admin
from .models import Producto, Transaccion, ActaEntrega, Funcionario

# Personalizar la vista de Producto en el panel de administración
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('codigo_barra', 'descripcion', 'stock', 'categoria', 'rut_proveedor', 'guia_despacho', 'numero_factura', 'orden_compra')  # Campos que se mostrarán en la lista
    list_filter = ('categoria',)  # Eliminamos 'fecha_ingreso' porque no existe
    search_fields = ('codigo_barra', 'descripcion')  # Campos por los que se puede buscar
    ordering = ('codigo_barra',)  # Ordenar por un campo que sí existe, como 'codigo_barra'

# Personalizar la vista de Transaccion
class TransaccionAdmin(admin.ModelAdmin):
    list_display = ('producto', 'tipo', 'cantidad', 'fecha', 'observacion')  # Añadimos 'observacion' para que sea más útil
    list_filter = ('tipo', 'fecha')
    search_fields = ('producto__descripcion', 'producto__codigo_barra')
    ordering = ('-fecha',)

# Personalizar la vista de ActaEntrega
class ActaEntregaAdmin(admin.ModelAdmin):
    list_display = ('numero_acta', 'producto', 'departamento', 'responsable', 'fecha', 'generador')  # Reemplazamos 'funcionario' por 'responsable' y 'fecha_entrega' por 'fecha'
    list_filter = ('departamento', 'fecha')  # Reemplazamos 'fecha_entrega' por 'fecha'
    search_fields = ('numero_acta', 'producto__descripcion', 'departamento', 'responsable')
    ordering = ('-fecha',)  # Reemplazamos 'fecha_entrega' por 'fecha'

# Personalizar la vista de Funcionario
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'departamento', 'es_jefe')
    list_filter = ('departamento', 'es_jefe')
    search_fields = ('nombre', 'departamento')
    ordering = ('nombre',)  # Ordenar por 'nombre' para que sea más intuitivo

# Registrar los modelos con sus configuraciones personalizadas
admin.site.register(Producto, ProductoAdmin)
admin.site.register(Transaccion, TransaccionAdmin)
admin.site.register(ActaEntrega, ActaEntregaAdmin)
admin.site.register(Funcionario, FuncionarioAdmin)