from core.live import register

from .models import PedidoTelegram

register(
    key='pedidos_voz',
    queryset=lambda user: PedidoTelegram.objects.all(),
    date_field='updated_at',
    # pedidos:lista no tiene código propio; se usa el de Pedidos de Fábrica, que es desde
    # donde se enlaza y a quienes se avisa de cada pedido nuevo.
    permission='despiece.pedidos',
)
