from datetime import datetime, timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class EventoAgendaQuerySet(models.QuerySet):
    def pendientes(self, ahora=None):
        """Devuelve los eventos cuyo recordatorio debe enviarse en este momento."""
        ahora = ahora or timezone.localtime()
        candidatos = (
            self.filter(activo=True)
            .exclude(estado='cancelado')
            .prefetch_related('destinatarios')
        )
        return [evento for evento in candidatos if evento.esta_pendiente(ahora)]


class EventoAgenda(models.Model):
    TIPO_CHOICES = [
        ('mediciones', 'Mediciones'),
        ('servicio_tecnico', 'Servicio técnico'),
        ('pendientes', 'Pendientes'),
        ('llamar', 'Llamar'),
        ('colocaciones', 'Colocaciones'),
    ]
    ESTADO_CHOICES = [
        ('programado', 'Programado'),
        ('enviado', 'Enviado'),
        ('cancelado', 'Cancelado'),
    ]

    titulo = models.CharField(max_length=200, verbose_name="Título")
    numero_pedido = models.CharField(max_length=50, blank=True, verbose_name="Número de pedido")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    tipo = models.CharField(
        max_length=20, choices=TIPO_CHOICES, default='pendientes', verbose_name="Tipo",
    )
    fecha_evento = models.DateField(verbose_name="Fecha del evento")
    hora_envio = models.TimeField(verbose_name="Hora de envío")
    anticipacion_dias = models.PositiveIntegerField(
        default=0,
        verbose_name="Anticipación (días antes)",
        help_text="Avisar X días antes de la fecha. Solo aplica a eventos sin repetir.",
    )
    destinatarios = models.ManyToManyField(
        'gastos_diarios.NumeroAutorizado',
        related_name='eventos_agenda',
        verbose_name="Destinatarios",
    )
    cliente = models.ForeignKey(
        'comercial.Cliente', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='eventos_agenda', verbose_name="Cliente",
    )
    colocador = models.ForeignKey(
        'comercial.Cuenta', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='eventos_agenda', verbose_name="Colocador",
    )
    tecnico = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='eventos_tecnico', verbose_name="Técnico responsable",
    )
    direccion = models.CharField(max_length=300, blank=True, verbose_name="Dirección")
    lat = models.FloatField(null=True, blank=True, verbose_name="Latitud")
    lng = models.FloatField(null=True, blank=True, verbose_name="Longitud")
    estado = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default='programado', verbose_name="Estado",
    )
    ultimo_envio = models.DateTimeField(null=True, blank=True, verbose_name="Último envío")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
    )

    objects = EventoAgendaQuerySet.as_manager()

    class Meta:
        verbose_name = "Evento de agenda"
        verbose_name_plural = "Eventos de agenda"
        ordering = ['fecha_evento', 'hora_envio']

    def __str__(self):
        return f"{self.get_tipo_display()}: {self.titulo} ({self.get_estado_display()})"

    # --- Lógica de scheduling ---

    def _aware(self, fecha):
        """datetime tz-aware (zona local) combinando una fecha con la hora de envío."""
        return timezone.make_aware(
            datetime.combine(fecha, self.hora_envio), timezone.get_current_timezone()
        )

    def fecha_recordatorio(self):
        """Fecha en que se envía el aviso de un evento sin repetir (con anticipación)."""
        return self.fecha_evento - timedelta(days=self.anticipacion_dias)

    def esta_pendiente(self, ahora=None):
        ahora = ahora or timezone.localtime()
        if not self.activo or self.estado != 'programado':
            return False
        return self._aware(self.fecha_recordatorio()) <= ahora

    def proximo_envio(self):
        """Próximo datetime de envío, para mostrar en el listado."""
        if self.estado != 'programado':
            return None
        return self._aware(self.fecha_recordatorio())

    def proximo_envio_relativo(self, hoy=None):
        """Etiqueta relativa del próximo envío para el listado.

        Devuelve un dict {'texto', 'urgencia'} o None si el evento no está
        programado. La urgencia ('vencido'|'hoy'|'pronto'|'normal') se usa
        para colorear el badge en el template.
        """
        if self.estado != 'programado':
            return None
        hoy = hoy or timezone.localdate()
        dias = (self.fecha_recordatorio() - hoy).days
        hora = self.hora_envio.strftime('%H:%M')
        if dias < 0:
            return {'texto': 'Vencido', 'urgencia': 'vencido'}
        if dias == 0:
            return {'texto': f'Hoy {hora}', 'urgencia': 'hoy'}
        if dias == 1:
            return {'texto': f'Mañana {hora}', 'urgencia': 'pronto'}
        if dias <= 7:
            return {'texto': f'En {dias} días', 'urgencia': 'pronto'}
        return {'texto': self.fecha_recordatorio().strftime('%d/%m/%Y'), 'urgencia': 'normal'}

    def ocurre_en(self, fecha):
        """Si el evento cae en la fecha dada (para mostrarlo en el calendario)."""
        return self.fecha_evento == fecha

    def marcar_enviado(self, ahora=None):
        ahora = ahora or timezone.now()
        self.ultimo_envio = ahora
        self.estado = 'enviado'
        self.save(update_fields=['ultimo_envio', 'estado', 'updated_at'])

    def maps_url(self):
        """Link a Google Maps a partir de coordenadas o dirección (no requiere API key)."""
        from urllib.parse import quote
        if self.lat is not None and self.lng is not None:
            return f"https://www.google.com/maps/search/?api=1&query={self.lat},{self.lng}"
        if self.direccion:
            return f"https://www.google.com/maps/search/?api=1&query={quote(self.direccion)}"
        return ''

    def mensaje(self):
        """Texto del recordatorio que se manda por WhatsApp."""
        partes = [f"🔔 {self.get_tipo_display()}: {self.titulo}"]
        if self.numero_pedido:
            partes.append(f"📦 Pedido N° {self.numero_pedido}")
        if self.descripcion:
            partes.append(self.descripcion)
        partes.append(f"📅 {self.fecha_evento.strftime('%d/%m/%Y')}")
        if self.cliente:
            partes.append(f"👤 {self.cliente.nombre} {self.cliente.apellido}".rstrip())
            if self.cliente.telefono:
                partes.append(f"📞 {self.cliente.telefono}")
        if self.direccion:
            partes.append(f"📍 {self.direccion}")
        url = self.maps_url()
        if url:
            partes.append(f"🗺️ {url}")
        return "\n".join(partes)
