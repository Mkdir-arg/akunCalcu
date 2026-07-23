from django.conf import settings
from django.db import models
from django.utils import timezone


class SolicitudPresupuestoQuerySet(models.QuerySet):
    def pendientes(self):
        """Solicitudes asignadas y sin contestar (con vendedor), para el resumen
        diario de recordatorios. Se agrupan por vendedor en la view."""
        return (
            self.filter(
                estado=SolicitudPresupuesto.ESTADO_ASIGNADA,
                vendedor__isnull=False,
            )
            .select_related('vendedor', 'vendedor__perfil_acceso__numero_whatsapp')
            .order_by('vendedor_id', 'fecha_recepcion')
        )


class SolicitudPresupuesto(models.Model):
    ESTADO_ASIGNADA = 'asignada'
    ESTADO_CONTESTADA = 'contestada'
    ESTADO_SIN_ASIGNAR = 'sin_asignar'
    ESTADO_CHOICES = [
        (ESTADO_ASIGNADA, 'Asignada'),
        (ESTADO_CONTESTADA, 'Contestada'),
        (ESTADO_SIN_ASIGNAR, 'Sin asignar'),
    ]

    nombre_cliente = models.CharField(max_length=200, blank=True, verbose_name="Nombre del cliente")
    email = models.EmailField(blank=True, verbose_name="Email")
    telefono = models.CharField(max_length=50, blank=True, verbose_name="Teléfono")
    asunto = models.CharField(max_length=300, blank=True, verbose_name="Asunto")
    mensaje = models.TextField(blank=True, verbose_name="Mensaje")
    vendedor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='solicitudes_presupuesto',
        verbose_name="Vendedor asignado",
    )
    estado = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default=ESTADO_ASIGNADA, verbose_name="Estado",
    )
    origen = models.CharField(max_length=30, default='email', verbose_name="Origen")
    gmail_thread_id = models.CharField(
        max_length=120, blank=True, db_index=True, verbose_name="ID de hilo de Gmail",
    )
    fecha_recepcion = models.DateTimeField(default=timezone.now, verbose_name="Fecha de recepción")
    fecha_asignacion = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de asignación")
    fecha_contestada = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de respuesta")
    ultimo_recordatorio = models.DateTimeField(null=True, blank=True, verbose_name="Último recordatorio")
    notas = models.TextField(blank=True, verbose_name="Notas internas")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = SolicitudPresupuestoQuerySet.as_manager()

    class Meta:
        verbose_name = "Solicitud de presupuesto"
        verbose_name_plural = "Solicitudes de presupuesto"
        ordering = ['-fecha_recepcion']

    def __str__(self):
        cliente = self.nombre_cliente or self.email or 'Sin datos'
        return f"Solicitud de {cliente} ({self.get_estado_display()})"

    @property
    def numero_whatsapp_vendedor(self):
        """Número de WhatsApp del vendedor asignado (o '' si no tiene uno activo)."""
        if not self.vendedor:
            return ''
        from usuarios.access_control import get_access_profile
        perfil = get_access_profile(self.vendedor)
        numero = perfil.numero_whatsapp if perfil else None
        if numero and numero.activo:
            return numero.numero
        return ''

    def marcar_contestada(self, ahora=None):
        self.estado = self.ESTADO_CONTESTADA
        self.fecha_contestada = ahora or timezone.now()
        self.save(update_fields=['estado', 'fecha_contestada', 'updated_at'])

    def _lineas_datos(self):
        partes = []
        if self.nombre_cliente:
            partes.append(f"👤 {self.nombre_cliente}")
        if self.telefono:
            partes.append(f"📞 {self.telefono}")
        if self.email:
            partes.append(f"✉️ {self.email}")
        if self.asunto:
            partes.append(f"📝 {self.asunto}")
        return partes

    def mensaje_whatsapp(self):
        """Aviso inicial que recibe el vendedor cuando se le asigna la solicitud."""
        return "\n".join(["📩 Nuevo pedido de presupuesto"] + self._lineas_datos())

    def resumen_corto(self):
        """Etiqueta de una sola línea para el listado del recordatorio diario.
        Sin saltos de línea: WhatsApp/Meta no los permite en params de plantilla."""
        cliente = self.nombre_cliente or self.email or 'Sin nombre'
        return f"{cliente} ({self.telefono})" if self.telefono else cliente


class ConfiguracionSolicitudes(models.Model):
    """Singleton (pk=1) que guarda el puntero del round-robin de vendedores."""

    ultimo_vendedor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        verbose_name="Último vendedor asignado",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuración de solicitudes"
        verbose_name_plural = "Configuración de solicitudes"

    def __str__(self):
        return "Configuración de rotación de solicitudes"
