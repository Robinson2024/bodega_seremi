from django.contrib import admin
from .models import Producto, Transaccion, ActaEntrega, Funcionario

# Personalizar la vista de Producto en el panel de administración
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('codigo_barra', 'descripcion', 'stock', 'categoria', 'rut_proveedor', 'guia_despacho', 'numero_factura', 'orden_compra')  # Campos que se mostrarán en la lista
    list_filter = ('categoria', 'fecha_ingreso')  # Filtros en la barra lateral
    search_fields = ('codigo_barra', 'descripcion')  # Campos por los que se puede buscar
    ordering = ('-fecha_ingreso',)  # Ordenar por fecha de ingreso descendente

# Personalizar la vista de Transaccion
class TransaccionAdmin(admin.ModelAdmin):
    list_display = ('producto', 'tipo', 'cantidad', 'fecha')
    list_filter = ('tipo', 'fecha')
    search_fields = ('producto__descripcion', 'producto__codigo_barra')
    ordering = ('-fecha',)

# Personalizar la vista de ActaEntrega
class ActaEntregaAdmin(admin.ModelAdmin):
    list_display = ('numero_acta', 'producto', 'departamento', 'funcionario', 'fecha_entrega')
    list_filter = ('departamento', 'fecha_entrega')
    search_fields = ('numero_acta', 'producto__descripcion')
    ordering = ('-fecha_entrega',)

# Personalizar la vista de Funcionario
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'departamento', 'es_jefe')
    list_filter = ('departamento', 'es_jefe')
    search_fields = ('nombre', 'departamento')

# Registrar los modelos con sus configuraciones personalizadas
admin.site.register(Producto, ProductoAdmin)
admin.site.register(Transaccion, TransaccionAdmin)
admin.site.register(ActaEntrega, ActaEntregaAdmin)
admin.site.register(Funcionario, FuncionarioAdmin)