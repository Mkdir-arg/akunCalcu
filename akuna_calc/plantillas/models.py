from django.db import models
from django.db.models import Max
from django.contrib.auth.models import User


class PedidoFabrica(models.Model):
    ESTADO_CHOICES = [
        ('BORRADOR', 'Borrador'),
        ('EN_PROCESO', 'En Proceso'),
        ('COMPLETADO', 'Completado'),
        ('CANCELADO', 'Cancelado'),
    ]

    numero = models.CharField(max_length=50, unique=True)
    cliente = models.CharField(max_length=200)
    fecha = models.DateField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='BORRADOR')
    observaciones = models.TextField(blank=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='pedidos_fabrica')
    presupuesto = models.ForeignKey(
        'presupuestos.Presupuesto',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pedidos_fabrica',
        verbose_name='Presupuesto de origen',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Pedido de Fábrica'
        verbose_name_plural = 'Pedidos de Fábrica'
        ordering = ['-created_at']

    def __str__(self):
        return f"Pedido {self.numero} - {self.cliente}"


class OrdenFabricacion(models.Model):
    """Orden de fabricación (planilla de fábrica). Una por ítem del presupuesto o manual."""

    pedido = models.ForeignKey(
        PedidoFabrica,
        on_delete=models.CASCADE,
        related_name='ordenes',
        verbose_name='Pedido de fábrica',
    )
    item_presupuesto = models.ForeignKey(
        'presupuestos.ItemPresupuesto',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ordenes_fabricacion',
        verbose_name='Ítem de presupuesto de origen',
    )
    numero = models.PositiveIntegerField(unique=True, verbose_name='N° de orden')
    orden = models.PositiveIntegerField(default=0, verbose_name='Orden en el pedido')
    fecha_comprometida = models.DateField(null=True, blank=True, verbose_name='Fecha comprometida')

    # Datos iniciales
    atendido_por = models.CharField(max_length=150, blank=True, verbose_name='Atendido por')
    medicion_por = models.CharField(max_length=150, blank=True, verbose_name='Medición realizada por')

    # Datos del cliente
    cliente_nombre = models.CharField(max_length=200, blank=True, verbose_name='Apellido y Nombre / Razón Social')
    cliente_domicilio = models.CharField(max_length=200, blank=True, verbose_name='Domicilio')
    cliente_piso = models.CharField(max_length=20, blank=True, verbose_name='Piso')
    cliente_depto = models.CharField(max_length=20, blank=True, verbose_name='Depto.')
    cliente_localidad = models.CharField(max_length=120, blank=True, verbose_name='Localidad')
    cliente_mail = models.CharField(max_length=150, blank=True, verbose_name='Mail')
    cliente_telefono = models.CharField(max_length=80, blank=True, verbose_name='Teléfono')

    # Detalle de la abertura
    tipo_abertura = models.CharField(max_length=150, blank=True, verbose_name='Tipo de abertura')
    linea = models.CharField(max_length=150, blank=True, verbose_name='Línea')
    color = models.CharField(max_length=100, blank=True, verbose_name='Color')

    # Sección Detalle
    mosquitero = models.CharField(max_length=100, blank=True, verbose_name='Mosquitero')
    mosquitero_modelo = models.CharField(max_length=150, blank=True, verbose_name='Modelo de mosquitero')
    travesano = models.CharField(max_length=150, blank=True, verbose_name='Travesaño')
    tipo_marco = models.CharField(max_length=150, blank=True, verbose_name='Tipo de marco')
    marco_desarmado = models.CharField(max_length=100, blank=True, verbose_name='Marco desarmado')
    umbral_transitable = models.CharField(max_length=100, blank=True, verbose_name='Umbral transitable')
    premarco = models.CharField(max_length=100, blank=True, verbose_name='Premarco')
    guia_persiana = models.CharField(max_length=100, blank=True, verbose_name='Guía para persiana')
    tipo_guia = models.CharField(max_length=100, blank=True, verbose_name='Tipo de guía')
    tapacinta = models.CharField(max_length=100, blank=True, verbose_name='Tapacinta')
    lado = models.CharField(max_length=100, blank=True, verbose_name='Lado')
    modelo_hoja = models.CharField(max_length=150, blank=True, verbose_name='Modelo de hoja')
    travesano_divisor = models.CharField(max_length=100, blank=True, verbose_name='Travesaño divisor')
    altura_travesano = models.CharField(max_length=100, blank=True, verbose_name='Altura del travesaño')
    cantidad_hojas = models.CharField(max_length=50, blank=True, verbose_name='Cantidad de hojas')
    tipo_vidrio = models.CharField(max_length=150, blank=True, verbose_name='Tipo de vidrio')
    contramarco = models.CharField(max_length=100, blank=True, verbose_name='Contramarco')
    modelo_contramarco = models.CharField(max_length=150, blank=True, verbose_name='Modelo de contramarco')
    tipo_trabajo = models.CharField(max_length=150, blank=True, verbose_name='Tipo de trabajo')
    altura_trabajo = models.CharField(max_length=100, blank=True, verbose_name='Altura')
    estructura = models.TextField(blank=True, verbose_name='Estructura')

    nota = models.TextField(blank=True, verbose_name='Nota / Observaciones')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Orden de Fabricación'
        verbose_name_plural = 'Órdenes de Fabricación'
        ordering = ['pedido', 'orden', 'id']

    def __str__(self):
        return f"Orden {self.numero_formateado} - {self.pedido.numero}"

    @property
    def numero_formateado(self):
        return f'{self.numero:04d}'

    @classmethod
    def generar_numero(cls):
        return (cls.objects.aggregate(m=Max('numero'))['m'] or 0) + 1


class MedidaOrdenFabricacion(models.Model):
    """Fila de la tabla 'Detalle de medidas' de una orden de fabricación."""

    orden = models.ForeignKey(
        OrdenFabricacion,
        on_delete=models.CASCADE,
        related_name='medidas',
        verbose_name='Orden de fabricación',
    )
    item = models.CharField(max_length=50, blank=True, verbose_name='Item')
    cantidad = models.PositiveIntegerField(default=1, verbose_name='Cantidad')
    medida = models.CharField(max_length=120, blank=True, verbose_name='Medida')
    observaciones = models.CharField(max_length=200, blank=True, verbose_name='Observaciones')
    piso_depto = models.CharField(max_length=80, blank=True, verbose_name='Piso / Depto.')
    orden_fila = models.PositiveIntegerField(default=0, verbose_name='Orden de fila')

    class Meta:
        verbose_name = 'Medida de Orden'
        verbose_name_plural = 'Medidas de Orden'
        ordering = ['orden', 'orden_fila', 'id']

    def __str__(self):
        return f"{self.orden.numero_formateado} - {self.medida}"


class OpcionalFabrica(models.Model):
    """Opcionales que se pueden agregar a los pedidos de fábrica."""

    TIPO_CHOICES = [
        ('mosquitero', 'Mosquitero'),
        ('premarco', 'Premarco'),
        ('otro', 'Otro'),
    ]

    codigo = models.CharField(max_length=50, unique=True, verbose_name='Código')
    nombre = models.CharField(max_length=200, verbose_name='Nombre')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='otro', verbose_name='Tipo')
    linea_id = models.IntegerField(null=True, blank=True, verbose_name='Línea ID')
    precio_m2 = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Precio por m²')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    activo = models.BooleanField(default=True, verbose_name='Activo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Opcional de Fábrica'
        verbose_name_plural = 'Opcionales de Fábrica'
        ordering = ['codigo']

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class FormulaOpcional(models.Model):
    """Fórmulas de cálculo para opcionales de fábrica."""

    TIPO_RELACIONADOR_CHOICES = [
        ('perfil', 'Perfil'),
        ('hoja', 'Hoja'),
        ('vidrio', 'Vidrio'),
    ]

    opcional = models.ForeignKey(OpcionalFabrica, on_delete=models.CASCADE, related_name='formulas')
    cantidad = models.CharField(max_length=100, verbose_name='Cantidad', help_text='Fórmula para cantidad (ej: 2, CANTIDAD_HOJAS)')
    formula = models.CharField(max_length=200, verbose_name='Fórmula', help_text='Fórmula de cálculo (ej: Alto - 42)')
    angulo = models.CharField(max_length=10, blank=True, verbose_name='Ángulo', help_text='Ángulo de corte (ej: 90, 45)')
    tipo_relacionador = models.CharField(max_length=20, choices=TIPO_RELACIONADOR_CHOICES, default='perfil', verbose_name='Tipo')
    perfil = models.CharField(max_length=100, blank=True, verbose_name='Perfil', help_text='Código del perfil')
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Precio')
    orden = models.IntegerField(default=0, verbose_name='Orden')

    class Meta:
        verbose_name = 'Fórmula de Opcional'
        verbose_name_plural = 'Fórmulas de Opcionales'
        ordering = ['opcional', 'orden', 'id']

    def __str__(self):
        return f"{self.opcional.codigo} - Fórmula #{self.orden}"


