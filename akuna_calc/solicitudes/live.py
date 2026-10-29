from core.live import register

from .models import SolicitudPresupuesto

register(
    key='solicitudes',
    queryset=lambda user: SolicitudPresupuesto.objects.all(),
    date_field='updated_at',
    permission='solicitudes.view',
)
