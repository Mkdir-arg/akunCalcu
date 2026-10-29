from core.live import register
from .models import Presupuesto

register(
    key='presupuestos',
    queryset=lambda user: Presupuesto.objects.filter(deleted_at__isnull=True),
    date_field='updated_at',
    permission='presupuestos.view',
)
