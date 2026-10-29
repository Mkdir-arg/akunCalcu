from django.contrib.auth import get_user_model

from core.live import register

from .models import PerfilAccesoUsuario

User = get_user_model()

register(
    key='usuarios',
    queryset=lambda user: User.objects.all(),
    date_field='date_joined',
    permission='configuracion.usuarios',
)

register(
    key='usuarios_perfiles',
    queryset=lambda user: PerfilAccesoUsuario.objects.all(),
    date_field='updated_at',
    permission='configuracion.usuarios',
)


def _solicitudes_del_vendedor(user):
    from solicitudes.models import SolicitudPresupuesto
    return SolicitudPresupuesto.objects.filter(
        vendedor=user, estado=SolicitudPresupuesto.ESTADO_ASIGNADA,
    )


register(
    key='inicio_solicitudes',
    queryset=_solicitudes_del_vendedor,
    date_field='updated_at',
)
