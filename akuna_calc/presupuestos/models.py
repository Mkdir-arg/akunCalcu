from decimal import Decimal, InvalidOperation

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


def _decimal_or_zero(value):
    if value in (None, ''):
        return Decimal('0')
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal('0')


class Presupuesto(models.Model):
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('enviado', 'Enviado'),
        ('confirmado', 'Confirmado'),
        ('vencido', 'Vencido'),
        ('cancelado', 'Cancelado'),
    ]
    TIPO_OBRA_CHOICES = [
        ('obra_nueva', 'Obra nueva'),
        ('renovacion', 'Renovación'),
    ]
    TIPO_MATERIAL_CHOICES = [
        ('aluminio', 'Aluminio'),
        ('pvc', 'PVC'),
    ]
    MODALIDAD_SENA_CHOICES = [
        ('50_50', '50% adelanto / 50% saldo'),
        ('70_30', '70% adelanto / 30% saldo'),
    ]

    numero = models.CharField(max_length=20, unique=True, verbose_name='Número')
    cliente = models.ForeignKey(
        'comercial.Cliente',
        on_delete=models.PROTECT,
        related_name='presupuestos',
        verbose_name='Cliente',
    )
    solicitud = models.OneToOneField(
        'solicitudes.SolicitudPresupuesto',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='presupuesto',
        verbose_name='Solicitud de origen',
    )
    fecha_expiracion = models.DateField(verbose_name='Fecha de expiración')
    validez_dias = models.PositiveIntegerField(default=30, verbose_name='Validez (días)')
    plazo_entrega_dias = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Plazo de entrega (días)',
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='borrador',
        verbose_name='Estado',
    )
    notas = models.TextField(blank=True, verbose_name='Notas')
    tipo_material = models.CharField(
        max_length=20,
        choices=TIPO_MATERIAL_CHOICES,
        default='aluminio',
        verbose_name='Tipo de material',
    )
    tipo_obra = models.CharField(
        max_length=20,
        choices=TIPO_OBRA_CHOICES,
        blank=True,
        default='',
        verbose_name='Tipo de obra',
    )
    modalidad_sena = models.CharField(
        max_length=10,
        choices=MODALIDAD_SENA_CHOICES,
        default='50_50',
        verbose_name='Modalidad de seña',
    )
    recargo_obra_nueva = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='Recargo obra nueva',
    )
    recargo_renovacion_unitario = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='Recargo renovación por unidad',
    )
    aplicar_iva = models.BooleanField(
        default=False,
        verbose_name='Aplicar IVA 21%',
    )
    incluye_flete = models.BooleanField(
        default=False,
        verbose_name='Incluye flete',
    )
    incluye_colocacion = models.BooleanField(
        default=False,
        verbose_name='Incluye colocación',
    )
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name='Total')
    cotizacion_usd = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Cotización USD',
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='presupuestos_creados',
        verbose_name='Creado por',
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='presupuestos_editados',
        verbose_name='Editado por',
    )
    venta = models.ForeignKey(
        'comercial.Venta',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='presupuestos',
        verbose_name='Venta asociada',
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de eliminación',
    )
    deleted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='presupuestos_eliminados',
        verbose_name='Eliminado por',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Presupuesto'
        verbose_name_plural = 'Presupuestos'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.numero} - {self.cliente}'

    def esta_bloqueado(self):
        return self.estado in ('confirmado', 'cancelado')

    def es_pvc(self):
        return self.tipo_material == 'pvc'

    def tiene_cotizacion_usd(self):
        return bool(self.cotizacion_usd and self.cotizacion_usd > 0)

    def _convertir_a_usd(self, monto_ars):
        if not self.tiene_cotizacion_usd():
            return None
        return monto_ars / self.cotizacion_usd

    def esta_eliminado(self):
        return self.deleted_at is not None

    def get_observaciones_pdf(self):
        if self.incluye_flete and self.incluye_colocacion:
            inclusiones = 'incluye flete y colocación'
        elif self.incluye_flete:
            inclusiones = 'incluye flete'
        elif self.incluye_colocacion:
            inclusiones = 'incluye colocación'
        else:
            inclusiones = 'no incluye flete ni colocación'
        return f'El presente presupuesto {inclusiones}.'

    def get_resumen_flete_colocacion(self):
        if self.incluye_flete and self.incluye_colocacion:
            return 'Flete y colocación'
        if self.incluye_flete:
            return 'Flete'
        if self.incluye_colocacion:
            return 'Colocación'
        return 'Sin flete ni colocación'

    def get_total_items(self):
        return sum((item.precio_total for item in self.items.all()), Decimal('0'))

    def get_total_items_usd(self):
        return self._convertir_a_usd(self.get_total_items())

    def get_recargo_obra_nueva_aplicado(self):
        if self.tipo_obra != 'obra_nueva':
            return Decimal('0')
        return _decimal_or_zero(self.recargo_obra_nueva)

    def get_recargo_obra_nueva_aplicado_usd(self):
        return self._convertir_a_usd(self.get_recargo_obra_nueva_aplicado())

    def get_recargo_total_renovacion(self):
        if self.tipo_obra != 'renovacion':
            return Decimal('0')
        return sum((item.get_recargo_renovacion_total() for item in self.items.all()), Decimal('0'))

    def get_recargo_total_renovacion_usd(self):
        return self._convertir_a_usd(self.get_recargo_total_renovacion())

    def get_recargo_renovacion_unitario_usd(self):
        return self._convertir_a_usd(_decimal_or_zero(self.recargo_renovacion_unitario))

    def get_monto_colocacion(self):
        """Monto de colocación aplicable según el tipo de obra.

        Obra nueva: el valor de colocación (recargo_obra_nueva).
        Renovación: el recargo por unidad (recargo_renovacion_unitario).
        """
        if self.tipo_obra == 'obra_nueva':
            return _decimal_or_zero(self.recargo_obra_nueva)
        if self.tipo_obra == 'renovacion':
            return _decimal_or_zero(self.recargo_renovacion_unitario)
        return Decimal('0')

    def actualizar_items_por_configuracion(self):
        recargo_unitario = self.recargo_renovacion_unitario if self.tipo_obra == 'renovacion' else Decimal('0')
        for item in self.items.all():
            item.aplicar_recargo_renovacion(recargo_unitario)

    def aplicar_validez_dias(self):
        """Recalcula la fecha de vencimiento a partir de la validez en días.

        La validez (en días) maneja la fecha de expiración: se cuenta desde la
        fecha de creación del presupuesto. Se persiste el cambio.
        """
        from datetime import timedelta
        base = (self.created_at or timezone.now()).date()
        self.fecha_expiracion = base + timedelta(days=self.validez_dias or 30)
        self.save(update_fields=['fecha_expiracion'])

    def get_subtotal_sin_iva(self):
        return self.get_total_items() + self.get_recargo_obra_nueva_aplicado()

    def get_iva_desglosado(self):
        return self.get_subtotal_sin_iva() * Decimal('0.21')

    def get_iva(self):
        if not self.aplicar_iva:
            return Decimal('0')
        return self.get_iva_desglosado()

    def get_subtotal_sin_iva_usd(self):
        return self._convertir_a_usd(self.get_subtotal_sin_iva())

    def get_iva_usd(self):
        return self._convertir_a_usd(self.get_iva())

    def get_total_usd(self):
        return self._convertir_a_usd(self.total)

    def get_porcentaje_sena(self):
        return Decimal('0.70') if self.modalidad_sena == '70_30' else Decimal('0.50')

    def get_sena_sugerida(self):
        return (self.total * self.get_porcentaje_sena()).quantize(Decimal('0.01'))

    def get_sena_sugerida_usd(self):
        sugerida_usd = self._convertir_a_usd(self.get_sena_sugerida())
        if sugerida_usd is None:
            return None
        return sugerida_usd.quantize(Decimal('0.01'))

    def recalcular_total(self):
        subtotal = self.get_subtotal_sin_iva()
        iva = self.get_iva()
        self.total = subtotal + iva
        self.save(update_fields=['total'])

    @classmethod
    def generar_numero(cls):
        año = timezone.now().year
        ultimo = (
            cls.objects.filter(numero__startswith=f'PRES-{año}-')
            .order_by('-numero')
            .first()
        )
        if ultimo:
            try:
                seq = int(ultimo.numero.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        return f'PRES-{año}-{seq:03d}'


class ItemPresupuesto(models.Model):
    presupuesto = models.ForeignKey(
        Presupuesto,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Presupuesto',
    )
    descripcion = models.CharField(max_length=300, verbose_name='Descripción')
    cantidad = models.PositiveIntegerField(default=1, verbose_name='Cantidad')
    ancho_mm = models.IntegerField(verbose_name='Ancho (mm)')
    alto_mm = models.IntegerField(verbose_name='Alto (mm)')
    margen_porcentaje = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name='Margen (%)'
    )
    precio_unitario = models.DecimalField(
        max_digits=14, decimal_places=2, verbose_name='Precio unitario'
    )
    precio_total = models.DecimalField(
        max_digits=14, decimal_places=2, verbose_name='Precio total'
    )
    resultado_json = models.JSONField(
        default=dict, verbose_name='Detalle del cálculo'
    )
    orden = models.PositiveIntegerField(default=0, verbose_name='Orden')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Ítem de presupuesto'
        verbose_name_plural = 'Ítems de presupuesto'
        ordering = ['orden', 'created_at']

    def __str__(self):
        return f'{self.descripcion} ({self.presupuesto.numero})'

    def get_precio_unitario_base(self):
        resultado = self.resultado_json or {}
        if 'precio_unitario_base' not in resultado:
            return _decimal_or_zero(self.precio_unitario)
        return _decimal_or_zero(resultado.get('precio_unitario_base'))

    def get_recargo_renovacion_unitario(self):
        resultado = self.resultado_json or {}
        if 'recargo_renovacion_unitario_aplicado' in resultado:
            return _decimal_or_zero(resultado.get('recargo_renovacion_unitario_aplicado'))
        base = self.get_precio_unitario_base()
        recargo = _decimal_or_zero(self.precio_unitario) - base
        return recargo if recargo > 0 else Decimal('0')

    def get_recargo_renovacion_total(self):
        return self.get_recargo_renovacion_unitario() * self.cantidad

    def get_precio_unitario_usd(self):
        return self.presupuesto._convertir_a_usd(self.precio_unitario)

    def get_precio_total_usd(self):
        return self.presupuesto._convertir_a_usd(self.precio_total)

    def aplicar_recargo_renovacion(self, recargo_unitario):
        recargo_unitario = _decimal_or_zero(recargo_unitario)
        base = self.get_precio_unitario_base()
        resultado = dict(self.resultado_json or {})
        resultado['precio_unitario_base'] = float(base)
        resultado['recargo_renovacion_unitario_aplicado'] = float(recargo_unitario)
        resultado['recargo_renovacion_total_aplicado'] = float(recargo_unitario * self.cantidad)
        self.resultado_json = resultado
        self.precio_unitario = base + recargo_unitario
        self.save(update_fields=['precio_unitario', 'precio_total', 'resultado_json'])

    def save(self, *args, **kwargs):
        self.precio_total = self.precio_unitario * self.cantidad
        super().save(*args, **kwargs)


class ComentarioPresupuesto(models.Model):
    PRIORIDAD_CHOICES = [
        ('normal', 'Normal'),
        ('importante', 'Importante'),
    ]

    presupuesto = models.ForeignKey(
        Presupuesto,
        on_delete=models.CASCADE,
        related_name='comentarios',
        verbose_name='Presupuesto',
    )
    autor = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name='Autor',
    )
    texto = models.TextField(verbose_name='Comentario')
    prioridad = models.CharField(
        max_length=20,
        choices=PRIORIDAD_CHOICES,
        default='normal',
        blank=True,
        verbose_name='Prioridad',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Comentario'
        verbose_name_plural = 'Comentarios'
        ordering = ['created_at']

    def __str__(self):
        return f'Comentario de {self.autor} en {self.presupuesto.numero}'
