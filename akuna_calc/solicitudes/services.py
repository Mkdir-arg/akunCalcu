from django.contrib.auth import get_user_model
from django.db import transaction

from .models import ConfiguracionSolicitudes


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
