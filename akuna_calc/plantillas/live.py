from core.live import register

from .models import PedidoFabrica

register(
    key='pedidos_fabrica',
    queryset=lambda user: PedidoFabrica.objects.all(),
    date_field='updated_at',
    permission='despiece.pedidos',
)
