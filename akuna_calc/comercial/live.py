from core.live import register

from .models import Compra

# ==== M5 (compras) - inicio ====
register(
    key='compras',
    queryset=lambda user: Compra.objects.filter(deleted_at__isnull=True),
    date_field='updated_at',
    permission='comercial.gastos',
)
# ==== M5 (compras) - fin ====
