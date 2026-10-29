import random
import re
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from . import live
from .models import Aviso, EdicionActiva

MAX_KEYS = 20
MAX_AVISOS = 10
RECURSO_RE = re.compile(r'^[a-z0-9_]{1,50}\.[a-z0-9_]{1,50}$')
OBJECT_ID_RE = re.compile(r'^[A-Za-z0-9_-]{1,64}$')
# Las filas vencidas de EdicionActiva se borran de vez en cuando (1 de cada N consultas
# con presencia), para no sumar una consulta en cada poll.
PURGA_PROBABILIDAD = 0.02
PURGA_ANTIGUEDAD = timedelta(hours=1)


def get_dolar():
    """Dólar oficial (BNA). Hoy la app lo trae desde el navegador (dolarapi.com);
    mientras no haya fuente en servidor devuelve None y live.js usa ese mismo origen."""
    return None


def get_kpis(user):
    """Punto de extensión para KPIs del tablero."""
    return {}


def _presencia(user, edit):
    if not edit or ':' not in edit:
        return None
    recurso, _, object_id = edit.partition(':')
    if not RECURSO_RE.match(recurso) or not OBJECT_ID_RE.match(object_id):
        return None
    ahora = timezone.now()
    propia = EdicionActiva.objects.filter(usuario=user, recurso=recurso, object_id=object_id)
    if not propia.update(last_seen=ahora):
        try:
            with transaction.atomic():
                EdicionActiva.objects.create(
                    usuario=user, recurso=recurso, object_id=object_id, last_seen=ahora)
        except IntegrityError:
            propia.update(last_seen=ahora)
    if random.random() < PURGA_PROBABILIDAD:
        EdicionActiva.objects.filter(last_seen__lt=ahora - PURGA_ANTIGUEDAD).delete()
    otros = (
        EdicionActiva.vigentes(ahora)
        .filter(recurso=recurso, object_id=object_id)
        .exclude(usuario=user)
        .select_related('usuario')
    )
    return {
        'recurso': recurso,
        'object_id': object_id,
        'otros': [{'usuario': e.usuario.get_username()} for e in otros],
    }


@login_required
@require_GET
def live_poll(request):
    keys = [k.strip() for k in request.GET.get('keys', '').split(',') if k.strip()][:MAX_KEYS]
    user = request.user

    unread = Aviso.objects.filter(usuario=user, leido=False)
    avisos = [
        {'id': a.pk, 'tipo': a.tipo, 'texto': a.texto, 'url': a.url, 'fecha': a.fecha.isoformat()}
        for a in unread[:MAX_AVISOS]
    ]
    # Si entraron todos en la página no hace falta el COUNT aparte.
    unread_count = len(avisos) if len(avisos) < MAX_AVISOS else unread.count()
    payload = {
        'sources': live.snapshots_for(user, keys),
        'avisos': {'count': unread_count, 'items': avisos},
        'dolar': get_dolar(),
        'kpis': get_kpis(user),
        'edit': _presencia(user, request.GET.get('edit', '')),
        'server_time': timezone.now().isoformat(),
    }
    return JsonResponse(payload)


@login_required
@require_POST
def aviso_leido(request):
    """POST con `id=<n>` marca ese aviso; `id=all` marca todos. Solo los propios."""
    target = request.POST.get('id', '')
    qs = Aviso.objects.filter(usuario=request.user, leido=False)
    if target != 'all':
        if not target.isdigit():
            return JsonResponse({'detail': 'id inválido'}, status=400)
        qs = qs.filter(pk=int(target))
    marcados = qs.update(leido=True)
    return JsonResponse({'marcados': marcados})
