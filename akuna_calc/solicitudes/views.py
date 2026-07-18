import json
import os

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .forms import ReasignarSolicitudForm
from .models import SolicitudPresupuesto
from .services import asignar_siguiente_vendedor, vendedores_pool


def _validar_token(request):
    token = request.headers.get('X-Bot-Secret', '')
    secret = os.environ.get('SOLICITUDES_BOT_SECRET', '')
    return bool(secret) and token == secret


def _payload_solicitud(solicitud, duplicada=False):
    vendedor = solicitud.vendedor
    vendedor_data = None
    if vendedor:
        vendedor_data = {
            'nombre': vendedor.get_full_name() or vendedor.username,
            'email': vendedor.email,
            'whatsapp': solicitud.numero_whatsapp_vendedor,
        }
    return {
        'ok': True,
        'duplicada': duplicada,
        'solicitud_id': solicitud.pk,
        'estado': solicitud.estado,
        'vendedor': vendedor_data,
        'mensaje_whatsapp': solicitud.mensaje_whatsapp(),
    }


# ---------------------------------------------------------------------------
# API para n8n (auth por header X-Bot-Secret)
# ---------------------------------------------------------------------------

@csrf_exempt
@require_POST
def api_crear(request):
    """Crea una solicitud, la asigna al próximo vendedor (round-robin) y devuelve
    sus datos para que n8n reenvíe el mail y avise por WhatsApp. Idempotente por
    gmail_thread_id (si n8n reintenta, no duplica)."""
    if not _validar_token(request):
        return JsonResponse({'error': 'No autorizado'}, status=401)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    thread_id = (data.get('gmail_thread_id') or '').strip()
    if thread_id:
        existente = SolicitudPresupuesto.objects.filter(gmail_thread_id=thread_id).first()
        if existente:
            return JsonResponse(_payload_solicitud(existente, duplicada=True))

    solicitud = SolicitudPresupuesto(
        nombre_cliente=(data.get('nombre_cliente') or '').strip()[:200],
        email=(data.get('email') or '').strip()[:254],
        telefono=(data.get('telefono') or '').strip()[:50],
        asunto=(data.get('asunto') or '').strip()[:300],
        mensaje=data.get('mensaje') or '',
        gmail_thread_id=thread_id,
        origen='email',
    )

    vendedor = asignar_siguiente_vendedor()
    if vendedor:
        solicitud.vendedor = vendedor
        solicitud.estado = SolicitudPresupuesto.ESTADO_ASIGNADA
        solicitud.fecha_asignacion = timezone.now()
    else:
        solicitud.estado = SolicitudPresupuesto.ESTADO_SIN_ASIGNAR
    solicitud.save()

    return JsonResponse(_payload_solicitud(solicitud), status=201)


@csrf_exempt
@require_POST
def api_recordatorios(request):
    """Devuelve las solicitudes sin contestar que necesitan recordatorio (>= 1h del
    último aviso) con el WhatsApp del vendedor, para el cron horario de n8n."""
    if not _validar_token(request):
        return JsonResponse({'error': 'No autorizado'}, status=401)

    data = []
    for solicitud in SolicitudPresupuesto.objects.pendientes_recordatorio():
        whatsapp = solicitud.numero_whatsapp_vendedor
        if not whatsapp:
            continue
        data.append({
            'id': solicitud.pk,
            'vendedor': solicitud.vendedor.get_full_name() or solicitud.vendedor.username,
            'whatsapp': whatsapp,
            'mensaje': solicitud.mensaje_recordatorio(),
        })

    return JsonResponse({'ok': True, 'solicitudes': data, 'cantidad': len(data)})


@csrf_exempt
@require_POST
def api_marcar_recordatorio(request):
    """Marca como enviado el recordatorio de las solicitudes indicadas (n8n lo llama
    después de mandar los WhatsApp)."""
    if not _validar_token(request):
        return JsonResponse({'error': 'No autorizado'}, status=401)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    ids = data.get('ids', [])
    if not isinstance(ids, list):
        return JsonResponse({'error': 'ids debe ser una lista'}, status=400)

    ahora = timezone.now()
    marcados = SolicitudPresupuesto.objects.filter(pk__in=ids).update(
        ultimo_recordatorio=ahora, updated_at=ahora,
    )
    return JsonResponse({'ok': True, 'marcados': marcados})


@csrf_exempt
@require_POST
def api_marcar_contestada(request):
    """Marca una solicitud como contestada. n8n la llama cuando detecta que el
    vendedor respondió en el hilo de Gmail (por gmail_thread_id)."""
    if not _validar_token(request):
        return JsonResponse({'error': 'No autorizado'}, status=401)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    solicitud_id = data.get('solicitud_id')
    thread_id = (data.get('gmail_thread_id') or '').strip()

    qs = SolicitudPresupuesto.objects.filter(estado=SolicitudPresupuesto.ESTADO_ASIGNADA)
    if solicitud_id:
        qs = qs.filter(pk=solicitud_id)
    elif thread_id:
        qs = qs.filter(gmail_thread_id=thread_id)
    else:
        return JsonResponse({'error': 'Falta solicitud_id o gmail_thread_id'}, status=400)

    marcadas = 0
    for solicitud in qs:
        solicitud.marcar_contestada()
        marcadas += 1

    return JsonResponse({'ok': True, 'marcadas': marcadas})


# ---------------------------------------------------------------------------
# Panel web
# ---------------------------------------------------------------------------

@login_required
def solicitud_list(request):
    estado = request.GET.get('estado', '')
    vendedor_id = request.GET.get('vendedor', '')

    qs = SolicitudPresupuesto.objects.select_related('vendedor')
    if estado:
        qs = qs.filter(estado=estado)
    if vendedor_id:
        qs = qs.filter(vendedor_id=vendedor_id)

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'solicitudes/solicitud_list.html', {
        'page_obj': page_obj,
        'estado_filter': estado,
        'vendedor_filter': vendedor_id,
        'vendedores': vendedores_pool(),
        'estado_choices': SolicitudPresupuesto.ESTADO_CHOICES,
    })


@login_required
@require_POST
def solicitud_marcar_contestada(request, pk):
    solicitud = get_object_or_404(SolicitudPresupuesto, pk=pk)
    solicitud.marcar_contestada()
    messages.success(request, "Solicitud marcada como contestada.")
    return redirect('solicitudes:lista')


@login_required
@require_POST
def solicitud_reasignar(request, pk):
    solicitud = get_object_or_404(SolicitudPresupuesto, pk=pk)
    form = ReasignarSolicitudForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Seleccioná un vendedor válido para reasignar.")
        return redirect('solicitudes:lista')

    vendedor = form.cleaned_data['vendedor']
    solicitud.vendedor = vendedor
    if solicitud.estado == SolicitudPresupuesto.ESTADO_SIN_ASIGNAR:
        solicitud.estado = SolicitudPresupuesto.ESTADO_ASIGNADA
    # Reinicia el reloj del recordatorio: el nuevo vendedor recién recibe la solicitud.
    solicitud.fecha_asignacion = timezone.now()
    solicitud.ultimo_recordatorio = None
    solicitud.save(update_fields=[
        'vendedor', 'estado', 'fecha_asignacion', 'ultimo_recordatorio', 'updated_at',
    ])
    messages.success(request, f"Solicitud reasignada a {vendedor.get_full_name() or vendedor.username}.")
    return redirect('solicitudes:lista')
