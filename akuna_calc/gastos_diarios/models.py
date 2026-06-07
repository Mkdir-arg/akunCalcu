from django.db import models


class NumeroAutorizado(models.Model):
    numero = models.CharField(
        max_length=30,
        unique=True,
        verbose_name="Número de WhatsApp",
        help_text="Sin el sufijo @s.whatsapp.net. Ej: 5491155555555",
    )
    nombre = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Nombre / Referencia",
    )
    activo = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.nombre:
            return f"{self.nombre} ({self.numero})"
        return self.numero

    class Meta:
        verbose_name = "Número autorizado"
        verbose_name_plural = "Números autorizados"
        ordering = ['nombre', 'numero']


class GastoDiario(models.Model):
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('en_espera', 'En espera'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
    ]

    # Espejo de comercial.TipoCuenta.TIPOS_CUENTA. Se replica acá para no
    # acoplar el modelo (y su migración) a la app comercial.
    TIPO_CUENTA_CHOICES = [
        ('colocadores', 'Colocadores'),
        ('colaboradores', 'Colaboradores'),
        ('fletes', 'Fletes'),
        ('retiros_propios', 'Retiros Propios'),
        ('varios', 'Varios'),
        ('proveedores', 'Proveedores'),
        ('caja_chica', 'Caja Chica'),
    ]

    descripcion = models.CharField(max_length=300, verbose_name="Descripción")
    monto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Monto",
    )
    fecha = models.DateField(auto_now_add=True, verbose_name="Fecha")
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='en_espera',
        verbose_name="Estado",
    )
    tipo_cuenta = models.CharField(
        max_length=20,
        choices=TIPO_CUENTA_CHOICES,
        blank=True,
        verbose_name="Clasificación (Tipo de Cuenta)",
        help_text="Tipo de cuenta donde se registra el gasto al aprobarlo. Vacío = sin clasificar.",
    )
    numero_origen = models.CharField(
        max_length=30,
        verbose_name="Número origen",
    )
    audio_id = models.CharField(
        max_length=120,
        blank=True,
        verbose_name="ID de audio (WhatsApp)",
    )
    transcripcion = models.TextField(
        blank=True,
        verbose_name="Transcripción del audio",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"#{self.pk} {self.descripcion} - ${self.monto} ({self.get_estado_display()})"

    class Meta:
        verbose_name = "Gasto diario"
        verbose_name_plural = "Gastos diarios"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['audio_id', 'numero_origen'], name='gd_audio_numero_idx'),
        ]
