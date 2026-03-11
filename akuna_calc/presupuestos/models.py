from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Presupuesto(models.Model):
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('enviado', 'Enviado'),
        ('confirmado', 'Confirmado'),
        ('vencido', 'Vencido'),
        ('cancelado', 'Cancelado'),
    ]

    numero = models.CharField(max_length=20, unique=True, verbose_name='Número')
    cliente = models.ForeignKey(
        'comercial.Cliente',
        on_delete=models.PROTECT,
        related_name='presupuestos',
        verbose_name='Cliente',
    )
    fecha_expiracion = models.DateField(verbose_name='Fecha de expiración')
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='borrador',
        verbose_name='Estado',
    )
    notas = models.TextField(blank=True, verbose_name='Notas')
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name='Total')
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='presupuestos_creados',
        verbose_name='Creado por',
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

    def recalcular_total(self):
        total = sum(item.precio_total for item in self.items.all())
        self.total = total
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

    def save(self, *args, **kwargs):
        self.precio_total = self.precio_unitario * self.cantidad
        super().save(*args, **kwargs)


class ComentarioPresupuesto(models.Model):
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
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Comentario'
        verbose_name_plural = 'Comentarios'
        ordering = ['created_at']

    def __str__(self):
        return f'Comentario de {self.autor} en {self.presupuesto.numero}'
