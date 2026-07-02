from decimal import Decimal

import base64
import io
import json
from pathlib import Path

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from django.utils import timezone
from xhtml2pdf import pisa

from core.navigation import append_return_to, resolve_return_url
from usuarios.access_control import get_access_profile, user_has_full_access
from comercial.models import _formatear_cuit
from pricing.services.calculator import calcular_precio, PricingError
from pricing.models import Producto
from .pdf_descriptions import build_item_snapshot, build_pdf_item_context
from .models import Presupuesto, ItemPresupuesto, ComentarioPresupuesto
from .forms import PresupuestoForm, PresupuestoConfiguracionObraForm, ItemPresupuestoForm, ComentarioForm


def _presupuestos_list_url():
    return reverse('presupuestos:presupuestos-lista')


def _presupuestos_return_url(request):
    return resolve_return_url(request, _presupuestos_list_url())


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


def _get_detalle_queryset():
    return Presupuesto.objects.select_related('cliente', 'created_by', 'updated_by').prefetch_related('items', 'comentarios__autor')


def _build_detalle_context(presupuesto, comentario_form=None, configuracion_form=None):
    items_detalle = []
    for item in presupuesto.items.all():
        item_context = build_pdf_item_context(item)
        item.resumen_compacto = item_context.get('resumen_compacto', '')
        items_detalle.append(item)

    return {
        'presupuesto': presupuesto,
        'items_detalle': items_detalle,
        'comentario_form': comentario_form or ComentarioForm(),
        'configuracion_form': configuracion_form or PresupuestoConfiguracionObraForm(instance=presupuesto),
    }


def _puede_ver_creador(user):
    """Ven el creador del presupuesto los super admin (acceso total) y el rol Administrativo."""
    if user_has_full_access(user):
        return True
    profile = get_access_profile(user)
    return bool(profile and profile.rol and profile.rol.codigo == 'administrativo')


@login_required
def lista(request):
    all_qs = Presupuesto.objects.filter(deleted_at__isnull=True)
    
    # Calcular KPIs manualmente para evitar problemas con Sum en versiones antiguas
    total_count = all_qs.count()
    total_monto = sum(p.total for p in all_qs) if total_count > 0 else 0
    borradores = all_qs.filter(estado='borrador').count()
    enviados = all_qs.filter(estado='enviado').count()
    confirmados = all_qs.filter(estado='confirmado').count()
    monto_confirmado = sum(p.total for p in all_qs.filter(estado='confirmado'))
    
    kpis = {
        'total': total_count,
        'total_monto': total_monto,
        'borradores': borradores,
        'enviados': enviados,
        'confirmados': confirmados,
        'monto_confirmado': monto_confirmado,
    }

    puede_ver_creador = _puede_ver_creador(request.user)

    qs = Presupuesto.objects.filter(deleted_at__isnull=True).select_related('cliente', 'created_by').annotate(item_count=Count('items'))

    estado = request.GET.get('estado', '')
    cliente_q = request.GET.get('cliente', '')
    creado_por = request.GET.get('creado_por', '') if puede_ver_creador else ''

    if estado:
        qs = qs.filter(estado=estado)
    if cliente_q:
        qs = qs.filter(
            Q(cliente__nombre__icontains=cliente_q) |
            Q(cliente__apellido__icontains=cliente_q) |
            Q(cliente__razon_social__icontains=cliente_q)
        )
    if creado_por.isdigit():
        qs = qs.filter(created_by_id=int(creado_por))

    qs = qs.order_by('-created_at')

    usuarios_creadores = []
    if puede_ver_creador:
        usuarios_creadores = User.objects.filter(
            presupuestos_creados__deleted_at__isnull=True
        ).distinct().order_by('first_name', 'last_name', 'username')

    return render(request, 'presupuestos/lista.html', {
        'presupuestos': qs,
        'estado_actual': estado,
        'cliente_q': cliente_q,
        'creado_por_actual': creado_por,
        'estados': Presupuesto.ESTADO_CHOICES,
        'kpis': kpis,
        'puede_ver_creador': puede_ver_creador,
        'usuarios_creadores': usuarios_creadores,
    })


@login_required
def crear(request):
    return_url = _presupuestos_return_url(request)
    if request.method == 'POST':
        form = PresupuestoForm(request.POST)
        if form.is_valid():
            presupuesto = form.save(commit=False)
            presupuesto.numero = Presupuesto.generar_numero()
            presupuesto.created_by = request.user
            presupuesto.save()
            messages.success(request, f'Presupuesto {presupuesto.numero} creado.')
            return redirect(append_return_to(reverse('presupuestos:presupuestos-detalle', kwargs={'pk': presupuesto.pk}), return_url))
    else:
        form = PresupuestoForm()
    return render(request, 'presupuestos/form.html', {'form': form, 'titulo': 'Nuevo Presupuesto', 'return_url': return_url})


