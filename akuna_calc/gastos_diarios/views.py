import json
import os
import unicodedata
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


TIPOS_VALIDOS = {clave for clave, _ in GastoDiario.TIPO_CUENTA_CHOICES}
TIPO_LABELS = dict(GastoDiario.TIPO_CUENTA_CHOICES)

# Sinónimos hablados/escritos -> clave de Tipo de Cuenta
SINONIMOS_TIPO_CUENTA = {
    'colocadores': 'colocadores', 'colocador': 'colocadores',
    'colaboradores': 'colaboradores', 'colaborador': 'colaboradores',
    'fletes': 'fletes', 'flete': 'fletes',
    'retiros propios': 'retiros_propios', 'retiro propio': 'retiros_propios',
    'retiros': 'retiros_propios', 'retiro': 'retiros_propios', 'retiros_propios': 'retiros_propios',
    'varios': 'varios', 'vario': 'varios',
    'proveedores': 'proveedores', 'proveedor': 'proveedores',
    'caja chica': 'caja_chica', 'cajachica': 'caja_chica', 'caja': 'caja_chica', 'caja_chica': 'caja_chica',
}

OPCIONES_TEXTO = 'colocadores, colaboradores, fletes, retiros, varios, proveedores, caja chica'


def _normalizar_texto(texto):
    texto = unicodedata.normalize('NFD', str(texto or '').lower())
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    return ' '.join(texto.split()).strip()


def _mapear_tipo(texto):
    """Devuelve la clave de Tipo de Cuenta a partir de texto libre, o '' si no se reconoce."""
    norm = _normalizar_texto(texto)
    if norm in TIPOS_VALIDOS:
        return norm
    return SINONIMOS_TIPO_CUENTA.get(norm, '')


def _interpretar_si_no(texto):
    norm = _normalizar_texto(texto)
    if norm in ('si', 's', 'ok', 'confirmo', 'confirmar', 'dale'):
        return 'si'
    if norm in ('no', 'n', 'cancelar', 'cancelo'):
        return 'no'
    return 'otro'


def _siguiente_mensaje(numero_origen):
    """Mensaje conversacional según el estado del borrador del número:
    pregunta el tipo del próximo gasto sin clasificar, o el resumen para confirmar."""
    borradores = list(
        GastoDiario.objects.filter(numero_origen=numero_origen, estado='borrador').order_by('pk')
    )
    if not borradores:
        return ''

    sin_clasificar = [g for g in borradores if not g.tipo_cuenta]
    if sin_clasificar:
        g = sin_clasificar[0]
        return (
            f"El gasto «{g.descripcion}» (${g.monto:.2f}) ¿de qué tipo es?\n"
            f"Responde con uno: {OPCIONES_TEXTO}."
        )

    lineas = '\n'.join(
        f"- {g.descripcion}: ${g.monto:.2f} ({g.get_tipo_cuenta_display()})" for g in borradores
    )
    total = sum(g.monto for g in borradores)
    return (
        f"Detecté {len(borradores)} gasto(s):\n\n{lineas}\n\n"
        f"Total: ${total:.2f}\n\n¿Confirmás? Responde SI para guardar o NO para cancelar."
    )


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

            tipo_raw = item.get('tipo') or ''
            tipo = tipo_raw if tipo_raw in TIPOS_VALIDOS else _mapear_tipo(tipo_raw)

            gasto = GastoDiario.objects.create(
                descripcion=descripcion,
                monto=monto,
                tipo_cuenta=tipo,
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
        'mensaje': _siguiente_mensaje(numero_origen),
        'finalizado': False,
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


@csrf_exempt
@require_POST
def api_responder(request):
    """Endpoint conversacional unificado. Recibe el texto crudo del usuario y,
    según el estado del borrador, lo interpreta como clasificación de tipo o como
    confirmación SI/NO. Devuelve {ok, mensaje, finalizado} para que n8n lo reenvíe."""
    if not _validar_token(request):
        return JsonResponse({'error': 'No autorizado'}, status=401)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    numero_origen = _normalizar_numero(data.get('numero_origen'))
    texto = (data.get('texto') or '').strip()

    if not numero_origen:
        return JsonResponse({'error': 'Falta numero_origen'}, status=400)
    if not NumeroAutorizado.objects.filter(numero=numero_origen, activo=True).exists():
        return JsonResponse({'error': 'Número no autorizado'}, status=403)

    # 'manejado' indica si había un borrador pendiente y por lo tanto este
    # mensaje se interpretó como respuesta conversacional. n8n lo usa para
    # decidir si un audio era una respuesta o un gasto nuevo a extraer.
    borradores = GastoDiario.objects.filter(numero_origen=numero_origen, estado='borrador')
    if not borradores.exists():
        return JsonResponse({
            'ok': True,
            'manejado': False,
            'finalizado': True,
            'mensaje': 'No tenés gastos pendientes. Mandá una nota de voz con el gasto y el monto (ej: nafta 20000).',
        })

    sin_clasificar = borradores.filter(tipo_cuenta='').order_by('pk')

    if sin_clasificar.exists():
        tipo = _mapear_tipo(texto)
        if not tipo:
            objetivo = sin_clasificar.first()
            return JsonResponse({
                'ok': True,
                'manejado': True,
                'finalizado': False,
                'mensaje': (
                    f"No reconocí el tipo. Para «{objetivo.descripcion}» respondé uno de: {OPCIONES_TEXTO}."
                ),
            })
        objetivo = sin_clasificar.first()
        objetivo.tipo_cuenta = tipo
        objetivo.save(update_fields=['tipo_cuenta', 'updated_at'])
        return JsonResponse({
            'ok': True,
            'manejado': True,
            'finalizado': False,
            'mensaje': _siguiente_mensaje(numero_origen),
        })

    accion = _interpretar_si_no(texto)
    if accion == 'si':
        afectados = borradores.update(estado='en_espera')
        return JsonResponse({
            'ok': True,
            'manejado': True,
            'finalizado': True,
            'accion': 'si',
            'afectados': afectados,
            'mensaje': 'Listo. Tus gastos quedaron cargados en AkunCalcu con estado en espera para revisión.',
        })
    if accion == 'no':
        afectados = borradores.count()
        borradores.delete()
        return JsonResponse({
            'ok': True,
            'manejado': True,
            'finalizado': True,
            'accion': 'no',
            'afectados': afectados,
            'mensaje': 'Cancelado. Descarté los gastos.',
        })

    return JsonResponse({
        'ok': True,
        'manejado': True,
        'finalizado': False,
        'mensaje': 'No te entendí. Respondé SI para confirmar o NO para cancelar.',
    })


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
        'tipo_choices': GastoDiario.TIPO_CUENTA_CHOICES,
    })


