from django.db.models import Q
from django.utils import timezone

from usuarios.access_control import (
    ACCESS_CODE_METADATA, ACCESS_MODULES, get_effective_access_codes, user_has_full_access,
)

from .models import LecturaNovedades, Noticia


def modulo_choices():
    return [('', 'General (todos)')] + [(m['key'], m['label']) for m in ACCESS_MODULES]


def modulo_label(key):
    if not key:
        return 'General'
    for m in ACCESS_MODULES:
        if m['key'] == key:
            return m['label']
    return key


def puede_gestionar(user):
    """Bandeja de novedades: solo acceso total. `is_staff` no alcanza: lo tienen usuarios comunes
    con permisos heredados (ver LEGACY_STAFF_ACCESS_CODES)."""
    return user_has_full_access(user)


def modulo_url(key, user):
    """URL del primer ítem del módulo al que el usuario tiene acceso, para el enlace «Ir a …»."""
    from django.urls import NoReverseMatch, reverse
    codes = get_effective_access_codes(user)
    for m in ACCESS_MODULES:
        if m['key'] != key:
            continue
        for item in m['items']:
            if item['code'] in codes:
                try:
                    return reverse(item['route_name'])
                except NoReverseMatch:
                    return None
    return None


def modulos_visibles(user):
    codes = get_effective_access_codes(user)
    return {ACCESS_CODE_METADATA[c]['group_key'] for c in codes if c in ACCESS_CODE_METADATA}


def publicadas_para(user):
    """Noticias publicadas que el usuario puede ver: las generales y las de sus módulos."""
    return Noticia.objects.filter(estado=Noticia.ESTADO_PUBLICADA).filter(
        Q(modulo='') | Q(modulo__in=modulos_visibles(user))
    )


def ultima_vista(user):
    """Desde cuándo cuentan las no leídas. Sin registro: desde el alta del usuario."""
    try:
        return user.lectura_novedades.ultima_vista
    except LecturaNovedades.DoesNotExist:
        return user.date_joined


def no_leidas_para(user):
    return publicadas_para(user).filter(publicada_en__gt=ultima_vista(user))


def marcar_leidas(user):
    LecturaNovedades.objects.update_or_create(usuario=user, defaults={'ultima_vista': timezone.now()})


def publicar(noticia, estado_anterior, user):
    """Al pasar a publicada toma la fecha de hoy, así cuenta como no leída para todos."""
    if estado_anterior != Noticia.ESTADO_PUBLICADA or not noticia.publicada_en:
        noticia.publicada_en = timezone.now()
    noticia.estado = Noticia.ESTADO_PUBLICADA
    noticia.publicada_por = user
    noticia.save()
