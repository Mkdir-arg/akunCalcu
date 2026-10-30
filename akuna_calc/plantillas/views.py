import base64
import io
from pathlib import Path

from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Count
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from xhtml2pdf import pisa

from configuracion.models import ConfiguracionGeneral
from core.avisos import crear_aviso
from usuarios.access_control import user_has_access
from .models import PedidoFabrica, OrdenFabricacion, MedidaOrdenFabricacion
from .forms import (
    CambiarEtapaForm, CancelarPedidoForm, EntregarPedidoForm, LiberarPedidoForm,
    OrdenFabricacionForm, PedidoFabricaForm,
)
from .services import circuito
from .utils import cortar_a_max_length


def _build_logo_data_url():
    logo_candidates = [
        Path(settings.BASE_DIR) / 'static' / 'imagenes' / 'AKUN-LOGO.png',
        Path(settings.BASE_DIR) / 'static' / 'AKUN-LOGO.png',
        Path(settings.STATIC_ROOT) / 'imagenes' / 'AKUN-LOGO.png',
        Path(settings.STATIC_ROOT) / 'AKUN-LOGO.png',
    ]
    logo_path = next((path for path in logo_candidates if path.exists()), None)
    if not logo_path:
        return ''
    logo_b64 = base64.b64encode(logo_path.read_bytes()).decode('ascii')
    return f'data:image/png;base64,{logo_b64}'


def _puede_gestionar(user):
    return user_has_access(user, 'fabrica.pedidos_gestion')


def _puede_mover_etapas(user):
    return _puede_gestionar(user) or user_has_access(user, 'fabrica.tablero')


def _exigir_gestion(user):
    """Además del control por ruta del middleware: la acción no depende solo del mapa de rutas."""
    if not _puede_gestionar(user):
        raise PermissionDenied('Solo el responsable de fábrica puede hacer esto.')


def _primer_error(error):
    return error.messages[0] if hasattr(error, 'messages') else str(error)


@login_required
def index(request):
    """Redirección de la raíz de la app al listado de pedidos"""
    return redirect('plantillas:pedido_list')


# ============ PEDIDOS DE FÁBRICA ============

@login_required
def pedido_list(request):
    """Listado de pedidos, filtrable por estado."""
    estado = request.GET.get('estado', '')
    estados_validos = dict(PedidoFabrica.ESTADO_CHOICES)
    pedidos = PedidoFabrica.objects.select_related('presupuesto').prefetch_related('ordenes')
    if estado in estados_validos:
        pedidos = pedidos.filter(estado=estado)
    else:
        estado = ''
    page_obj = Paginator(pedidos, 20).get_page(request.GET.get('page'))
    conteos = dict(PedidoFabrica.objects.values_list('estado').annotate(n=Count('id')))
    contexto = {
        'pedidos': page_obj,
        'page_obj': page_obj,
        'estado_actual': estado,
        'pestanas': [('', 'Todos', sum(conteos.values()))] + [
            (clave, etiqueta, conteos.get(clave, 0)) for clave, etiqueta in PedidoFabrica.ESTADO_CHOICES
        ],
        'query_sin_page': f'estado={estado}' if estado else '',
    }
    template = 'plantillas/_pedido_tabla.html' if request.GET.get('partial') else 'plantillas/pedido_list.html'
    return render(request, template, contexto)


@login_required
def pedido_create(request):
    """Alta manual de un pedido (sin presupuesto de origen)."""
    if request.method == 'POST':
        form = PedidoFabricaForm(request.POST)
        if form.is_valid():
            pedido = form.save(commit=False)
            pedido.usuario = request.user
            pedido.save()
            messages.success(request, f'Pedido {pedido.numero} creado.')
            return redirect('plantillas:pedido_detail', pk=pedido.pk)
    else:
        form = PedidoFabricaForm(initial={'numero': PedidoFabrica.generar_numero()})

    return render(request, 'plantillas/pedido_form.html', {'form': form})


@login_required
def pedido_detail(request, pk):
    """Detalle de pedido con sus órdenes, el checklist para liberar y el historial."""
    pedido = get_object_or_404(
        PedidoFabrica.objects.select_related('presupuesto', 'presupuesto__venta', 'usuario', 'liberado_por'),
        pk=pk,
    )
    ordenes = pedido.ordenes.prefetch_related('medidas').all()
    puede_gestionar = _puede_gestionar(request.user)
    return render(request, 'plantillas/pedido_detail.html', {
        'pedido': pedido,
        'ordenes': ordenes,
        'faltantes': pedido.faltantes_para_liberar() if pedido.estado == 'recibido' else [],
        'sin_sena': pedido.estado == 'recibido' and not circuito.venta_tiene_sena(pedido),
        'historial': pedido.historial.select_related('orden', 'usuario')[:30],
        'puede_gestionar': puede_gestionar,
        'puede_mover_etapas': _puede_mover_etapas(request.user),
    })


