from calendar import monthrange
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
        ('visita', 'Visita'),
        ('vencimiento', 'Vencimiento'),
        ('cobro', 'Cobro'),
        ('otro', 'Otro'),
    ]
    RECURRENCIA_CHOICES = [
        ('ninguna', 'Sin repetir'),
        ('diaria', 'Diaria'),
        ('semanal', 'Semanal'),
        ('mensual', 'Mensual'),
    ]
    ESTADO_CHOICES = [
        ('programado', 'Programado'),
        ('enviado', 'Enviado'),
        ('cancelado', 'Cancelado'),
    ]

    titulo = models.CharField(max_length=200, verbose_name="Título")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    tipo = models.CharField(
        max_length=20, choices=TIPO_CHOICES, default='otro', verbose_name="Tipo",
    )
    fecha_evento = models.DateField(verbose_name="Fecha del evento")
    hora_envio = models.TimeField(verbose_name="Hora de envío")
    anticipacion_dias = models.PositiveIntegerField(
        default=0,
        verbose_name="Anticipación (días antes)",
        help_text="Avisar X días antes de la fecha. Solo aplica a eventos sin repetir.",
    )
    recurrencia = models.CharField(
        max_length=20, choices=RECURRENCIA_CHOICES, default='ninguna', verbose_name="Recurrencia",
    )
    destinatarios = models.ManyToManyField(
        'gastos_diarios.NumeroAutorizado',
        related_name='eventos_agenda',
        verbose_name="Destinatarios",
    )
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

    def _corresponde(self, fecha):
        """Si un evento recurrente debe dispararse en la fecha dada."""
        if fecha < self.fecha_evento:
            return False
        if self.recurrencia == 'diaria':
            return True
        if self.recurrencia == 'semanal':
            return fecha.weekday() == self.fecha_evento.weekday()
        if self.recurrencia == 'mensual':
            ultimo_dia = monthrange(fecha.year, fecha.month)[1]
            return fecha.day == min(self.fecha_evento.day, ultimo_dia)
        return False

    def _enviado_hoy(self, ahora):
        if not self.ultimo_envio:
            return False
        return timezone.localtime(self.ultimo_envio).date() == ahora.date()

    def esta_pendiente(self, ahora=None):
        ahora = ahora or timezone.localtime()
        if not self.activo or self.estado == 'cancelado':
            return False
        if self.recurrencia == 'ninguna':
            if self.estado != 'programado':
                return False
            return self._aware(self.fecha_recordatorio()) <= ahora
        # Recurrente: corresponde hoy, ya pasó la hora y no se envió hoy
        if not self._corresponde(ahora.date()):
            return False
        if self._aware(ahora.date()) > ahora:
            return False
        return not self._enviado_hoy(ahora)

    def proximo_envio(self):
        """Próximo datetime de envío, para mostrar en el listado."""
        ahora = timezone.localtime()
        if self.recurrencia == 'ninguna':
            if self.estado != 'programado':
                return None
            return self._aware(self.fecha_recordatorio())
        for i in range(0, 366):
            dia = ahora.date() + timedelta(days=i)
            if not self._corresponde(dia):
                continue
            candidato = self._aware(dia)
            if dia == ahora.date() and (self._enviado_hoy(ahora) or candidato <= ahora):
                continue
            return candidato
        return None

    def marcar_enviado(self, ahora=None):
        ahora = ahora or timezone.now()
        self.ultimo_envio = ahora
        if self.recurrencia == 'ninguna':
            self.estado = 'enviado'
        self.save(update_fields=['ultimo_envio', 'estado', 'updated_at'])

    def mensaje(self):
        """Texto del recordatorio que se manda por WhatsApp."""
        partes = [f"🔔 {self.get_tipo_display()}: {self.titulo}"]
        if self.descripcion:
            partes.append(self.descripcion)
        partes.append(f"📅 {self.fecha_evento.strftime('%d/%m/%Y')}")
        return "\n".join(partes)
