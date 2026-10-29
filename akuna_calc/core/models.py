from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class Provincia(models.Model):
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=10, unique=True)
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Provincia"
        verbose_name_plural = "Provincias"
        ordering = ['nombre']

class Aviso(models.Model):
    TIPO_INFO = 'info'
    TIPO_EXITO = 'exito'
    TIPO_ALERTA = 'alerta'
    TIPO_ERROR = 'error'
    TIPO_CHOICES = [
        (TIPO_INFO, 'Información'),
        (TIPO_EXITO, 'Éxito'),
        (TIPO_ALERTA, 'Alerta'),
        (TIPO_ERROR, 'Error'),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='avisos', verbose_name='Usuario',
    )
    tipo = models.CharField('Tipo', max_length=10, choices=TIPO_CHOICES, default=TIPO_INFO)
    texto = models.CharField('Texto', max_length=255)
    url = models.CharField('Enlace', max_length=500, blank=True)
    leido = models.BooleanField('Leído', default=False)
    fecha = models.DateTimeField('Fecha', default=timezone.now)

    class Meta:
        verbose_name = 'Aviso'
        verbose_name_plural = 'Avisos'
        ordering = ['-fecha', '-id']
        indexes = [
            models.Index(fields=['usuario', 'leido', '-fecha'], name='aviso_usuario_leido_idx'),
        ]

    def __str__(self):
        return f'{self.usuario_id} · {self.texto[:60]}'


class EdicionActiva(models.Model):
    """Quién tiene abierta una pantalla de edición. Vive en la base porque el
    caché local de cada worker de gunicorn no se comparte."""

    CADUCIDAD_SEGUNDOS = 60

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='ediciones_activas', verbose_name='Usuario',
    )
    recurso = models.CharField('Recurso', max_length=100, help_text='Formato app.modelo, por ejemplo presupuestos.presupuesto')
    object_id = models.CharField('ID del objeto', max_length=64)
    last_seen = models.DateTimeField('Última actividad', default=timezone.now)

    class Meta:
        verbose_name = 'Edición activa'
        verbose_name_plural = 'Ediciones activas'
        constraints = [
            models.UniqueConstraint(fields=['usuario', 'recurso', 'object_id'], name='edicion_activa_unica'),
        ]
        indexes = [
            models.Index(fields=['recurso', 'object_id', '-last_seen'], name='edicion_recurso_obj_idx'),
        ]

    def __str__(self):
        return f'{self.usuario_id} edita {self.recurso}:{self.object_id}'

    @classmethod
    def vigentes(cls, ahora=None):
        limite = (ahora or timezone.now()) - timedelta(seconds=cls.CADUCIDAD_SEGUNDOS)
        return cls.objects.filter(last_seen__gte=limite)