@login_required
@require_POST
def pedido_liberar(request, pk):
    _exigir_gestion(request.user)
    pedido = get_object_or_404(PedidoFabrica, pk=pk)
    form = LiberarPedidoForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'El motivo para liberar sin seña puede tener hasta 500 caracteres.')
        return redirect('plantillas:pedido_detail', pk=pk)
    try:
        circuito.liberar_pedido(pedido, request.user, form.cleaned_data['motivo_sin_sena'])
    except ValidationError as error:
        messages.error(request, _primer_error(error))
    else:
        messages.success(request, f'Pedido {pedido.numero} liberado a fábrica.')
    return redirect('plantillas:pedido_detail', pk=pk)


@login_required
@require_POST
def pedido_cancelar(request, pk):
    _exigir_gestion(request.user)
    pedido = get_object_or_404(PedidoFabrica, pk=pk)
    form = CancelarPedidoForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Indicá el motivo de la cancelación.')
        return redirect('plantillas:pedido_detail', pk=pk)
    try:
        circuito.cancelar_pedido(pedido, request.user, form.cleaned_data['motivo'])
    except ValidationError as error:
        messages.error(request, _primer_error(error))
    else:
        messages.success(request, f'Pedido {pedido.numero} cancelado.')
    return redirect('plantillas:pedido_detail', pk=pk)


@login_required
@require_POST
def pedido_entregar(request, pk):
    _exigir_gestion(request.user)
    pedido = get_object_or_404(PedidoFabrica, pk=pk)
    form = EntregarPedidoForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Elegí si se entregó o se colocó.')
        return redirect('plantillas:pedido_detail', pk=pk)
    try:
        circuito.marcar_entregado(pedido, request.user, form.cleaned_data['tipo'])
    except ValidationError as error:
        messages.error(request, _primer_error(error))
    else:
        messages.success(request, f'Pedido {pedido.numero} marcado como {form.cleaned_data["tipo"]}.')
    return redirect('plantillas:pedido_detail', pk=pk)


def _avisar_pedido_terminado(pedido):
    presupuesto = pedido.presupuesto
    vendedor = presupuesto.created_by if presupuesto else None
    if vendedor is None or not vendedor.is_active:
        return
    crear_aviso(
        vendedor,
        f'Pedido {pedido.numero} ({pedido.cliente}) terminado: listo para entregar.',
        tipo='exito',
        url=reverse('plantillas:pedido_detail', args=[pedido.pk]),
    )


# ============ ÓRDENES DE FABRICACIÓN ============

def _guardar_medidas(orden, request):
    """Reemplaza las filas de medidas de una orden con las enviadas en el POST."""
    items = request.POST.getlist('medida_item')
    cantidades = request.POST.getlist('medida_cantidad')
    medidas = request.POST.getlist('medida_medida')
    observaciones = request.POST.getlist('medida_observaciones')
    pisos = request.POST.getlist('medida_piso_depto')

    orden.medidas.all().delete()
    fila = 0
    for i in range(len(cantidades)):
        def _cortar(campo, valores):
            return cortar_a_max_length(MedidaOrdenFabricacion, campo, valores[i] if i < len(valores) else '')

        item_txt = _cortar('item', items)
        medida_txt = _cortar('medida', medidas)
        obs_txt = _cortar('observaciones', observaciones)
        piso_txt = _cortar('piso_depto', pisos)
        # Una fila se guarda solo si tiene algún dato de texto cargado.
        if not any([item_txt, medida_txt, obs_txt, piso_txt]):
            continue
        try:
            cantidad = int(cantidades[i])
        except (ValueError, TypeError):
            cantidad = 1
        fila += 1
        MedidaOrdenFabricacion.objects.create(
            orden=orden,
            item=item_txt,
            cantidad=max(cantidad, 1),
            medida=medida_txt,
            observaciones=obs_txt,
            piso_depto=piso_txt,
            orden_fila=fila,
        )


def _solo_pedido_recibido(request, pedido, accion):
    """Agregar o borrar órdenes solo se puede antes de liberar el pedido."""
    if pedido.estado == 'recibido':
        return None
    messages.error(request, f'No se puede {accion}: el pedido ya fue liberado a fábrica o está cerrado.')
    return redirect('plantillas:pedido_detail', pk=pedido.pk)


