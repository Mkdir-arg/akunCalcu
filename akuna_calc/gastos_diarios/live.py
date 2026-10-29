from core.live import register

from .models import GastoDiario

register(
    key='gastos',
    queryset=lambda user: GastoDiario.objects.exclude(estado='borrador'),
    date_field='updated_at',
    permission='gastos_diarios.view',
)
