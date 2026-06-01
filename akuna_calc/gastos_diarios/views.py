import json
import os
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .forms import NumeroAutorizadoForm
from .models import GastoDiario, NumeroAutorizado


def _validar_token(request):
    token = request.headers.get('X-Bot-Secret', '')
    secret = os.environ.get('TELEGRAM_BOT_SECRET', '')
    return bool(secret) and token == secret


def _normalizar_numero(numero):
    if numero is None:
        return ''
    numero = str(numero).strip()
    if '@' in numero:
        numero = numero.split('@', 1)[0]
    return numero


def _staff_required(user):
    return user.is_authenticated and user.is_staff


@csrf_exempt
@require_POST
def api_crear_borrador(request):
    if not _validar_token(request):
        return JsonResponse({'error': 'No autorizado'}, status=401)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    numero_origen = _normalizar_numero(data.get('numero_origen'))
    audio_id = (data.get('audio_id') or '').strip()
    transcripcion = data.get('transcripcion', '') or ''
    gastos_data = data.get('gastos', [])

    if not numero_origen:
        return JsonResponse({'error': 'Falta numero_origen'}, status=400)

    if not isinstance(gastos_data, list) or not gastos_data:
        return JsonResponse({'error': 'Lista de gastos vacía'}, status=400)

    if not NumeroAutorizado.objects.filter(numero=numero_origen, activo=True).exists():
        return JsonResponse({'error': 'Número no autorizado'}, status=403)

    with transaction.atomic():
        GastoDiario.objects.filter(numero_origen=numero_origen, estado='borrador').delete()

        creados_ids = []
        for item in gastos_data:
            descripcion = (item.get('descripcion') or '').strip()
            try:
                monto = Decimal(str(item.get('monto', '0')))
            except (InvalidOperation, TypeError):
                continue
            if not descripcion or monto <= 0:
                continue

            gasto = GastoDiario.objects.create(
                descripcion=descripcion,
                monto=monto,
                numero_origen=numero_origen,
                audio_id=audio_id,
                transcripcion=transcripcion,
                estado='borrador',
            )
            creados_ids.append(gasto.pk)

    return JsonResponse({
        'ok': True,
        'creados': len(creados_ids),
        'ids': creados_ids,
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

    numero_origen = _normalizar_numero(data.get('numero_origen'))
    accion = (data.get('accion') or '').strip().lower()

    if not numero_origen:
        return JsonResponse({'error': 'Falta numero_origen'}, status=400)
    if accion not in ('si', 'no'):
        return JsonResponse({'error': 'Acción debe ser "si" o "no"'}, status=400)

    if not NumeroAutorizado.objects.filter(numero=numero_origen, activo=True).exists():
        return JsonResponse({'error': 'Número no autorizado'}, status=403)

    borradores = GastoDiario.objects.filter(numero_origen=numero_origen, estado='borrador')
    if not borradores.exists():
        return JsonResponse({'ok': True, 'accion': accion, 'afectados': 0, 'aviso': 'No había borrador pendiente'})

    if accion == 'si':
        afectados = borradores.update(estado='en_espera')
    else:
        afectados = borradores.update(estado='rechazado')

    return JsonResponse({'ok': True, 'accion': accion, 'afectados': afectados})


@login_required
def gasto_list(request):
    estado = request.GET.get('estado', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')

    qs = GastoDiario.objects.exclude(estado='borrador')
    if estado:
        qs = qs.filter(estado=estado)
    if fecha_desde:
        qs = qs.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        qs = qs.filter(fecha__lte=fecha_hasta)

    paginator = Paginator(qs, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    numeros = {gasto.numero_origen for gasto in page_obj}
    nombres = dict(
        NumeroAutorizado.objects.filter(numero__in=numeros).values_list('numero', 'nombre')
    )
    for gasto in page_obj:
        gasto.origen_nombre = nombres.get(gasto.numero_origen) or gasto.numero_origen

    return render(request, 'gastos_diarios/gasto_list.html', {
        'page_obj': page_obj,
        'estado_filter': estado,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
    })


@login_required
@require_POST
def gasto_aprobar(request, pk):
    gasto = get_object_or_404(GastoDiario, pk=pk)
    if gasto.estado == 'en_espera':
        gasto.estado = 'aprobado'
        gasto.save(update_fields=['estado', 'updated_at'])
        messages.success(request, f"Gasto #{gasto.pk} aprobado.")
    else:
        messages.info(request, f"El gasto #{gasto.pk} ya estaba {gasto.get_estado_display().lower()}.")
    return redirect('gastos_diarios:lista')


@login_required
@require_POST
def gasto_rechazar(request, pk):
    gasto = get_object_or_404(GastoDiario, pk=pk)
    if gasto.estado == 'en_espera':
        gasto.estado = 'rechazado'
        gasto.save(update_fields=['estado', 'updated_at'])
        messages.success(request, f"Gasto #{gasto.pk} rechazado.")
    else:
        messages.info(request, f"El gasto #{gasto.pk} ya estaba {gasto.get_estado_display().lower()}.")
    return redirect('gastos_diarios:lista')


@login_required
@user_passes_test(_staff_required)
def numero_list(request):
    numeros = NumeroAutorizado.objects.all()
    return render(request, 'gastos_diarios/numero_list.html', {'numeros': numeros})


@login_required
@user_passes_test(_staff_required)
def numero_create(request):
    if request.method == 'POST':
        form = NumeroAutorizadoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Número autorizado creado.")
            return redirect('gastos_diarios:numero_list')
    else:
        form = NumeroAutorizadoForm()
    return render(request, 'gastos_diarios/numero_form.html', {'form': form, 'titulo': 'Nuevo número autorizado'})


@login_required
@user_passes_test(_staff_required)
def numero_edit(request, pk):
    numero = get_object_or_404(NumeroAutorizado, pk=pk)
    if request.method == 'POST':
        form = NumeroAutorizadoForm(request.POST, instance=numero)
        if form.is_valid():
            form.save()
            messages.success(request, "Número autorizado actualizado.")
            return redirect('gastos_diarios:numero_list')
    else:
        form = NumeroAutorizadoForm(instance=numero)
    return render(request, 'gastos_diarios/numero_form.html', {
        'form': form,
        'titulo': f'Editar número - {numero}',
        'numero': numero,
    })


@login_required
@user_passes_test(_staff_required)
@require_POST
def numero_delete(request, pk):
    numero = get_object_or_404(NumeroAutorizado, pk=pk)
    nombre = str(numero)
    numero.delete()
    messages.success(request, f"Número '{nombre}' eliminado.")
    return redirect('gastos_diarios:numero_list')