@login_required
def detalle(request, pk):
    presupuesto = get_object_or_404(_get_detalle_queryset().filter(deleted_at__isnull=True), pk=pk)
    context = _build_detalle_context(presupuesto)
    context['return_url'] = _presupuestos_return_url(request)
    context['es_pvc'] = presupuesto.tipo_material == 'pvc'
    return render(request, 'presupuestos/detalle.html', context)


@login_required
def editar(request, pk):
    presupuesto = get_object_or_404(Presupuesto.objects.filter(deleted_at__isnull=True), pk=pk)
    return_url = _presupuestos_return_url(request)
    if presupuesto.esta_bloqueado():
        messages.error(request, 'No se puede editar un presupuesto confirmado o cancelado.')
        return redirect(append_return_to(reverse('presupuestos:presupuestos-detalle', kwargs={'pk': pk}), return_url))

    if request.method == 'POST':
        form = PresupuestoForm(request.POST, instance=presupuesto)
        if form.is_valid():
            presupuesto = form.save(commit=False)
            presupuesto.updated_by = request.user
            presupuesto.save()
            messages.success(request, 'Presupuesto actualizado.')
            return redirect(append_return_to(reverse('presupuestos:presupuestos-detalle', kwargs={'pk': pk}), return_url))
    else:
        form = PresupuestoForm(instance=presupuesto)
    return render(request, 'presupuestos/form.html', {'form': form, 'titulo': 'Editar Presupuesto', 'presupuesto': presupuesto, 'return_url': return_url})


def _fields_item_desde_post(request, presupuesto):
    """Construye los campos de un ItemPresupuesto desde el POST del cotizador.

    Devuelve (fields, error). Si error != None, la validación falló y no se debe
    guardar. Lo comparten agregar_item (crear) y editar_item (actualizar), para
    que editar use exactamente la misma lógica de cálculo que agregar.
    """
    data = request.POST
    descripcion = data.get('descripcion', '').strip()
    try:
        cantidad = max(1, int(data.get('cantidad', 1) or 1))
    except (TypeError, ValueError):
        cantidad = 1

    # PVC: valor manual en dólares
    if presupuesto.tipo_material == 'pvc':
        if not presupuesto.tiene_cotizacion_usd():
            return None, 'Configurá la cotización USD del presupuesto antes de agregar ítems.'
        valor_usd = float(data.get('valor_usd', 0) or 0)
        margen_porcentaje = float(data.get('margen_porcentaje', 30) or 30)
        valor_base = valor_usd * float(presupuesto.cotizacion_usd)
        precio_unitario_base = valor_base * (1 + margen_porcentaje / 100)
        precio_unitario = precio_unitario_base
        if presupuesto.tipo_obra == 'renovacion':
            precio_unitario = precio_unitario_base + float(presupuesto.recargo_renovacion_unitario or 0)
        return {
            'descripcion': descripcion or 'Item sin descripción',
            'cantidad': cantidad, 'ancho_mm': 0, 'alto_mm': 0,
            'margen_porcentaje': margen_porcentaje, 'precio_unitario': precio_unitario,
            'resultado_json': {
                'precio_unitario_base': precio_unitario_base, 'valor_base': valor_base,
                'valor_usd': valor_usd, 'margen': margen_porcentaje,
                'recargo_renovacion_unitario_aplicado': float(presupuesto.recargo_renovacion_unitario or 0) if presupuesto.tipo_obra == 'renovacion' else 0,
                'tipo': 'pvc_simple',
            },
        }, None

    # Producto terciarizado: precio final manual, sin marco ni despiece
    producto_id_raw = data.get('producto_id')
    if producto_id_raw and Producto.objects.filter(pk=producto_id_raw, terciarizado=True).exists():
        try:
            precio_unitario = float(data.get('precio_terciarizado', 0) or 0)
        except (TypeError, ValueError):
            precio_unitario = 0
        if precio_unitario <= 0:
            return None, 'Ingresá el precio final del producto terciarizado.'
        return {
            'descripcion': descripcion or 'Producto terciarizado',
            'cantidad': cantidad, 'ancho_mm': 0, 'alto_mm': 0,
            'margen_porcentaje': 0, 'precio_unitario': precio_unitario,
            'resultado_json': {
                'precio_unitario_base': precio_unitario, 'tipo': 'terciarizado',
                'producto_id': int(producto_id_raw),
            },
        }, None

    # Aluminio: cotizador completo
    config = {
        'producto_id': data.get('producto_id') and int(data['producto_id']),
        'marco_id': data.get('marco_id') and int(data['marco_id']),
        'hoja_id': data.get('hoja_id') and int(data['hoja_id']),
        'vidrio_codigo': data.get('vidrio_codigo') or None,
        'interior_id': data.get('interior_id') and int(data['interior_id']),
        'tratamiento_id': data.get('tratamiento_id') and int(data['tratamiento_id']),
        'ancho_mm': int(data.get('ancho_mm') or 1200),
        'alto_mm': int(data.get('alto_mm') or 1500),
        'margen_porcentaje': float(data.get('margen_porcentaje') or 30),
    }
    try:
        opcionales_list = json.loads(data.get('opcionales_json', '[]'))
        if opcionales_list:
            config['opcionales'] = opcionales_list
    except (json.JSONDecodeError, TypeError):
        pass

    descripcion = descripcion or 'Abertura sin descripción'
    try:
        resultado = calcular_precio(config)
    except PricingError as e:
        return None, f'Error al calcular: {e}'

    precio_unitario_base = resultado['precio_total']
    resultado['precio_unitario_base'] = precio_unitario_base
    resultado['recargo_renovacion_unitario_aplicado'] = 0
    resultado['recargo_renovacion_total_aplicado'] = 0
    precio_unitario = precio_unitario_base
    if presupuesto.tipo_obra == 'renovacion':
        recargo_unitario = float(presupuesto.recargo_renovacion_unitario or 0)
        resultado['recargo_renovacion_unitario_aplicado'] = recargo_unitario
        resultado['recargo_renovacion_total_aplicado'] = recargo_unitario * cantidad
        precio_unitario = precio_unitario_base + recargo_unitario
    resultado['snapshot_item'] = build_item_snapshot(config, descripcion, cantidad)
    return {
        'descripcion': descripcion, 'cantidad': cantidad,
        'ancho_mm': config['ancho_mm'], 'alto_mm': config['alto_mm'],
        'margen_porcentaje': config['margen_porcentaje'],
        'precio_unitario': precio_unitario, 'resultado_json': resultado,
    }, None


