from core.live import register

from .models import Producto

register(
    key='catalogo-productos',
    queryset=lambda user: Producto.objects.all(),
    date_field='updated_at',
    permission='fabrica.interior',
)
