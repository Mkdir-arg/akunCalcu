import re

from django.db import models
from django.db.models import Max
from django.contrib.auth.models import User
from django.utils import timezone


class PedidoFabrica(models.Model):
    ESTADO_CHOICES = [
        ('recibido', 'Recibido'),
        ('en_fabrica', 'En fábrica'),
        ('en_produccion', 'En producción'),
        ('terminado', 'Terminado'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    ]
    # Estados en los que el taller trabaja: las órdenes están congeladas y el
    # estado del pedido se calcula a partir de sus etapas (REQ-063).
    ESTADOS_LIBERADOS = ('en_fabrica', 'en_produccion', 'terminado')
    ESTADOS_CERRADOS = ('entregado', 'cancelado')
    TONOS_ESTADO = {
        'recibido': 'amber', 'en_fabrica': 'violet', 'en_produccion': 'blue',
        'terminado': 'green', 'entregado': 'gray', 'cancelado': 'red',
    }

    numero = models.CharField(max_length=50, unique=True)
    cliente = models.CharField(max_length=200)
    fecha = models.DateField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='recibido')
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
    liberado_at = models.DateTimeField(null=True, blank=True, verbose_name='Liberado a fábrica el')
    liberado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pedidos_fabrica_liberados', verbose_name='Liberado por',
    )
    entregado_at = models.DateTimeField(null=True, blank=True, verbose_name='Entregado el')
    motivo_cancelacion = models.TextField(blank=True, verbose_name='Motivo de cancelación')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Pedido de Fábrica'
        verbose_name_plural = 'Pedidos de Fábrica'
        ordering = ['-created_at']

    def __str__(self):
        return f"Pedido {self.numero} - {self.cliente}"

    @classmethod
    def generar_numero(cls):
        """Próximo PF-NNNN: el mayor existente + 1 (los pedidos manuales pueden dejar huecos)."""
        mayor = 0
        for numero in cls.objects.filter(numero__startswith='PF-').values_list('numero', flat=True):
            coincidencia = re.fullmatch(r'PF-(\d+)', numero)
            if coincidencia:
                mayor = max(mayor, int(coincidencia.group(1)))
        return f'PF-{mayor + 1:04d}'

    @property
    def tono_estado(self):
        return self.TONOS_ESTADO.get(self.estado, 'gray')

    @property
    def esta_liberado(self):
        return self.estado in self.ESTADOS_LIBERADOS

    @property
    def esta_cerrado(self):
        return self.estado in self.ESTADOS_CERRADOS

    def ordenes_activas(self):
        return self.ordenes.exclude(etapa='anulada')

    @property
    def fecha_comprometida(self):
        fechas = [o.fecha_comprometida for o in self.ordenes.all() if o.fecha_comprometida]
        return min(fechas) if fechas else None

    @property
    def esta_atrasado(self):
        if self.esta_cerrado or self.estado == 'terminado':
            return False
        fecha = self.fecha_comprometida
        return bool(fecha and fecha < timezone.localdate())

    def faltantes_para_liberar(self):
        """[(orden, ['Medida', 'Color', …])] de las órdenes que no se pueden fabricar todavía."""
        resultado = []
        for orden in self.ordenes_activas().prefetch_related('medidas'):
            faltan = orden.faltantes()
            if faltan:
                resultado.append((orden, faltan))
        return resultado

    def estado_calculado(self):
        """Estado que corresponde a las etapas de sus órdenes. Fuera de los estados liberados no cambia."""
        if not self.esta_liberado:
            return self.estado
        etapas = list(self.ordenes_activas().values_list('etapa', flat=True))
        if etapas and all(e == 'lista' for e in etapas):
            return 'terminado'
        if any(e != 'por_fabricar' for e in etapas):
            return 'en_produccion'
        return 'en_fabrica'


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

    # Circuito de fábrica (REQ-063)
    ETAPA_CHOICES = [
        ('por_fabricar', 'Por fabricar'),
        ('corte', 'Corte'),
        ('armado', 'Armado'),
        ('vidriado', 'Vidriado'),
        ('lista', 'Lista'),
        ('anulada', 'Anulada'),
    ]
    FLUJO_ETAPAS = ['por_fabricar', 'corte', 'armado', 'vidriado', 'lista']
    etapa = models.CharField(max_length=20, choices=ETAPA_CHOICES, default='por_fabricar', verbose_name='Etapa')
    etapa_at = models.DateTimeField(null=True, blank=True, verbose_name='Etapa actualizada el')
    revision = models.PositiveSmallIntegerField(default=0, verbose_name='Revisión')
    reimpresion_pendiente = models.BooleanField(default=False, verbose_name='Reimpresión pendiente')

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

    def faltantes(self):
        """Datos sin los que el taller no puede fabricar la orden."""
        faltan = []
        if not any(m.medida.strip() for m in self.medidas.all()):
            faltan.append('Medida')
        for campo, etiqueta in (('linea', 'Línea'), ('color', 'Color'), ('tipo_vidrio', 'Vidrio')):
            if not getattr(self, campo).strip():
                faltan.append(etiqueta)
        if self.modelo_hoja.strip() and not self.cantidad_hojas.strip():
            faltan.append('Cantidad de hojas')
        if not self.fecha_comprometida:
            faltan.append('Fecha comprometida')
        return faltan

    def _indice_etapa(self):
        return self.FLUJO_ETAPAS.index(self.etapa) if self.etapa in self.FLUJO_ETAPAS else None

    @property
    def etapa_siguiente(self):
        i = self._indice_etapa()
        return self.FLUJO_ETAPAS[i + 1] if i is not None and i + 1 < len(self.FLUJO_ETAPAS) else None

    @property
    def etapa_anterior(self):
        i = self._indice_etapa()
        return self.FLUJO_ETAPAS[i - 1] if i else None

    @property
    def tono_etapa(self):
        if self.etapa in ('corte', 'armado', 'vidriado'):
            return 'blue'
        return {'lista': 'green', 'anulada': 'red'}.get(self.etapa, 'gray')

    @property
    def pasos(self):
        """Pasos del stepper (corte, armado, vidriado, lista). Una orden lista los muestra todos como hechos."""
        if self.etapa == 'anulada':
            return []
        etiquetas = dict(self.ETAPA_CHOICES)
        i = self._indice_etapa()
        pasos = []
        for n, clave in enumerate(self.FLUJO_ETAPAS[1:], start=1):
            if i == n and clave != 'lista':
                estado = 'actual'
            elif i >= n:
                estado = 'hecho'
            else:
                estado = 'pendiente'
            pasos.append({'etiqueta': etiquetas[clave], 'estado': estado})
        return pasos

    @property
    def etiqueta_siguiente(self):
        return dict(self.ETAPA_CHOICES).get(self.etapa_siguiente, '')

    @property
    def etiqueta_anterior(self):
        return dict(self.ETAPA_CHOICES).get(self.etapa_anterior, '')

    @property
    def cantidad_total(self):
        """Unidades a fabricar: suma de las filas de medidas (usa el prefetch si lo hay)."""
        return sum(m.cantidad or 0 for m in self.medidas.all())


