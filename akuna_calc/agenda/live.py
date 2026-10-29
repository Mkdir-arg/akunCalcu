from core.live import register

from .models import EventoAgenda

register(
    key='eventos',
    queryset=lambda user: EventoAgenda.objects.filter(activo=True),
    date_field='updated_at',
    permission='agenda.view',
)
