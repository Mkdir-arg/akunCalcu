"""Registro de fuentes de tiempo real.

Cada app declara las suyas en `<app>/live.py` (se importan solas al arrancar):

    from core.live import register
    from .models import Presupuesto

    register(
        key='presupuestos',
        queryset=lambda user: Presupuesto.objects.all(),
        date_field='updated_at',
        permission='presupuestos.view',
    )

El endpoint /core/api/live/ hace UNA consulta agregada por fuente pedida.
"""
from dataclasses import dataclass
from typing import Callable, Optional, Sequence, Union

from django.db.models import Count, Max

_REGISTRY = {}


@dataclass(frozen=True)
class LiveSource:
    key: str
    queryset: Callable
    date_field: str = 'updated_at'
    permission: Optional[Union[str, Sequence[str]]] = None

    def visible_for(self, user):
        if not self.permission:
            return True
        from usuarios.access_control import user_has_any_access
        return user_has_any_access(user, self.permission)

    def snapshot(self, user):
        data = self.queryset(user).aggregate(stamp=Max(self.date_field), count=Count('pk'))
        stamp = data['stamp']
        # date_field puede ser un pk (tablas legacy sin fecha de modificación).
        if stamp is not None:
            stamp = stamp.isoformat() if hasattr(stamp, 'isoformat') else str(stamp)
        return {'stamp': stamp, 'count': data['count']}


def register(key, queryset, date_field='updated_at', permission=None):
    """`queryset` es un callable `f(user) -> QuerySet` ya filtrado para ese usuario."""
    if not callable(queryset):
        raise TypeError('queryset debe ser un callable f(user) -> QuerySet')
    _REGISTRY[key] = LiveSource(key=key, queryset=queryset, date_field=date_field, permission=permission)


def unregister(key):
    _REGISTRY.pop(key, None)


def get_source(key):
    return _REGISTRY.get(key)


def all_sources():
    return dict(_REGISTRY)


def snapshots_for(user, keys):
    result = {}
    for key in keys:
        source = _REGISTRY.get(key)
        if source is None or not source.visible_for(user):
            continue
        result[key] = source.snapshot(user)
    return result


def _avisos_del_usuario(user):
    from .models import Aviso
    return Aviso.objects.filter(usuario=user)


# Ejemplo funcionando: el propio usuario ve "hay cambios" cuando le llega un aviso.
register(key='avisos', queryset=_avisos_del_usuario, date_field='fecha')
