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

    def _esta_en_grupos(self, *nombres):
        if not getattr(self, 'is_authenticated', False):
            return False
        if self.is_superuser:
            return True
        return self.groups.filter(name__in=nombres).exists()

    def es_admin_operativo(self):
        """Administrador o Administrador Auditor: menús de gestión."""
        return self._esta_en_grupos('Administrador', 'Administrador Auditor')

    def puede_operar_bodega(self):
        """Salidas, agregar stock y vencimientos."""
        return self._esta_en_grupos('Administrador', 'Administrador Auditor', 'Usuario de Bodega')

    def puede_corregir_ingreso(self):
        """Solo Administrador Auditor (jefe/informática) o superusuario."""
        return self._esta_en_grupos('Administrador Auditor')

    def puede_panel_admin(self):
        """Panel Django: solo Administrador Auditor o superusuario."""
        return self._esta_en_grupos('Administrador Auditor')

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
    codigo_barra = models.CharField(max_length=50, unique=True)

    @staticmethod
    def get_next_codigo_barra():
        """Obtiene el siguiente código de barra correlativo, partiendo desde 100000."""
        ultimo = Producto.objects.order_by('-codigo_barra').first()
        try:
            ultimo_num = int(ultimo.codigo_barra)
            if ultimo_num < 100000:
                return '100000'
            return str(ultimo_num + 1)
        except (AttributeError, ValueError):
            return '100000'

    def save(self, *args, **kwargs):
        # Asignar automáticamente el código de barra si no está definido
        if not self.codigo_barra:
            self.codigo_barra = Producto.get_next_codigo_barra()
        super().save(*args, **kwargs)
    descripcion = models.CharField(max_length=200)
    stock = models.IntegerField(default=0, db_index=True)
    categoria = models.ForeignKey('Categoria', on_delete=models.SET_NULL, null=True, blank=True)
    rut_proveedor = models.CharField(max_length=12, blank=True)
    guia_despacho = models.CharField(max_length=50, blank=True)
    numero_factura = models.CharField(max_length=50, blank=True)
    orden_compra = models.CharField(max_length=50, blank=True)
    # Campos para control de vencimiento
    tiene_vencimiento = models.BooleanField(default=False, verbose_name="¿Tiene fecha de vencimiento?")
    fecha_vencimiento = models.DateField(null=True, blank=True, verbose_name="Fecha de vencimiento")

    def get_stock_category(self):
        """Clasifica stock: Sin Stock, Bajo, Medio, Alto."""
        if self.stock == 0:
            return "Sin Stock"
        elif 1 <= self.stock <= 10:
            return "Bajo"
        elif 11 <= self.stock <= 50:
            return "Medio"
        return "Alto"

    def get_dias_para_vencer(self):
        """Calcula los días restantes hasta el vencimiento."""
        if not self.tiene_vencimiento or not self.fecha_vencimiento:
            return None
        from datetime import date
        hoy = date.today()
        return (self.fecha_vencimiento - hoy).days

    def get_estado_vencimiento(self):
        """Determina el estado de vencimiento del producto."""
        if not self.tiene_vencimiento or not self.fecha_vencimiento:
            return "Sin Vencimiento"
        
        dias_restantes = self.get_dias_para_vencer()
        
        if dias_restantes < 0:
            return "Vencido"
        elif dias_restantes == 0:
            return "Vence Hoy"
        elif dias_restantes <= 7:
            return "Crítico"
        elif dias_restantes <= 30:
            return "Precaución"
        else:
            return "Normal"

    def get_color_estado_vencimiento(self):
        """Retorna el color CSS para el estado de vencimiento."""
        estado = self.get_estado_vencimiento()
        colores = {
            'Vencido': '#dc3545',      # Rojo
            'Vence Hoy': '#fd7e14',    # Naranja oscuro
            'Crítico': '#ffc107',      # Amarillo
            'Precaución': '#28a745',   # Verde
            'Normal': '#6c757d',       # Gris
            'Sin Vencimiento': '#17a2b8'  # Azul info
        }
        return colores.get(estado, '#6c757d')

    def get_proximo_numero_lote(self):
        """Obtiene el siguiente número de lote automáticamente SIN eliminar lotes."""
        if not self.tiene_vencimiento:
            return None
        
        # SOLUCIÓN CORREGIDA: NO eliminar lotes, solo calcular el próximo número
        # Obtener el último número de lote usado (incluye lotes con stock=0 para preservar trazabilidad)
        ultimo_lote = self.lotes.aggregate(max_lote=models.Max('numero_lote'))['max_lote']
        return (ultimo_lote or 0) + 1

    def marcar_lotes_vencidos(self):
        """Marca lotes vencidos pero NO los elimina (preserva trazabilidad)."""
        try:
            from datetime import date
            hoy = date.today()
            
            # Solo marcar como información, NO eliminar
            lotes_vencidos = self.lotes.filter(
                fecha_vencimiento__lt=hoy,
                stock__gt=0  # Solo lotes vencidos que aún tienen stock
            )
            
            cantidad_vencidos = lotes_vencidos.count()
            
            if cantidad_vencidos > 0:
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Producto {self.codigo_barra}: {cantidad_vencidos} lotes vencidos con stock")
                
            return cantidad_vencidos
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error al marcar lotes vencidos del producto {self.codigo_barra}: {e}")
            return 0

    def crear_lote_automatico(self, cantidad, fecha_vencimiento, numero_lote_personalizado=None):
        """Crea un lote automáticamente con numeración secuencial o personalizada."""
        if not self.tiene_vencimiento:
            raise ValueError("No se pueden crear lotes para productos sin fecha de vencimiento")
        
        if numero_lote_personalizado:
            # Validar que el número de lote personalizado no exista
            if self.lotes.filter(numero_lote=numero_lote_personalizado).exists():
                raise ValueError(f"Ya existe un lote con el número {numero_lote_personalizado} para este producto")
            numero_lote = numero_lote_personalizado
        else:
            numero_lote = self.get_proximo_numero_lote()
            
        lote = LoteProducto.objects.create(
            producto=self,
            numero_lote=numero_lote,
            fecha_vencimiento=fecha_vencimiento,
            stock=cantidad
        )
        # El save del lote alinea producto.stock con la suma de lotes.
        self.refresh_from_db(fields=['stock'])
        return lote

    def agregar_lote(self, cantidad, fecha_vencimiento, numero_lote_personalizado=None):
        """Agrega un nuevo lote y stock a un producto existente de forma segura."""
        if not self.tiene_vencimiento:
            raise ValueError("No se pueden crear lotes para productos sin fecha de vencimiento")
        
        if numero_lote_personalizado:
            # Validar que el número de lote personalizado no exista
            if self.lotes.filter(numero_lote=numero_lote_personalizado).exists():
                raise ValueError(f"Ya existe un lote con el número {numero_lote_personalizado} para este producto")
            numero_lote = numero_lote_personalizado
        else:
            numero_lote = self.get_proximo_numero_lote()
            
        lote = LoteProducto.objects.create(
            producto=self,
            numero_lote=numero_lote,
            fecha_vencimiento=fecha_vencimiento,
            stock=cantidad
        )
        self.refresh_from_db(fields=['stock'])
        return lote

    def get_lotes_con_stock(self):
        """Obtiene todos los lotes que tienen stock, ordenados por fecha de vencimiento (FIFO)."""
        return self.lotes.filter(stock__gt=0).order_by('fecha_vencimiento')

    def get_lotes_vencidos_con_stock(self):
        """Obtiene lotes vencidos que aún tienen stock (requieren gestión manual)."""
        from datetime import date
        hoy = date.today()
        return self.lotes.filter(
            fecha_vencimiento__lt=hoy,
            stock__gt=0
        ).order_by('fecha_vencimiento')

    def reducir_stock_fifo(self, cantidad_reducir):
        """Reduce stock siguiendo el método FIFO (First In, First Out) SIN eliminar lotes."""
        if not self.tiene_vencimiento:
            # Si no tiene vencimiento, reducir del stock principal
            if self.stock >= cantidad_reducir:
                self.stock -= cantidad_reducir
                self.save()
                return True
            return False
        
        cantidad_restante = cantidad_reducir
        lotes_con_stock = self.get_lotes_con_stock()
        
        for lote in lotes_con_stock:
            if cantidad_restante <= 0:
                break
                
            if lote.stock >= cantidad_restante:
                # Este lote tiene suficiente stock
                lote.stock -= cantidad_restante
                lote.save(sync_producto=False)
                cantidad_restante = 0
            else:
                # Usar todo el stock de este lote y continuar con el siguiente
                cantidad_restante -= lote.stock
                lote.stock = 0
                lote.save(sync_producto=False)
        
        # Un solo recálculo al final: stock del producto = suma de lotes
        self.sincronizar_stock_con_lotes()
        
        # IMPORTANTE: NO llamar a limpiar_lotes_vacios() aquí
        # Los lotes con stock=0 se conservan para la trazabilidad del Bincard
        
        return cantidad_restante == 0

    def sincronizar_stock_con_lotes(self):
        """Alinea producto.stock con la suma de lotes (fuente de verdad si hay vencimiento)."""
        if not self.tiene_vencimiento:
            return False
        total_stock = self.lotes.aggregate(total=models.Sum('stock'))['total'] or 0
        if self.stock != total_stock:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Sincronizando stock del producto {self.codigo_barra}: {self.stock} → {total_stock}")
            self.stock = total_stock
            self.save(update_fields=['stock'])
            return True
        return False

    def stock_disponible(self):
        """Stock vigente para listados y salidas. Recalcula desde lotes si corresponde."""
        self.sincronizar_stock_con_lotes()
        return self.stock

    def get_estado_vencimiento_completo(self):
        """Obtiene el estado de vencimiento considerando TODOS los lotes."""
        if not self.tiene_vencimiento:
            return "Sin Vencimiento"
        
        if not self.lotes.filter(stock__gt=0).exists():
            # Si no hay lotes con stock, usar fecha del producto principal
            return self.get_estado_vencimiento()
        
        # Si hay lotes, obtener el estado del lote más crítico
        estados_peso = {'Vencido': 4, 'Vence Hoy': 3, 'Crítico': 2, 'Precaución': 1, 'Normal': 0}
        estado_mas_critico = 'Normal'
        peso_max = 0
        
        for lote in self.lotes.filter(stock__gt=0):
            estado_lote = lote.get_estado_vencimiento()
            peso_lote = estados_peso.get(estado_lote, 0)
            if peso_lote > peso_max:
                peso_max = peso_lote
                estado_mas_critico = estado_lote
        
        return estado_mas_critico

    def get_lotes_detalle(self):
        """Obtiene detalle de todos los lotes con información de vencimiento."""
        lotes_detalle = []
        for lote in self.lotes.all().order_by('fecha_vencimiento'):  # Incluye TODOS los lotes, incluso con stock=0
            lotes_detalle.append({
                'numero_lote': lote.numero_lote,
                'fecha_vencimiento': lote.fecha_vencimiento,
                'stock': lote.stock,
                'dias_restantes': lote.get_dias_para_vencer(),
                'estado': lote.get_estado_vencimiento(),
                'color': lote.get_color_estado_vencimiento(),
                'esta_vacio': lote.stock == 0,  # Indica si el lote está vacío
                'esta_vencido': lote.get_dias_para_vencer() < 0 if lote.get_dias_para_vencer() is not None else False
            })
        return lotes_detalle

    def get_lotes_activos_detalle(self):
        """Obtiene detalle solo de los lotes con stock > 0 para gestión."""
        lotes_detalle = []
        for lote in self.lotes.filter(stock__gt=0).order_by('fecha_vencimiento'):  # Solo lotes con stock
            lotes_detalle.append({
                'numero_lote': lote.numero_lote,
                'fecha_vencimiento': lote.fecha_vencimiento,
                'stock': lote.stock,
                'dias_restantes': lote.get_dias_para_vencer(),
                'estado': lote.get_estado_vencimiento(),
                'color': lote.get_color_estado_vencimiento(),
                'esta_vacio': False,  # Por definición, estos lotes no están vacíos
                'esta_vencido': lote.get_dias_para_vencer() < 0 if lote.get_dias_para_vencer() is not None else False
            })
        return lotes_detalle

    def get_total_lotes_activos(self):
        """Obtiene el número de lotes que tienen stock > 0."""
        return self.lotes.filter(stock__gt=0).count()

    def get_estadisticas_lotes(self):
        """Obtiene estadísticas completas de los lotes del producto."""
        if not self.tiene_vencimiento:
            return None
            
        total_lotes = self.lotes.count()
        lotes_con_stock = self.lotes.filter(stock__gt=0).count()
        lotes_vacios = self.lotes.filter(stock=0).count()
        lotes_vencidos_con_stock = self.get_lotes_vencidos_con_stock().count()
        
        from datetime import date, timedelta
        hoy = date.today()
        lotes_criticos = self.lotes.filter(
            fecha_vencimiento__lte=hoy + timedelta(days=7),
            fecha_vencimiento__gte=hoy,
            stock__gt=0
        ).count()
        
        return {
            'total_lotes': total_lotes,
            'lotes_con_stock': lotes_con_stock,
            'lotes_vacios': lotes_vacios,
            'lotes_vencidos_con_stock': lotes_vencidos_con_stock,
            'lotes_criticos': lotes_criticos,
            'stock_total': self.stock
        }

    def get_proximo_vencimiento(self):
        """Obtiene la fecha de vencimiento más próxima considerando todos los lotes."""
        if self.tiene_vencimiento and self.lotes.filter(stock__gt=0).exists():
            lote_proximo = self.lotes.filter(stock__gt=0).order_by('fecha_vencimiento').first()
            return lote_proximo.fecha_vencimiento if lote_proximo else None
        return self.fecha_vencimiento

    def get_info_proximo_lote(self):
        """Obtiene información sobre el próximo lote que se creará."""
        if not self.tiene_vencimiento:
            return None
        
        proximo_numero = self.get_proximo_numero_lote()
        lotes_activos = self.lotes.filter(stock__gt=0).count()
        lotes_vencidos = self.get_lotes_vencidos_con_stock().count()
        
        mensaje = f"Se creará el Lote #{proximo_numero}"
        if proximo_numero == 1:
            mensaje += " (primer lote del producto)"
        else:
            mensaje += f" ({lotes_activos} lotes activos"
            if lotes_vencidos > 0:
                mensaje += f", {lotes_vencidos} lotes vencidos con stock"
            mensaje += ")"
        
        return {
            'numero': proximo_numero,
            'es_primer_lote': proximo_numero == 1,
            'lotes_activos': lotes_activos,
            'lotes_vencidos': lotes_vencidos,
            'mensaje': mensaje
        }

    def __str__(self):
        return f"{self.descripcion} ({self.codigo_barra})"

    class Meta:
        indexes = [models.Index(fields=['stock'], name='idx_producto_stock')]

