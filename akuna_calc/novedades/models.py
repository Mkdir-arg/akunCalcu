from django.conf import settings
from django.db import models


class Noticia(models.Model):
    TIPO_NUEVO = 'nuevo'
    TIPO_MEJORA = 'mejora'
    TIPO_ARREGLO = 'arreglo'
    TIPO_CHOICES = [
        (TIPO_NUEVO, 'Nuevo'),
        (TIPO_MEJORA, 'Mejora'),
        (TIPO_ARREGLO, 'Arreglo'),
    ]

    ESTADO_BORRADOR = 'borrador'
    ESTADO_PUBLICADA = 'publicada'
    ESTADO_DESCARTADA = 'descartada'
    ESTADO_CHOICES = [
        (ESTADO_BORRADOR, 'Borrador'),
        (ESTADO_PUBLICADA, 'Publicada'),
        (ESTADO_DESCARTADA, 'Descartada'),
    ]

    ORIGEN_PUSH = 'push'
    ORIGEN_PR = 'pr'
    ORIGEN_MANUAL = 'manual'
    ORIGEN_CHOICES = [
        (ORIGEN_PUSH, 'Push a main'),
        (ORIGEN_PR, 'Pull request'),
        (ORIGEN_MANUAL, 'Manual'),
    ]

    titulo = models.CharField('Título', max_length=200)
    texto = models.TextField('Texto', blank=True)
    tipo = models.CharField('Tipo', max_length=10, choices=TIPO_CHOICES, default=TIPO_MEJORA)
    # Clave de usuarios.access_control.ACCESS_MODULES; vacío = General (la ven todos).
    modulo = models.CharField('Módulo', max_length=40, blank=True)
    estado = models.CharField('Estado', max_length=12, choices=ESTADO_CHOICES, default=ESTADO_BORRADOR, db_index=True)

    origen = models.CharField('Origen', max_length=8, choices=ORIGEN_CHOICES, default=ORIGEN_MANUAL)
    sha = models.CharField('Commit', max_length=40, unique=True, null=True, blank=True)
    pr_numero = models.PositiveIntegerField('Nº de PR', null=True, blank=True)
    texto_tecnico = models.TextField('Texto técnico (GitHub)', blank=True)
    autor_git = models.CharField('Autor en GitHub', max_length=100, blank=True)

    creada_en = models.DateTimeField('Creada', auto_now_add=True)
    publicada_en = models.DateTimeField('Publicada', null=True, blank=True, db_index=True)
    publicada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name='Publicada por', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='noticias_publicadas',
    )

    class Meta:
        verbose_name = 'Noticia'
        verbose_name_plural = 'Noticias'
        ordering = ['-publicada_en', '-creada_en']

    def __str__(self):
        return f'{self.titulo} ({self.get_estado_display()})'

    @property
    def origen_corto(self):
        if self.origen == self.ORIGEN_PR and self.pr_numero:
            return f'PR #{self.pr_numero}'
        if self.origen == self.ORIGEN_MANUAL:
            return 'Manual'
        return 'Push'

    @property
    def sha_corto(self):
        return (self.sha or '')[:7]


class LecturaNovedades(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, verbose_name='Usuario', on_delete=models.CASCADE,
        related_name='lectura_novedades',
    )
    ultima_vista = models.DateTimeField('Última vez que vio las novedades')

    class Meta:
        verbose_name = 'Lectura de novedades'
        verbose_name_plural = 'Lecturas de novedades'

    def __str__(self):
        return f'{self.usuario} · {self.ultima_vista:%d/%m/%Y %H:%M}'
