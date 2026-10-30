from core.live import register

from .models import OrdenFabricacion, PedidoFabrica

register(
    key='pedidos_fabrica',
    queryset=lambda user: PedidoFabrica.objects.all(),
    date_field='updated_at',
    permission=['despiece.pedidos', 'fabrica.pedidos_gestion', 'fabrica.tablero'],
)

# REQ-063: el avance del taller (etapas) cambia las órdenes sin tocar la cabecera.
register(
    key='ordenes_fabrica',
    queryset=lambda user: OrdenFabricacion.objects.all(),
    date_field='updated_at',
    permission=['despiece.pedidos', 'fabrica.pedidos_gestion', 'fabrica.tablero'],
)