class HistorialPedidoFabrica(models.Model):
    """Registro de cada cambio de estado del pedido, de etapa o de revisión de una orden."""

    TIPO_CHOICES = [
        ('estado_pedido', 'Estado del pedido'),
        ('etapa_orden', 'Etapa de orden'),
        ('revision', 'Revisión de orden'),
    ]

    pedido = models.ForeignKey(PedidoFabrica, on_delete=models.CASCADE, related_name='historial', verbose_name='Pedido')
    orden = models.ForeignKey(
        OrdenFabricacion, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='historial', verbose_name='Orden',
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name='Tipo')
    desde = models.CharField(max_length=20, blank=True, verbose_name='Desde')
    hasta = models.CharField(max_length=20, blank=True, verbose_name='Hasta')
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Usuario')
    nota = models.TextField(blank=True, verbose_name='Nota')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Historial de pedido de fábrica'
        verbose_name_plural = 'Historial de pedidos de fábrica'
        ordering = ['-created_at', '-id']

    def __str__(self):
        sujeto = f'orden {self.orden.numero_formateado}' if self.orden_id else f'pedido {self.pedido.numero}'
        return f'{self.get_tipo_display()} {sujeto}: {self.desde or "—"} → {self.hasta}'

    @property
    def texto(self):
        """Frase para la línea de tiempo del detalle del pedido."""
        if self.tipo == 'estado_pedido':
            estados = dict(PedidoFabrica.ESTADO_CHOICES)
            return f'Pedido: {estados.get(self.hasta, self.hasta)}'
        etapas = dict(OrdenFabricacion.ETAPA_CHOICES)
        numero = self.orden.numero_formateado if self.orden_id else '—'
        if self.tipo == 'revision':
            return f'Orden {numero}: revisión {self.hasta}'
        return f'Orden {numero}: {etapas.get(self.desde, self.desde)} → {etapas.get(self.hasta, self.hasta)}'


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
        ('unidad', 'Unidad'),
        ('otro', 'Otro'),
    ]

    codigo = models.CharField(max_length=50, unique=True, verbose_name='Código')
    nombre = models.CharField(max_length=200, verbose_name='Nombre')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='otro', verbose_name='Tipo')
    linea_id = models.IntegerField(null=True, blank=True, verbose_name='Línea ID')
    precio_m2 = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Precio por m²')
    precio_unidad = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Precio por unidad')
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
