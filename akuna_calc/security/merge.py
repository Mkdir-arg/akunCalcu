"""Fusión de registros duplicados (merge): reasigna todo lo relacionado de un
registro ORIGEN a un DESTINO y da de baja lógica al origen.

La reasignación es genérica: recorre las relaciones inversas (FK / OneToOne) que
apuntan al modelo, así cubre todas las tablas actuales y cualquier FK futura sin
tener que enumerarlas. El destino no se modifica (solo recibe los registros)."""

from django.db import transaction


def get_merge_entities():
    """Entidades fusionables. `proveedor` y `cuenta` usan el mismo modelo (Cuenta);
    `proveedor` solo acota la lista a las cuentas de tipo proveedores."""
    from comercial.models import Cliente, Cuenta
    return {
        'cliente': {
            'label': 'Cliente',
            'model': Cliente,
            'queryset': Cliente.objects.filter(deleted_at__isnull=True).order_by('apellido', 'nombre'),
        },
        'proveedor': {
            'label': 'Proveedor',
            'model': Cuenta,
            'queryset': Cuenta.objects.filter(
                deleted_at__isnull=True, tipo_cuenta__tipo='proveedores',
            ).order_by('nombre'),
        },
        'cuenta': {
            'label': 'Cuenta',
            'model': Cuenta,
            'queryset': Cuenta.objects.filter(deleted_at__isnull=True).order_by('nombre'),
        },
    }


def _fk_rels(model):
    """Relaciones inversas FK/OneToOne (concretas, no M2M) que apuntan al modelo."""
    rels = []
    for rel in model._meta.related_objects:
        if rel.many_to_many:
            continue
        if not getattr(rel.field, 'concrete', True):
            continue
        rels.append(rel)
    return rels


def preview_merge(instance):
    """Devuelve [{label, count}] de los registros relacionados que se moverían."""
    resultado = []
    for rel in _fk_rels(type(instance)):
        modelo = rel.related_model
        fname = rel.field.name
        count = modelo._base_manager.filter(**{fname: instance}).count()
        if count:
            resultado.append({'label': str(modelo._meta.verbose_name_plural), 'count': count})
    return resultado


@transaction.atomic
def merge_records(origen, destino):
    """Reasigna los registros relacionados de `origen` a `destino` y da de baja al
    origen. Atómico. Devuelve [(label_modelo, cantidad)] de lo movido."""
    if origen.pk == destino.pk:
        raise ValueError('El origen y el destino no pueden ser el mismo registro.')
    if type(origen) is not type(destino):
        raise ValueError('El origen y el destino deben ser del mismo tipo.')

    movidos = []
    for rel in _fk_rels(type(origen)):
        modelo = rel.related_model
        fname = rel.field.name
        n = modelo._base_manager.filter(**{fname: origen}).update(**{fname: destino})
        if n:
            movidos.append((str(modelo._meta.verbose_name_plural), n))

    origen.delete()  # baja lógica: el delete() de estos modelos setea deleted_at
    return movidos
