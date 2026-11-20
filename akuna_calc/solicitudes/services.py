import re
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from .models import ConfiguracionSolicitudes, SolicitudPresupuesto

VENTANA_REENVIO = timedelta(hours=24)
# Los clientes escriben el mismo número con y sin 011/15/+54: se comparan los
# últimos 8 dígitos, que en Argentina son el abonado.
DIGITOS_TELEFONO = 8


def _clave_telefono(telefono):
    digitos = re.sub(r'\D', '', telefono or '')
    return digitos[-DIGITOS_TELEFONO:] if len(digitos) >= DIGITOS_TELEFONO else ''


def buscar_reenvio(email, telefono, ahora=None):
    """Solicitud no descartada del mismo cliente (email o teléfono) recibida en las
    últimas 24 h, o None. El formulario web manda un mail nuevo (otro hilo de Gmail)
    cada vez que el cliente aprieta Enviar, así que el hilo solo no alcanza."""
    email = (email or '').strip().lower()
    clave_tel = _clave_telefono(telefono)
    if not email and not clave_tel:
        return None
    desde = (ahora or timezone.now()) - VENTANA_REENVIO
    candidatas = (
        SolicitudPresupuesto.objects
        .filter(fecha_recepcion__gte=desde)
        .exclude(estado=SolicitudPresupuesto.ESTADO_DESCARTADA)
        .order_by('fecha_recepcion')
    )
    for solicitud in candidatas:
        if email and solicitud.email.strip().lower() == email:
            return solicitud
        if clave_tel and _clave_telefono(solicitud.telefono) == clave_tel:
            return solicitud
    return None


def vendedores_pool():
    """Queryset de usuarios que entran en la rotación de solicitudes.

    Criterio: rol de sistema con código 'vendedor' y activo, usuario activo y con
    email cargado (el email es el destino del reenvío del pedido).
    """
    User = get_user_model()
    return (
        User.objects.filter(
            perfil_acceso__rol__codigo='vendedor',
            perfil_acceso__rol__activo=True,
            is_active=True,
        )
        .exclude(email='')
        .order_by('id')
    )


@transaction.atomic
def asignar_siguiente_vendedor():
    """Devuelve el próximo vendedor de la rotación (round-robin) o None si no hay pool.

    Toma el puntero con select_for_update para que dos solicitudes que llegan a la
    vez no reciban el mismo vendedor.
    """
    config, _ = ConfiguracionSolicitudes.objects.select_for_update().get_or_create(pk=1)
    vendedores = list(vendedores_pool())
    if not vendedores:
        return None
    ids = [v.pk for v in vendedores]
    ultimo = config.ultimo_vendedor_id
    idx = (ids.index(ultimo) + 1) % len(ids) if ultimo in ids else 0
    elegido = vendedores[idx]
    config.ultimo_vendedor = elegido
    config.save(update_fields=['ultimo_vendedor', 'updated_at'])
    return elegido