class LoteProducto(models.Model):
    """Modelo para manejar diferentes lotes de un mismo producto con fechas de vencimiento distintas."""
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='lotes')
    fecha_vencimiento = models.DateField(verbose_name="Fecha de vencimiento")
    stock = models.IntegerField(default=0, verbose_name="Stock del lote")
    fecha_ingreso = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de ingreso")
    numero_lote = models.IntegerField(verbose_name="Número de lote")
    
    def get_dias_para_vencer(self):
        """Calcula los días restantes hasta el vencimiento."""
        from datetime import date
        hoy = date.today()
        return (self.fecha_vencimiento - hoy).days

    def esta_vencido(self):
        """Verifica si el lote está vencido."""
        return self.get_dias_para_vencer() < 0

    def get_estado_vencimiento(self):
        """Determina el estado de vencimiento del lote."""
        dias_restantes = self.get_dias_para_vencer()
        
        if dias_restantes < 0:
            return "Vencido"
        elif dias_restantes == 0:
            return "Vence Hoy"
        elif dias_restantes <= 7:
            return "Crítico"
        elif dias_restantes <= 30:
            return "Precaución"
        else:
            return "Normal"

    def get_color_estado_vencimiento(self):
        """Retorna el color CSS para el estado de vencimiento."""
        estado = self.get_estado_vencimiento()
        colores = {
            'Vencido': '#dc3545',      # Rojo
            'Vence Hoy': '#fd7e14',    # Naranja oscuro
            'Crítico': '#ffc107',      # Amarillo
            'Precaución': '#28a745',   # Verde
            'Normal': '#6c757d',       # Gris
        }
        return colores.get(estado, '#6c757d')

    def save(self, *args, **kwargs):
        """Al guardar un lote, el stock del producto queda igual a la suma de lotes."""
        sync_producto = kwargs.pop('sync_producto', True)
        super().save(*args, **kwargs)
        if sync_producto:
            self.producto.sincronizar_stock_con_lotes()

    def delete(self, *args, **kwargs):
        producto = self.producto
        result = super().delete(*args, **kwargs)
        producto.sincronizar_stock_con_lotes()
        return result

    def puede_ser_usado(self):
        """Determina si el lote puede ser usado (tiene stock y no está marcado como problemático)."""
        return self.stock > 0

    def requiere_atencion(self):
        """Determina si el lote requiere atención especial (vencido con stock)."""
        return self.stock > 0 and self.esta_vencido()

    def get_descripcion_estado(self):
        """Obtiene una descripción completa del estado del lote."""
        if self.stock == 0:
            return "Lote vacío (sin stock)"
        elif self.esta_vencido():
            return f"Lote vencido con {self.stock} unidades"
        else:
            dias = self.get_dias_para_vencer()
            if dias == 0:
                return f"Vence hoy - {self.stock} unidades"
            elif dias <= 7:
                return f"Vence en {dias} días - {self.stock} unidades"
            else:
                return f"Stock normal - {self.stock} unidades"

    def __str__(self):
        return f"{self.producto.descripcion} - Lote: {self.numero_lote} - Vence: {self.fecha_vencimiento}"

    class Meta:
        verbose_name = "Lote de Producto"
        verbose_name_plural = "Lotes de Productos"
        ordering = ['fecha_vencimiento']
        unique_together = ('producto', 'numero_lote')  # Un producto no puede tener dos lotes con el mismo número

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
    lote = models.ForeignKey(
        'LoteProducto',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transacciones',
        verbose_name="Lote asociado",
    )

    def __str__(self):
        return f"{self.tipo} - {self.producto.descripcion} - {self.cantidad}"

    def inferir_lote(self):
        """Prioriza el lote escrito en la observación (origen del ingreso); luego el FK."""
        import re
        observacion = self.observacion or ''
        match = re.search(r'Lote\s*#\s*(\d+)', observacion)
        if match:
            lote_obs = self.producto.lotes.filter(numero_lote=int(match.group(1))).first()
            if lote_obs:
                return lote_obs
        if self.lote_id:
            return self.lote
        lotes = list(self.producto.lotes.all())
        if len(lotes) == 1:
            return lotes[0]
        return None

    def alinear_lote_con_observacion(self):
        """Si la observación nombra un lote distinto al FK, deja el FK igual al texto."""
        lote = self.inferir_lote()
        if lote and self.lote_id != lote.pk:
            Transaccion.objects.filter(pk=self.pk).update(lote=lote)
            self.lote = lote
            return True
        return False

    @staticmethod
    def observacion_base(texto):
        """Quita notas de corrección previas y deja el texto original del ingreso."""
        import re
        if not texto:
            return ''
        limpio = re.split(
            r'\n?\s*(?:Última corrección|Corrección de ingreso)\s*:',
            texto,
            maxsplit=1,
        )[0].strip()
        return limpio

    @classmethod
    def armar_observacion_correccion(cls, observacion_actual, cantidad_anterior, cantidad_nueva, motivo, usuario, lote=None):
        import re
        base = cls.observacion_base(observacion_actual)
        if lote is not None:
            texto_lote = f"Lote #{lote.numero_lote}"
            if lote.fecha_vencimiento:
                texto_lote += f" - Vence: {lote.fecha_vencimiento}"
            if re.search(r'Lote\s*#\s*\d+', base):
                base = re.sub(
                    r'Lote\s*#\s*\d+(?:\s*-\s*Vence:\s*\S+)?',
                    texto_lote,
                    base,
                    count=1,
                )
            else:
                base = f"{texto_lote}. {base}".strip() if base else texto_lote
        linea = (
            f"Última corrección: {cantidad_anterior} → {cantidad_nueva}. "
            f"Motivo: {motivo}. Usuario: {usuario.nombre}."
        )
        return f"{base}\n{linea}".strip() if base else linea

    @classmethod
    def ultima_correccion_texto(cls, observacion):
        base = cls.observacion_base(observacion)
        full = (observacion or '').strip()
        if not full:
            return ''
        if base and full.startswith(base):
            return full[len(base):].strip()
        return ''

    @staticmethod
    def _clave_kardex(transaccion):
        """Misma regla que el bincard: fecha, y si empatan, entradas antes que salidas."""
        from datetime import datetime
        import pytz
        fecha = transaccion.fecha
        if fecha is None:
            fecha = datetime(1970, 1, 1, tzinfo=pytz.UTC)
        elif fecha.tzinfo is None:
            fecha = pytz.UTC.localize(fecha)
        tipo_orden = 0 if transaccion.tipo == 'entrada' else 1
        return (fecha, tipo_orden, transaccion.pk or 0)

    @classmethod
    def simular_saldos(cls, producto, override_id=None, override_cantidad=None):
        """Kardex lineal. Permite probar una cantidad distinta en una entrada."""
        transacciones = list(cls.objects.filter(producto=producto))
        transacciones.sort(key=cls._clave_kardex)
        saldo = 0
        resultado = []
        for transaccion in transacciones:
            cantidad = transaccion.cantidad
            if override_id is not None and transaccion.pk == override_id:
                cantidad = override_cantidad
            if transaccion.tipo == 'entrada':
                saldo += cantidad
            else:
                saldo -= cantidad
            resultado.append((transaccion, saldo))
        return resultado

    @classmethod
    def limites_correccion_ingreso(cls, transaccion, lote=None):
        """Mínimo = lo que exige el lote y el kardex. El bincard nunca puede quedar negativo."""
        lote = lote or transaccion.inferir_lote()
        if lote is not None and lote.pk:
            lote.refresh_from_db()
        producto = transaccion.producto
        producto.refresh_from_db()
        if producto.tiene_vencimiento:
            stock_fisico = lote.stock if lote is not None else 0
        else:
            stock_fisico = producto.stock
        minimo_fisico = max(0, transaccion.cantidad - stock_fisico)

        saldos = cls.simular_saldos(transaccion.producto)
        min_tail = None
        fecha_critica = None
        empezado = False
        for tx, saldo in saldos:
            if tx.pk == transaccion.pk:
                empezado = True
            if empezado:
                if min_tail is None or saldo < min_tail:
                    min_tail = saldo
                    fecha_critica = tx.fecha
        minimo_kardex = transaccion.cantidad - min_tail if min_tail is not None else 0
        minimo = max(0, minimo_fisico, minimo_kardex)
        return {
            'minimo': minimo,
            'minimo_kardex': max(0, minimo_kardex),
            'minimo_fisico': minimo_fisico,
            'fecha_critica': fecha_critica,
            'saldo_minimo': min_tail,
            'stock_fisico': stock_fisico,
            'puede_reducir': minimo < transaccion.cantidad,
            'debe_aumentar': minimo > transaccion.cantidad,
            'puede_anular': minimo == 0,
            'puede_cero': minimo == 0,
        }

    @classmethod
    def texto_ayuda_limites(cls, limites):
        """Texto único para formulario, pantalla y AJAX."""
        minimo = limites['minimo']
        stock_fisico = limites.get('stock_fisico', 0)
        fecha = limites.get('fecha_critica')
        if hasattr(fecha, 'strftime'):
            fecha_txt = fecha.strftime('%d/%m/%Y %H:%M')
        else:
            fecha_txt = fecha or ''

        if limites.get('debe_aumentar'):
            extra = f' (punto crítico: {fecha_txt})' if fecha_txt else ''
            return (
                f'El bincard ya tiene saldo negativo. Debe aumentar este ingreso '
                f'al menos a {minimo} unidades{extra}. No se puede reducir, dejar en 0 ni anular.'
            )
        if limites.get('puede_cero'):
            return (
                'Puede dejar en 0: esas unidades siguen en bodega y el bincard no queda negativo. '
                '0 anula el ingreso y deja el lote en 0.'
            )
        if limites.get('puede_reducir'):
            partes = [f'No puede bajar de {minimo} unidades.']
            if limites.get('minimo_kardex', 0) >= limites.get('minimo_fisico', 0) and limites.get('minimo_kardex', 0) > 0:
                critico = f' el {fecha_txt}' if fecha_txt else ''
                partes.append(
                    f'El bincard exige {limites["minimo_kardex"]}: si baja más, el saldo queda negativo{critico}.'
                )
            if limites.get('minimo_fisico', 0) > 0:
                partes.append(
                    f'En el lote quedan {stock_fisico}; {limites["minimo_fisico"]} deja el lote en 0.'
                )
            partes.append('No se puede 0 ni anular.')
            return ' '.join(partes)
        return (
            f'Este ingreso no se puede reducir (mínimo {minimo}). Solo puede aumentarse. '
            'No se puede 0 ni anular.'
        )

    @classmethod
    def texto_ayuda_anular(cls, limites):
        if limites.get('puede_anular'):
            return 'Anular o cantidad 0 quita este movimiento y deja el lote en 0. El bincard no queda negativo.'
        if limites.get('debe_aumentar') or limites.get('minimo_kardex', 0) >= limites.get('minimo_fisico', 0):
            return (
                f'No se puede 0 ni anular: el bincard quedaría negativo. '
                f'Mínimo {limites["minimo"]} unidades.'
            )
        return (
            f'No se puede 0 ni anular: parte de este ingreso ya se usó. '
            f'Mínimo {limites["minimo"]} (deja el lote en 0).'
        )

    @classmethod
    def validar_correccion_ingreso(cls, transaccion, cantidad_nueva, lote=None):
        """No deja lote/stock ni saldo histórico negativo. 0 solo si sigue todo en bodega."""
        if transaccion.tipo != 'entrada':
            raise ValueError('Solo se pueden corregir transacciones de entrada.')
        if cantidad_nueva is None or cantidad_nueva < 0:
            raise ValueError('La cantidad no puede ser negativa.')
        if cantidad_nueva == transaccion.cantidad:
            raise ValueError('La cantidad nueva debe ser distinta a la registrada.')

        limites = cls.limites_correccion_ingreso(transaccion, lote)
        if cantidad_nueva < limites['minimo']:
            fecha = limites['fecha_critica']
            fecha_txt = fecha.strftime('%d/%m/%Y %H:%M') if fecha else 'una fecha del historial'
            if limites['debe_aumentar'] or (
                limites['minimo_kardex'] >= limites['minimo_fisico'] and limites['minimo_kardex'] > 0
            ):
                raise ValueError(
                    f'No se puede corregir a {cantidad_nueva}: el {fecha_txt} el saldo del bincard '
                    f'quedaría negativo (hay una salida mayor a ese ingreso). '
                    f'El mínimo es {limites["minimo"]} unidades.'
                )
            raise ValueError(
                f'No se puede corregir a {cantidad_nueva}: el lote o el stock quedaría negativo. '
                f'Solo quedan {limites["stock_fisico"]} unidades de este ingreso. '
                f'El mínimo es {limites["minimo"]} (el lote quedaría en 0).'
            )

        saldos = cls.simular_saldos(
            transaccion.producto,
            override_id=transaccion.pk,
            override_cantidad=cantidad_nueva,
        )
        empezado = False
        for tx, saldo in saldos:
            if tx.pk == transaccion.pk:
                empezado = True
            if empezado and saldo < 0:
                fecha_txt = tx.fecha.strftime('%d/%m/%Y %H:%M') if tx.fecha else 'una fecha'
                raise ValueError(
                    f'No se puede corregir a {cantidad_nueva}: el {fecha_txt} el saldo quedaría en {saldo}. '
                    f'El mínimo es {limites["minimo"]} unidades.'
                )

        delta = cantidad_nueva - transaccion.cantidad
        producto = transaccion.producto
        lote_obj = lote or transaccion.inferir_lote()
        if producto.tiene_vencimiento:
            if lote_obj is None:
                raise ValueError('Debe indicar el lote asociado a este ingreso.')
            if lote_obj.stock + delta < 0:
                raise ValueError(
                    f'No se puede corregir: el lote #{lote_obj.numero_lote} tiene {lote_obj.stock} '
                    f'y la corrección dejaría {lote_obj.stock + delta}.'
                )
        elif producto.stock + delta < 0:
            raise ValueError(
                f'No se puede corregir: el stock actual es {producto.stock} y la corrección '
                f'dejaría {producto.stock + delta}.'
            )
        return limites

    @classmethod
    def validar_anulacion_ingreso(cls, transaccion, lote=None):
        """Anular (cantidad 0) solo si sigue en bodega y el kardex no queda negativo."""
        if transaccion.tipo != 'entrada':
            raise ValueError('Solo se pueden anular transacciones de entrada.')
        limites = cls.limites_correccion_ingreso(transaccion, lote)
        if not limites['puede_anular']:
            raise ValueError(cls.texto_ayuda_anular(limites))
        return limites


def usuario_es_administrador(user):
    """Compatibilidad: hoy significa que puede corregir ingresos (Administrador Auditor)."""
    return usuario_puede_corregir_ingreso(user)


def usuario_puede_corregir_ingreso(user):
    """True solo para Administrador Auditor o superusuario."""
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    return (
        user.is_superuser
        or user.groups.filter(name='Administrador Auditor').exists()
    )


def usuario_puede_panel_admin(user):
    """True para entrar al panel Django (Administrador Auditor o superusuario)."""
    return usuario_puede_corregir_ingreso(user)


def usuario_es_admin_operativo(user):
    """Administrador o Administrador Auditor: gestión de usuarios, departamentos, categorías."""
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    return (
        user.is_superuser
        or user.groups.filter(name__in=['Administrador', 'Administrador Auditor']).exists()
    )


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

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        permissions = [
            ("can_manage_categories", "Can manage categories"),
        ]