class AccesorioOpcional(models.Model):
    """Accesorios para opcionales de fábrica."""
    opcional = models.ForeignKey(OpcionalFabrica, on_delete=models.CASCADE, related_name='accesorios')
    cantidad = models.CharField(max_length=100, verbose_name='Cantidad', help_text='Fórmula para cantidad (ej: 2, CANTIDAD_HOJAS)')
    accesorio = models.CharField(max_length=100, verbose_name='Accesorio', help_text='Código del accesorio')
    orden = models.IntegerField(default=0, verbose_name='Orden')

    class Meta:
        verbose_name = 'Accesorio de Opcional'
        verbose_name_plural = 'Accesorios de Opcionales'
        ordering = ['opcional', 'orden', 'id']

    def __str__(self):
        return f"{self.opcional.codigo} - Accesorio #{self.orden}"


class RelacionProductoOpcional(models.Model):
    """Relaciones entre opcionales y productos de la base legacy."""
    opcional = models.ForeignKey(OpcionalFabrica, on_delete=models.CASCADE, related_name='relaciones_productos')
    extrusora_id = models.IntegerField(verbose_name='Extrusora ID')
    linea_id = models.IntegerField(verbose_name='Línea ID')
    producto_id = models.IntegerField(verbose_name='Producto ID')
    cantidad = models.IntegerField(default=1, verbose_name='Cantidad')
    orden = models.IntegerField(default=0, verbose_name='Orden')

    class Meta:
        verbose_name = 'Relación Producto-Opcional'
        verbose_name_plural = 'Relaciones Producto-Opcional'
        ordering = ['opcional', 'orden', 'id']

    def __str__(self):
        return f"{self.opcional.codigo} - Producto {self.producto_id}"
