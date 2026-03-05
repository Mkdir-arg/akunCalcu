from django.db import models


class PedidoTelegram(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('confirmado', 'Confirmado'),
        ('cancelado', 'Cancelado'),
    ]

    telegram_chat_id = models.CharField(max_length=50, verbose_name="Chat ID")
    telegram_username = models.CharField(max_length=100, blank=True, verbose_name="Usuario Telegram")
    transcripcion_original = models.TextField(verbose_name="Transcripción del audio")
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pendiente',
        verbose_name="Estado",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Pedido #{self.pk} - {self.telegram_username or self.telegram_chat_id} ({self.get_estado_display()})"

    class Meta:
        verbose_name = "Pedido Telegram"
        verbose_name_plural = "Pedidos Telegram"
        ordering = ['-created_at']


class ItemPedidoTelegram(models.Model):
    pedido = models.ForeignKey(
        PedidoTelegram,
        on_delete=models.CASCADE,
        related_name='items',
    )
    descripcion = models.CharField(max_length=300, verbose_name="Descripción")
    cantidad = models.PositiveIntegerField(default=1, verbose_name="Cantidad")

    def __str__(self):
        return f"{self.cantidad}x {self.descripcion}"

    class Meta:
        verbose_name = "Ítem de Pedido"
        verbose_name_plural = "Ítems de Pedido"