def _registrar_compra(gasto, user):
    """Registra un gasto diario aprobado como una Compra en el Tipo de Cuenta
    indicado por su clasificación, para que aparezca en el reporte de comercial.
    Si el gasto no tiene clasificación, va a Caja Chica (fallback)."""
    from comercial.models import TipoCuenta, Cuenta, TipoGasto, Compra

    numero_pedido = f'CAJA-{gasto.pk}'
    if Compra.objects.filter(numero_pedido=numero_pedido, deleted_at__isnull=True).exists():
        return

    tipo_key = gasto.tipo_cuenta or 'caja_chica'
    descripcion_tipo = TIPO_LABELS.get(tipo_key, 'Caja Chica')

    tipo_cuenta, _ = TipoCuenta.objects.get_or_create(
        tipo=tipo_key,
        defaults={'descripcion': descripcion_tipo, 'activo': True},
    )
    cuenta, _ = Cuenta.objects.get_or_create(
        tipo_cuenta=tipo_cuenta,
        nombre=descripcion_tipo,
        defaults={'activo': True},
    )
    tipo_gasto, _ = TipoGasto.objects.get_or_create(
        tipo_cuenta=tipo_cuenta,
        nombre=descripcion_tipo,
        defaults={'activo': True},
    )
    Compra.objects.create(
        numero_pedido=numero_pedido,
        cuenta=cuenta,
        tipo_gasto=tipo_gasto,
        fecha_pago=gasto.fecha,
        valor_total=gasto.monto,
        con_factura=False,
        descripcion=gasto.descripcion,
        estado='pagado',
        created_by=user,
    )


@login_required
@require_POST
def gasto_aprobar(request, pk):
    gasto = get_object_or_404(GastoDiario, pk=pk)
    if gasto.estado == 'en_espera':
        tipo_post = request.POST.get('tipo_cuenta', '').strip()
        with transaction.atomic():
            if tipo_post in TIPOS_VALIDOS:
                gasto.tipo_cuenta = tipo_post
            gasto.estado = 'aprobado'
            gasto.save(update_fields=['estado', 'tipo_cuenta', 'updated_at'])
            _registrar_compra(gasto, request.user)
        destino = gasto.get_tipo_cuenta_display() or 'Caja Chica'
        messages.success(request, f"Gasto #{gasto.pk} aprobado y registrado en {destino}.")
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
