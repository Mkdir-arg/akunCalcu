import json
import os
import secrets

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .forms import BorradorApiForm, NoticiaForm
from .models import Noticia
from .services import (
    marcar_leidas, modulo_label, modulo_url, publicadas_para, publicar, puede_gestionar, ultima_vista,
)

POR_PAGINA = 20


def _solo_staff(user):
    if not puede_gestionar(user):
        raise PermissionDenied


@login_required
def lista(request):
    tipo = request.GET.get('tipo', '')
    qs = publicadas_para(request.user).order_by('-publicada_en')
    if tipo in dict(Noticia.TIPO_CHOICES):
        qs = qs.filter(tipo=tipo)
    page_obj = Paginator(qs, POR_PAGINA).get_page(request.GET.get('page'))

    desde = ultima_vista(request.user)
    for n in page_obj:
        n.modulo_label = modulo_label(n.modulo)
        n.modulo_url = modulo_url(n.modulo, request.user) if n.modulo else None
        n.es_nueva = n.publicada_en and n.publicada_en > desde
    # Con filtro o en otra página puede haber no leídas que no se ven: no se marcan.
    if not tipo and page_obj.number == 1:
        marcar_leidas(request.user)

    return render(request, 'novedades/lista.html', {
        'page_obj': page_obj,
        'tipo_filter': tipo,
        'tipo_choices': Noticia.TIPO_CHOICES,
        'query': f'tipo={tipo}' if tipo else '',
    })


@login_required
@require_POST
def marcar_leidas_view(request):
    marcar_leidas(request.user)
    destino = request.POST.get('next', '')
    if not url_has_allowed_host_and_scheme(destino, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        destino = '/'
    return redirect(destino)


@login_required
def bandeja(request):
    _solo_staff(request.user)
    estado = request.GET.get('estado', Noticia.ESTADO_BORRADOR)
    qs = Noticia.objects.select_related('publicada_por').order_by('-creada_en')
    if estado in dict(Noticia.ESTADO_CHOICES):
        qs = qs.filter(estado=estado)
    else:
        estado = ''
    page_obj = Paginator(qs, POR_PAGINA).get_page(request.GET.get('page'))
    for n in page_obj:
        n.modulo_label = modulo_label(n.modulo)
    conteos = {e: Noticia.objects.filter(estado=e).count() for e, _ in Noticia.ESTADO_CHOICES}
    return render(request, 'novedades/bandeja.html', {
        'page_obj': page_obj,
        'estado_filter': estado,
        'estados': [(e, label, conteos[e]) for e, label in Noticia.ESTADO_CHOICES],
        'query': f'estado={estado}',
    })


def _guardar_segun_accion(request, form, noticia_nueva=False):
    accion = request.POST.get('accion', 'guardar')
    estado_anterior = form.instance.estado
    noticia = form.save(commit=False)
    if noticia_nueva:
        noticia.origen = Noticia.ORIGEN_MANUAL
    if accion == 'publicar':
        publicar(noticia, estado_anterior, request.user)
        messages.success(request, 'Noticia publicada. El equipo la va a ver al entrar.')
    elif accion == 'descartar':
        noticia.estado = Noticia.ESTADO_DESCARTADA
        noticia.publicada_en = None
        noticia.save()
        messages.success(request, 'Noticia descartada. No la ve nadie del equipo.')
    else:
        noticia.save()
        messages.success(request, 'Cambios guardados.')
    return noticia


@login_required
def editar(request, pk):
    _solo_staff(request.user)
    noticia = get_object_or_404(Noticia, pk=pk)
    form = NoticiaForm(request.POST or None, instance=noticia)
    if request.method == 'POST' and form.is_valid():
        _guardar_segun_accion(request, form)
        return redirect('novedades:bandeja')
    return render(request, 'novedades/form.html', {'form': form, 'noticia': noticia})


@login_required
def crear(request):
    _solo_staff(request.user)
    form = NoticiaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        _guardar_segun_accion(request, form, noticia_nueva=True)
        return redirect('novedades:bandeja')
    return render(request, 'novedades/form.html', {'form': form, 'noticia': None})


@csrf_exempt
@require_POST
def api_borrador(request):
    """La GitHub Action avisa que llegó un cambio a main. Header X-Bot-Secret = NOVEDADES_BOT_SECRET."""
    esperado = os.environ.get('NOVEDADES_BOT_SECRET', '')
    recibido = request.META.get('HTTP_X_BOT_SECRET', '')
    if not esperado or not secrets.compare_digest(recibido.encode('utf-8'), esperado.encode('utf-8')):
        return JsonResponse({'error': 'forbidden'}, status=403)

    try:
        datos = json.loads(request.body or b'{}')
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({'error': 'json invalido'}, status=400)
    if not isinstance(datos, dict):
        return JsonResponse({'error': 'json invalido'}, status=400)

    form = BorradorApiForm(datos)
    if not form.is_valid():
        return JsonResponse({'error': 'datos invalidos', 'detalle': form.errors.get_json_data()}, status=400)
    d = form.cleaned_data

    noticia, creada = Noticia.objects.get_or_create(
        sha=d['sha'],
        defaults={
            'titulo': d['titulo'],
            'texto': d['texto_usuario'],
            'texto_tecnico': d['texto_tecnico'],
            'pr_numero': d['pr_numero'],
            'autor_git': d['autor'],
            'origen': Noticia.ORIGEN_PR if d['pr_numero'] else Noticia.ORIGEN_PUSH,
        },
    )
    return JsonResponse({'id': noticia.pk, 'creada': creada}, status=201 if creada else 200)
