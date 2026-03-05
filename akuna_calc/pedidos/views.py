import json
import os

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import ItemPedidoTelegram, PedidoTelegram


def _validar_token(request):
    token = request.headers.get('X-Bot-Secret', '')
    secret = os.environ.get('TELEGRAM_BOT_SECRET', '')
    return bool(secret) and token == secret


@csrf_exempt
@require_POST
def api_crear_borrador(request):
    if not _validar_token(request):
        return JsonResponse({'error': 'No autorizado'}, status=401)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    chat_id = data.get('chat_id')
    username = data.get('telegram_username', '')
    transcripcion = data.get('transcripcion', '')
    items_data = data.get('items', [])

    if not chat_id or not items_data:
        return JsonResponse({'error': 'Faltan datos requeridos'}, status=400)

    pedido = PedidoTelegram.objects.create(
        telegram_chat_id=str(chat_id),
        telegram_username=username,
        transcripcion_original=transcripcion,
        estado='pendiente',
    )

    for item in items_data:
        ItemPedidoTelegram.objects.create(
            pedido=pedido,
            descripcion=item.get('descripcion', ''),
            cantidad=int(item.get('cantidad', 1)),
        )

    items_texto = '\n'.join(
        f"• {i.cantidad}x {i.descripcion}" for i in pedido.items.all()
    )

    return JsonResponse({
        'pedido_id': pedido.pk,
        'items_texto': items_texto,
        'total_items': pedido.items.count(),
    })


@csrf_exempt
@require_POST
def api_confirmar(request):
    if not _validar_token(request):
        return JsonResponse({'error': 'No autorizado'}, status=401)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    chat_id = str(data.get('chat_id', ''))
    accion = data.get('accion', '').lower().strip()

    if not chat_id or accion not in ('si', 'no'):
        return JsonResponse({
            'error': 'Datos inválidos',
            'recibido_chat_id': chat_id,
            'recibido_accion': accion,
        }, status=400)

    pedido = (
        PedidoTelegram.objects
        .filter(telegram_chat_id=chat_id, estado='pendiente')
        .order_by('-created_at')
        .first()
    )

    if not pedido:
        return JsonResponse({'error': 'No hay pedido pendiente para este chat'}, status=404)

    pedido.estado = 'confirmado' if accion == 'si' else 'cancelado'
    pedido.save()

    return JsonResponse({
        'pedido_id': pedido.pk,
        'estado': pedido.estado,
    })


@login_required
def pedidos_list(request):
    estado = request.GET.get('estado', '')
    pedidos = PedidoTelegram.objects.prefetch_related('items').all()

    if estado:
        pedidos = pedidos.filter(estado=estado)

    return render(request, 'pedidos/pedidos_list.html', {
        'pedidos': pedidos,
        'estado_filter': estado,
    })