@login_required
def agregar_item(request, pk):
    presupuesto = get_object_or_404(Presupuesto.objects.filter(deleted_at__isnull=True), pk=pk)
    if presupuesto.esta_bloqueado():
        messages.error(request, 'No se pueden agregar ítems a un presupuesto confirmado o cancelado.')
        return redirect('presupuestos:presupuestos-detalle', pk=pk)

    if not presupuesto.tipo_obra:
        messages.error(request, 'Debes definir si el presupuesto es obra nueva o renovación antes de agregar ítems.')
        return redirect('presupuestos:presupuestos-detalle', pk=pk)

    if request.method == 'POST':
        fields, error = _fields_item_desde_post(request, presupuesto)
        if error:
            messages.error(request, error)
            return redirect('presupuestos:presupuestos-detalle', pk=pk)
        item = ItemPresupuesto.objects.create(
            presupuesto=presupuesto, orden=presupuesto.items.count(), **fields,
        )
        presupuesto.recalcular_total()
        messages.success(request, f'Ítem "{item.descripcion}" agregado.')
        return redirect('presupuestos:presupuestos-detalle', pk=pk)

    return redirect('presupuestos:presupuestos-detalle', pk=pk)


@login_required
@require_POST
def actualizar_configuracion_obra(request, pk):
    presupuesto = get_object_or_404(_get_detalle_queryset().filter(deleted_at__isnull=True), pk=pk)
    if presupuesto.esta_bloqueado():
        messages.error(request, 'No se puede modificar un presupuesto confirmado o cancelado.')
        return redirect('presupuestos:presupuestos-detalle', pk=pk)

    configuracion_form = PresupuestoConfiguracionObraForm(request.POST, instance=presupuesto)
    if configuracion_form.is_valid():
        presupuesto = configuracion_form.save(commit=False)
        presupuesto.updated_by = request.user
        presupuesto.save()
        presupuesto.aplicar_validez_dias()
        presupuesto.actualizar_items_por_configuracion()
        presupuesto.recalcular_total()
        messages.success(request, 'Configuración de obra actualizada.')
        return redirect('presupuestos:presupuestos-detalle', pk=pk)

    return render(
        request,
        'presupuestos/detalle.html',
        _build_detalle_context(presupuesto, configuracion_form=configuracion_form),
    )


@login_required
@require_POST
def editar_item(request, pk, ipk):
    presupuesto = get_object_or_404(Presupuesto.objects.filter(deleted_at__isnull=True), pk=pk)
    if presupuesto.esta_bloqueado():
        messages.error(request, 'No se puede modificar un presupuesto confirmado o cancelado.')
        return redirect('presupuestos:presupuestos-detalle', pk=pk)

    item = get_object_or_404(ItemPresupuesto, pk=ipk, presupuesto=presupuesto)

    fields, error = _fields_item_desde_post(request, presupuesto)
    if error:
        messages.error(request, error)
        return redirect('presupuestos:presupuestos-detalle', pk=pk)

    for campo, valor in fields.items():
        setattr(item, campo, valor)
    item.save()  # recalcula precio_total = precio_unitario * cantidad
    presupuesto.recalcular_total()
    messages.success(request, f'Ítem "{item.descripcion}" actualizado.')
    return redirect('presupuestos:presupuestos-detalle', pk=pk)


