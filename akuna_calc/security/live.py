from core.live import register

from .models import AuditLog, Backup, HeartbeatIntegracion

# Backup no tiene updated_at: se cuentan solo los terminados (completo o fallido), así el
# cambio de estado al finalizar suma al count y el listado se entera.
register(
    key='backups',
    queryset=lambda user: Backup.objects.filter(status__in=['completed', 'failed']),
    date_field='created_at',
    permission='seguridad.backups',
)

register(
    key='auditoria',
    queryset=lambda user: AuditLog.objects.all(),
    date_field='timestamp',
    permission='seguridad.auditoria',
)

register(
    key='salud',
    queryset=lambda user: HeartbeatIntegracion.objects.all(),
    date_field='updated_at',
    permission='seguridad.salud',
)
