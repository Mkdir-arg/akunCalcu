import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


DIAS_SEMANA = [
    (0, 'Lunes'),
    (1, 'Martes'),
    (2, 'Miércoles'),
    (3, 'Jueves'),
    (4, 'Viernes'),
    (5, 'Sábado'),
    (6, 'Domingo'),
]


class ConfiguracionAgente(models.Model):
    """Singleton (pk=1) con la configuración general del asistente de clientes."""

    nombre_firma = models.CharField(
        max_length=100, default='Matías Fariña', verbose_name='Nombre con el que firma',
    )
    instrucciones_tono = models.TextField(
        blank=True,
        verbose_name='Indicaciones de tono',
        help_text='Cómo habla el asistente: saludo, cierre, expresiones habituales, qué evitar.',
    )
    modelo_ia = models.CharField(
        max_length=60, default='gpt-5-mini', verbose_name='Modelo de IA (OpenAI)',
    )
    whatsapp_activo = models.BooleanField(default=False, verbose_name='Atiende WhatsApp')
    email_activo = models.BooleanField(default=False, verbose_name='Atiende email')
    instagram_activo = models.BooleanField(default=False, verbose_name='Atiende Instagram')
    modo_prueba = models.BooleanField(
        default=True,
        verbose_name='Modo prueba',
        help_text='Si está activo, el asistente solo responde a los números de prueba.',
    )
    numeros_prueba = models.TextField(
        blank=True,
        verbose_name='Números de prueba',
        help_text='Un número por línea, con código de país (ej. 5491155555555).',
    )
    derivar_a = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        verbose_name='Derivar a dirección',
        help_text='Quién recibe las conversaciones que el asistente no puede resolver.',
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuración del agente'
        verbose_name_plural = 'Configuración del agente'

    def __str__(self):
        return f'Configuración del agente ({self.nombre_firma})'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def obtener(cls):
        config, _ = cls.objects.get_or_create(pk=1)
        return config

    def lista_numeros_prueba(self):
        return [linea for linea in self.numeros_prueba.splitlines() if linea.strip()]


class FranjaBase(models.Model):
    dia_semana = models.PositiveSmallIntegerField(choices=DIAS_SEMANA, verbose_name='Día')
    hora_desde = models.TimeField(verbose_name='Desde')
    hora_hasta = models.TimeField(verbose_name='Hasta')

    class Meta:
        abstract = True
        ordering = ['dia_semana', 'hora_desde']

    def __str__(self):
        return f"{self.get_dia_semana_display()} {self.hora_desde:%H:%M}-{self.hora_hasta:%H:%M}"

    def _franjas_del_mismo_grupo(self):
        raise NotImplementedError

    def clean(self):
        if self.hora_desde is None or self.hora_hasta is None or self.dia_semana is None:
            return
        if self.hora_desde >= self.hora_hasta:
            raise ValidationError({'hora_hasta': 'La hora de fin tiene que ser posterior a la de inicio.'})
        if getattr(self, '_superposicion_validada_afuera', False):
            return
        otras = self._franjas_del_mismo_grupo().filter(
            dia_semana=self.dia_semana,
            hora_desde__lt=self.hora_hasta,
            hora_hasta__gt=self.hora_desde,
        )
        if self.pk:
            otras = otras.exclude(pk=self.pk)
        if otras.exists():
            raise ValidationError('Se superpone con otra franja del mismo día.')


class FranjaAtencion(FranjaBase):
    class Meta(FranjaBase.Meta):
        verbose_name = 'Franja de atención'
        verbose_name_plural = 'Franjas de atención'

    def _franjas_del_mismo_grupo(self):
        return FranjaAtencion.objects.all()


class DiaCerrado(models.Model):
    fecha = models.DateField(unique=True, verbose_name='Fecha')
    motivo = models.CharField(max_length=150, blank=True, verbose_name='Motivo')

    class Meta:
        verbose_name = 'Día cerrado'
        verbose_name_plural = 'Días cerrados'
        ordering = ['fecha']

    def __str__(self):
        return f"{self.fecha:%d/%m/%Y}" + (f" ({self.motivo})" if self.motivo else '')


class TecnicoVisita(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tecnico_visita',
        verbose_name='Técnico',
    )
    duracion_minutos = models.PositiveIntegerField(
        default=60, validators=[MinValueValidator(1)], verbose_name='Duración de la visita (min)',
    )
    cupo_por_franja = models.PositiveIntegerField(
        default=1, validators=[MinValueValidator(1)], verbose_name='Visitas por franja',
    )
    costo_visita = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Costo de la visita',
        help_text='0 = sin costo para el cliente.',
    )
    activo = models.BooleanField(default=True, verbose_name='Activo')
    notas = models.TextField(blank=True, verbose_name='Notas')

    class Meta:
        verbose_name = 'Técnico de visitas'
        verbose_name_plural = 'Técnicos de visitas'
        ordering = ['usuario__first_name', 'usuario__username']

    def __str__(self):
        return self.usuario.get_full_name() or self.usuario.username


class FranjaTecnico(FranjaBase):
    tecnico = models.ForeignKey(
        TecnicoVisita, on_delete=models.CASCADE, related_name='franjas', verbose_name='Técnico',
    )

    class Meta(FranjaBase.Meta):
        verbose_name = 'Franja del técnico'
        verbose_name_plural = 'Franjas del técnico'

    def _franjas_del_mismo_grupo(self):
        if not self.tecnico_id:
            return FranjaTecnico.objects.none()
        return FranjaTecnico.objects.filter(tecnico_id=self.tecnico_id)


class ZonaTecnico(models.Model):
    tecnico = models.ForeignKey(
        TecnicoVisita, on_delete=models.CASCADE, related_name='zonas', verbose_name='Técnico',
    )
    localidad = models.CharField(max_length=100, verbose_name='Localidad')
    provincia = models.ForeignKey(
        'core.Provincia', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='+', verbose_name='Provincia',
    )

    class Meta:
        verbose_name = 'Zona del técnico'
        verbose_name_plural = 'Zonas del técnico'
        ordering = ['localidad']
        constraints = [
            models.UniqueConstraint(fields=['tecnico', 'localidad'], name='agente_zona_tecnico_unica'),
        ]

    def __str__(self):
        return f"{self.localidad}" + (f" ({self.provincia})" if self.provincia_id else '')


class EntradaConocimiento(models.Model):
    tema = models.CharField(max_length=150, verbose_name='Tema')
    contenido = models.TextField(verbose_name='Contenido')
    activo = models.BooleanField(default=True, verbose_name='Activo')
    orden = models.PositiveIntegerField(default=0, verbose_name='Orden')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Entrada de conocimiento'
        verbose_name_plural = 'Base de conocimiento'
        ordering = ['orden', 'tema']

    def __str__(self):
        return self.tema


def normalizar_numeros(texto):
    """Deja un número por línea, solo dígitos, sin repetidos ni vacíos."""
    numeros = []
    for linea in (texto or '').splitlines():
        digitos = re.sub(r'\D', '', linea)
        if digitos and digitos not in numeros:
            numeros.append(digitos)
    return '\n'.join(numeros)
