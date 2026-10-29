from core.live import register
from .models import Factura

register(
    key='facturas',
    queryset=lambda user: Factura.objects.all(),
    date_field='updated_at',
    permission='facturacion.facturas',
)
