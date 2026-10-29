from core.live import register

from .models import Cliente, Compra, Venta


register(
    key='ventas',
    queryset=lambda user: Venta.objects.filter(deleted_at__isnull=True),
    date_field='updated_at',
    permission='comercial.ventas',
)

# Cliente no tiene campo de modificación: las ediciones no se detectan, solo altas y bajas por count.
register(
    key='clientes',
    queryset=lambda user: Cliente.objects.filter(deleted_at__isnull=True),
    date_field='created_at',
    permission='comercial.clientes',
)

register(
    key='compras',
    queryset=lambda user: Compra.objects.filter(deleted_at__isnull=True),
    date_field='updated_at',
    permission='comercial.gastos',
)
