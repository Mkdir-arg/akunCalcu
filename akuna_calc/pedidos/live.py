from core.live import register

from .models import PedidoTelegram

register(
    key='pedidos_voz',
    queryset=lambda user: PedidoTelegram.objects.all(),
    date_field='updated_at',
)
