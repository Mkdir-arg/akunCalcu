"""APIs del resumen de la dirección para n8n (REQ-071). Header X-Bot-Secret = RESUMEN_BOT_SECRET."""
import json
import os
import secrets
from datetime import date

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .forms import GuardarResumenForm
from .models import Resumen
from .services import PERIODOS, calcular_datos, destinatarios, rango


def _secreto_valido(request):
    esperado = os.environ.get('RESUMEN_BOT_SECRET', '')
    recibido = request.META.get('HTTP_X_BOT_SECRET', '')
    return bool(esperado) and secrets.compare_digest(recibido.encode('utf-8'), esperado.encode('utf-8'))


def _prohibido():
    return JsonResponse({'error': 'forbidden'}, status=403)


@require_GET
def api_datos(request):
    if not _secreto_valido(request):
        return _prohibido()
    periodo = request.GET.get('periodo', 'dia')
    if periodo not in PERIODOS:
        return JsonResponse({'error': 'periodo invalido'}, status=400)
    fecha = None
    if request.GET.get('fecha'):
        try:
            fecha = date.fromisoformat(request.GET['fecha'])
        except ValueError:
            return JsonResponse({'error': 'fecha invalida'}, status=400)
    datos = calcular_datos(periodo, fecha)
    return JsonResponse({'destinatarios': destinatarios(), 'datos': datos})


@csrf_exempt
@require_POST
def api_guardar(request):
    if not _secreto_valido(request):
        return _prohibido()
    try:
        cuerpo = json.loads(request.body or b'{}')
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({'error': 'json invalido'}, status=400)
    if not isinstance(cuerpo, dict):
        return JsonResponse({'error': 'json invalido'}, status=400)
    if isinstance(cuerpo.get('datos'), (dict, list)):
        cuerpo['datos'] = json.dumps(cuerpo['datos'])

    form = GuardarResumenForm(cuerpo)
    if not form.is_valid():
        return JsonResponse({'error': 'datos invalidos', 'detalle': form.errors.get_json_data()}, status=400)
    d = form.cleaned_data
    desde, hasta = rango(d['periodo'], d['hasta'])
    resumen, creado = Resumen.objects.update_or_create(
        periodo=d['periodo'], hasta=hasta,
        defaults={'desde': desde, 'texto': d['texto'], 'datos': d['datos'] or {}},
    )
    return JsonResponse({'id': resumen.pk, 'creado': creado}, status=201 if creado else 200)


@require_GET
def api_ultimo(request):
    """Último resumen para el teléfono que tocó «Ver resumen». Otro número → 404, sin pistas."""
    if not _secreto_valido(request):
        return _prohibido()
    telefono = ''.join(c for c in request.GET.get('telefono', '') if c.isdigit())
    resumen = Resumen.objects.first()
    if not telefono or telefono not in destinatarios() or resumen is None:
        return JsonResponse({'error': 'no encontrado'}, status=404)
    if telefono not in resumen.abierto_por:
        resumen.abierto_por = [*resumen.abierto_por, telefono]
        resumen.save(update_fields=['abierto_por', 'updated_at'])
    return JsonResponse({'id': resumen.pk, 'periodo': resumen.periodo, 'texto': resumen.texto})