@login_required
@require_POST
def orden_create(request, pedido_pk):
    """Alta de una orden de fabricación dentro de un pedido.

    Los datos de la abertura (opcionales) llegan desde el popup del cotizador y
    precargan la orden; si no vienen, la orden nace en blanco para completar a mano.
    """
    pedido = get_object_or_404(PedidoFabrica, pk=pedido_pk)
    bloqueo = _solo_pedido_recibido(request, pedido, 'agregar órdenes')
    if bloqueo:
        return bloqueo
    campos_abertura = ('tipo_abertura', 'linea', 'color', 'tipo_vidrio', 'modelo_hoja', 'cantidad_hojas',
                       'mosquitero', 'mosquitero_modelo', 'premarco')
    datos = {
        campo: cortar_a_max_length(OrdenFabricacion, campo, request.POST.get(campo))
        for campo in campos_abertura
    }
    # El número es único: si otro usuario tomó el mismo en paralelo, se recalcula.
    for intento in range(3):
        try:
            with transaction.atomic():
                orden = OrdenFabricacion.objects.create(
                    pedido=pedido,
                    numero=OrdenFabricacion.generar_numero(),
                    orden=pedido.ordenes.count() + 1,
                    cliente_nombre=cortar_a_max_length(OrdenFabricacion, 'cliente_nombre', pedido.cliente),
                    **datos,
                )
            break
        except IntegrityError:
            if intento == 2:
                raise
    messages.success(request, f'Orden {orden.numero_formateado} creada. Completá el detalle.')
    return redirect('plantillas:orden_edit', pk=orden.pk)


@login_required
def orden_edit(request, pk):
    """Editar el detalle de una orden. Liberado el pedido, solo el responsable y con motivo (sube la revisión)."""
    orden = get_object_or_404(
        OrdenFabricacion.objects.select_related('pedido').prefetch_related('medidas'),
        pk=pk,
    )
    pedido = orden.pedido
    if pedido.esta_cerrado or orden.etapa == 'anulada':
        messages.error(request, 'La orden es de un pedido cerrado: no se puede modificar.')
        return redirect('plantillas:pedido_detail', pk=pedido.pk)
    liberada = pedido.esta_liberado
    if liberada and not _puede_gestionar(request.user):
        raise PermissionDenied('Solo el responsable de fábrica modifica una orden liberada.')

    if request.method == 'POST':
        try:
            # Con pedido y orden bloqueados y guardando solo los campos del form,
            # no se pisa una etapa o una anulación que el taller hizo mientras se editaba.
            with transaction.atomic():
                pedido = PedidoFabrica.objects.select_for_update().get(pk=pedido.pk)
                orden = OrdenFabricacion.objects.select_for_update().get(pk=orden.pk)
                if pedido.esta_cerrado or orden.etapa == 'anulada' or pedido.esta_liberado != liberada:
                    raise ValidationError('El pedido cambió de estado mientras editabas la orden. Revisala y volvé a intentar.')
                form = OrdenFabricacionForm(request.POST, instance=orden, requiere_motivo=liberada)
                if form.is_valid():
                    form.save(commit=False).save(update_fields=[*form.Meta.fields, 'updated_at'])
                    _guardar_medidas(orden, request)
                    if liberada:
                        orden = circuito.revisar_orden(orden, request.user, form.cleaned_data['motivo_revision'])
        except ValidationError as error:
            messages.error(request, _primer_error(error))
            return redirect('plantillas:pedido_detail', pk=pedido.pk)
        if form.is_valid():
            if liberada:
                _avisar_revision(orden, request.user, form.cleaned_data['motivo_revision'])
                messages.success(request, f'Orden {orden.numero_formateado} actualizada: ahora es la revisión {orden.revision}. Reimprimila.')
            else:
                messages.success(request, f'Orden {orden.numero_formateado} actualizada.')
            return redirect('plantillas:pedido_detail', pk=pedido.pk)
    else:
        form = OrdenFabricacionForm(instance=orden, requiere_motivo=liberada)

    return render(request, 'plantillas/orden_form.html', {
        'form': form,
        'orden': orden,
        'pedido': pedido,
        'medidas': orden.medidas.all(),
        'liberada': liberada,
    })


@login_required
@require_POST
def orden_delete(request, pk):
    """Eliminar una orden de fabricación."""
    orden = get_object_or_404(OrdenFabricacion.objects.select_related('pedido'), pk=pk)
    bloqueo = _solo_pedido_recibido(request, orden.pedido, 'eliminar órdenes')
    if bloqueo:
        return bloqueo
    pedido_pk = orden.pedido.pk
    numero = orden.numero_formateado
    orden.delete()
    messages.success(request, f'Orden {numero} eliminada.')
    return redirect('plantillas:pedido_detail', pk=pedido_pk)


