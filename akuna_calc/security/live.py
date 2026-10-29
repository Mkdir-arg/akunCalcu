from core.live import register

from .models import AuditLog, Backup, HeartbeatIntegracion

register(
    key='backups',
    queryset=lambda user: Backup.objects.all(),
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