@login_required
@require_POST
def eliminar_item(request, pk, ipk):
    presupuesto = get_object_or_404(Presupuesto.objects.filter(deleted_at__isnull=True), pk=pk)
    if presupuesto.esta_bloqueado():
        messages.error(request, 'No se puede modificar un presupuesto confirmado o cancelado.')
        return redirect('presupuestos:presupuestos-detalle', pk=pk)

    item = get_object_or_404(ItemPresupuesto, pk=ipk, presupuesto=presupuesto)
    item.delete()
    presupuesto.recalcular_total()
    messages.success(request, 'Ítem eliminado.')
    return redirect('presupuestos:presupuestos-detalle', pk=pk)


@login_required
@require_POST
def comentar(request, pk):
    presupuesto = get_object_or_404(Presupuesto.objects.filter(deleted_at__isnull=True), pk=pk)
    form = ComentarioForm(request.POST)
    if form.is_valid():
        comentario = form.save(commit=False)
        comentario.presupuesto = presupuesto
        comentario.autor = request.user
        comentario.save()
    return redirect('presupuestos:presupuestos-detalle', pk=pk)


@login_required
@require_POST
def cambiar_estado(request, pk):
    presupuesto = get_object_or_404(Presupuesto.objects.filter(deleted_at__isnull=True), pk=pk)
    nuevo_estado = request.POST.get('estado')
    estados_validos = [e[0] for e in Presupuesto.ESTADO_CHOICES]

    if nuevo_estado not in estados_validos:
        messages.error(request, 'Estado inválido.')
        return redirect('presupuestos:presupuestos-detalle', pk=pk)

    if presupuesto.esta_bloqueado():
        messages.error(request, 'No se puede cambiar el estado de un presupuesto confirmado o cancelado.')
        return redirect('presupuestos:presupuestos-detalle', pk=pk)

    presupuesto.estado = nuevo_estado
    presupuesto.save(update_fields=['estado'])
    messages.success(request, f'Estado actualizado a "{presupuesto.get_estado_display()}".')
    return redirect('presupuestos:presupuestos-detalle', pk=pk)


@login_required
@require_POST
def eliminar(request, pk):
    presupuesto = get_object_or_404(Presupuesto, pk=pk, deleted_at__isnull=True)
    numero = presupuesto.numero
    presupuesto.deleted_at = timezone.now()
    presupuesto.deleted_by = request.user
    presupuesto.save(update_fields=['deleted_at', 'deleted_by'])
    messages.success(request, f'Presupuesto {numero} eliminado correctamente.')
    return redirect('presupuestos:presupuestos-lista')


def _build_blank_recibo_context(presupuesto):
    cliente = presupuesto.cliente
    return {
        'copias': range(2),
        'logo_url': _build_logo_data_url(),
        'cliente_nombre': cliente.get_nombre_completo(),
        'cliente_direccion': cliente.direccion or '',
        'cliente_localidad': cliente.localidad or '',
        'cliente_cp': '',
        'cliente_cuit': _formatear_cuit(cliente.cuit),
        'cliente_condicion_iva': cliente.get_condicion_iva_display(),
        'filas_vacias': range(4),
    }


@login_required
def recibo(request, pk):
    presupuesto = get_object_or_404(
        Presupuesto.objects.filter(deleted_at__isnull=True).select_related('cliente'),
        pk=pk,
    )
    html = render_to_string(
        'presupuestos/recibo_blank.html',
        _build_blank_recibo_context(presupuesto),
    )

    result = io.BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=result)
    if pisa_status.err:
        return HttpResponse(
            'No se pudo generar la plantilla del recibo.',
            content_type='text/plain; charset=utf-8',
            status=500,
        )

    response = HttpResponse(result.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="recibo_plantilla_{presupuesto.numero}.pdf"'
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


@login_required
def pdf(request, pk):
    presupuesto = get_object_or_404(
        Presupuesto.objects.filter(deleted_at__isnull=True).select_related('cliente', 'created_by').prefetch_related('items'),
        pk=pk,
    )
    items_pdf = [build_pdf_item_context(item) for item in presupuesto.items.all()]
    pdf_subtotal = presupuesto.get_total_items()
    pdf_iva = pdf_subtotal * Decimal('0.21')
    return render(request, 'presupuestos/pdf.html', {
        'logo_url': _build_logo_data_url(),
        'presupuesto': presupuesto,
        'items_pdf': items_pdf,
        'pdf_subtotal': pdf_subtotal,
        'pdf_iva': pdf_iva,
    })