@login_required
@require_POST
def orden_cambiar_etapa(request, pk):
    """Avanza o retrocede una etapa del taller (Corte → Armado → Vidriado → Lista)."""
    if not _puede_mover_etapas(request.user):
        raise PermissionDenied('No tenés permiso para mover etapas del taller.')
    orden = get_object_or_404(OrdenFabricacion.objects.select_related('pedido'), pk=pk)
    form = CambiarEtapaForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Etapa inválida.')
        return redirect('plantillas:pedido_detail', pk=orden.pedido.pk)
    estado_previo = orden.pedido.estado
    try:
        orden, pedido = circuito.cambiar_etapa(orden, request.user, form.cleaned_data['etapa'], form.cleaned_data['nota'])
    except ValidationError as error:
        messages.error(request, _primer_error(error))
        return redirect('plantillas:pedido_detail', pk=orden.pedido.pk)

    messages.success(request, f'Orden {orden.numero_formateado}: {orden.get_etapa_display()}.')
    if pedido.estado == 'terminado' and estado_previo != 'terminado':
        _avisar_pedido_terminado(pedido)
        messages.success(request, f'Pedido {pedido.numero} terminado: se avisó al vendedor.')
    return redirect('plantillas:pedido_detail', pk=pedido.pk)


@login_required
@require_POST
def orden_marcar_reimpresa(request, pk):
    """El taller confirma que tiene en papel la revisión vigente (ver el PDF no alcanza)."""
    if not _puede_mover_etapas(request.user):
        raise PermissionDenied('No tenés permiso para marcar órdenes reimpresas.')
    orden = get_object_or_404(OrdenFabricacion, pk=pk)
    try:
        revision = int(request.POST.get('revision', ''))
    except ValueError:
        revision = None
    # Filtrar por la revisión que vio el usuario: si entretanto salió otra, sigue pendiente.
    marcadas = OrdenFabricacion.objects.filter(pk=orden.pk, revision=revision, reimpresion_pendiente=True).update(
        reimpresion_pendiente=False, updated_at=timezone.now(),
    )
    if marcadas:
        messages.success(request, f'Orden {orden.numero_formateado}: Rev. {revision} marcada como reimpresa.')
    else:
        messages.error(request, f'La orden {orden.numero_formateado} cambió de revisión: reimprimí la vigente.')
    return redirect('plantillas:pedido_detail', pk=orden.pedido_id)


def _avisar_revision(orden, actor, motivo):
    crear_aviso(
        circuito.responsables_fabrica(excluir=actor),
        f'Orden {orden.numero_formateado} (pedido {orden.pedido.numero}) pasó a Rev. {orden.revision}: {motivo}'[:255],
        tipo='alerta',
        url=reverse('plantillas:pedido_detail', args=[orden.pedido_id]),
    )


# ============ PDF ============

def _contexto_hoja(orden, posicion, total_ordenes):
    return {
        'orden': orden,
        'medidas': orden.medidas.all(),
        'posicion': posicion,
        'total_ordenes': total_ordenes,
    }


def _contexto_pdf_base():
    return {
        'empresa': ConfiguracionGeneral.get_datos_empresa(),
        'logo_url': _build_logo_data_url(),
        'croquis_filas': range(12),
        'croquis_cols': range(26),
        'nota_lineas': range(23),
    }


def _respuesta_pdf(html, nombre):
    result = io.BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=result)
    if pisa_status.err:
        return HttpResponse('No se pudo generar el PDF.', content_type='text/plain; charset=utf-8', status=500)
    response = HttpResponse(result.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{nombre}"'
    return response


@login_required
def orden_pdf(request, pk):
    """Genera el PDF A4 de la orden de fabricación (planilla de fábrica)."""
    orden = get_object_or_404(
        OrdenFabricacion.objects.select_related('pedido', 'pedido__presupuesto').prefetch_related('medidas'),
        pk=pk,
    )
    activas = list(orden.pedido.ordenes_activas().values_list('pk', flat=True))
    posicion = activas.index(orden.pk) + 1 if orden.pk in activas else None
    html = render_to_string('plantillas/orden_pdf.html', {
        **_contexto_pdf_base(),
        'hoja': _contexto_hoja(orden, posicion, len(activas)),
    })
    return _respuesta_pdf(html, f'orden_fabricacion_{orden.numero_formateado}.pdf')


@login_required
def pedido_pdf(request, pk):
    """Todas las órdenes activas del pedido en un PDF, con carátula."""
    pedido = get_object_or_404(PedidoFabrica.objects.select_related('presupuesto'), pk=pk)
    ordenes = list(pedido.ordenes_activas().select_related('pedido', 'pedido__presupuesto').prefetch_related('medidas'))
    html = render_to_string('plantillas/pedido_pdf.html', {
        **_contexto_pdf_base(),
        'pedido': pedido,
        'ordenes': ordenes,
        'hojas': [_contexto_hoja(o, i, len(ordenes)) for i, o in enumerate(ordenes, start=1)],
    })
    return _respuesta_pdf(html, f'pedido_fabrica_{pedido.numero}.pdf')
