import base64
import io
from pathlib import Path

from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from xhtml2pdf import pisa

from configuracion.models import ConfiguracionGeneral
from .models import PedidoFabrica, OrdenFabricacion, MedidaOrdenFabricacion
from .forms import OrdenFabricacionForm


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


@login_required
def index(request):
    """Redirección de la raíz de la app al listado de pedidos"""
    return redirect('plantillas:pedido_list')


# ============ PEDIDOS DE FÁBRICA ============

@login_required
def pedido_list(request):
    """Listado de pedidos"""
    pedidos = PedidoFabrica.objects.select_related('presupuesto').all()
    return render(request, 'plantillas/pedido_list.html', {'pedidos': pedidos})


@login_required
def pedido_create(request):
    """Crear pedido"""
    if request.method == 'POST':
        numero = request.POST.get('numero')
        cliente = request.POST.get('cliente')
        observaciones = request.POST.get('observaciones', '')

        pedido = PedidoFabrica.objects.create(
            numero=numero,
            cliente=cliente,
            observaciones=observaciones,
            usuario=request.user
        )
        messages.success(request, f'Pedido {numero} creado exitosamente')
        return redirect('plantillas:pedido_detail', pk=pedido.pk)

    # Generar número automático
    ultimo = PedidoFabrica.objects.count() + 1
    numero_sugerido = f"PF-{ultimo:04d}"

    return render(request, 'plantillas/pedido_form.html', {'numero_sugerido': numero_sugerido})


@login_required
def pedido_detail(request, pk):
    """Detalle de pedido con sus órdenes de fabricación"""
    pedido = get_object_or_404(
        PedidoFabrica.objects.select_related('presupuesto', 'presupuesto__venta', 'usuario'),
        pk=pk,
    )
    ordenes = pedido.ordenes.prefetch_related('medidas').all()
    return render(request, 'plantillas/pedido_detail.html', {'pedido': pedido, 'ordenes': ordenes})


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
        item_txt = items[i].strip() if i < len(items) else ''
        medida_txt = medidas[i].strip() if i < len(medidas) else ''
        obs_txt = observaciones[i].strip() if i < len(observaciones) else ''
        piso_txt = pisos[i].strip() if i < len(pisos) else ''
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


@login_required
def orden_create(request, pedido_pk):
    """Alta manual de una orden de fabricación dentro de un pedido."""
    pedido = get_object_or_404(PedidoFabrica, pk=pedido_pk)
    orden = OrdenFabricacion.objects.create(
        pedido=pedido,
        numero=OrdenFabricacion.generar_numero(),
        orden=pedido.ordenes.count() + 1,
        cliente_nombre=pedido.cliente,
    )
    messages.success(request, f'Orden {orden.numero_formateado} creada. Completá el detalle.')
    return redirect('plantillas:orden_edit', pk=orden.pk)


@login_required
def orden_edit(request, pk):
    """Editar el detalle de una orden de fabricación."""
    orden = get_object_or_404(
        OrdenFabricacion.objects.select_related('pedido').prefetch_related('medidas'),
        pk=pk,
    )
    if request.method == 'POST':
        form = OrdenFabricacionForm(request.POST, instance=orden)
        if form.is_valid():
            form.save()
            _guardar_medidas(orden, request)
            messages.success(request, f'Orden {orden.numero_formateado} actualizada.')
            return redirect('plantillas:pedido_detail', pk=orden.pedido.pk)
    else:
        form = OrdenFabricacionForm(instance=orden)

    return render(request, 'plantillas/orden_form.html', {
        'form': form,
        'orden': orden,
        'pedido': orden.pedido,
        'medidas': orden.medidas.all(),
    })


@login_required
@require_POST
def orden_delete(request, pk):
    """Eliminar una orden de fabricación."""
    orden = get_object_or_404(OrdenFabricacion, pk=pk)
    pedido_pk = orden.pedido.pk
    numero = orden.numero_formateado
    orden.delete()
    messages.success(request, f'Orden {numero} eliminada.')
    return redirect('plantillas:pedido_detail', pk=pedido_pk)


@login_required
def orden_pdf(request, pk):
    """Genera el PDF A4 de la orden de fabricación (planilla de fábrica)."""
    orden = get_object_or_404(
        OrdenFabricacion.objects.select_related('pedido').prefetch_related('medidas'),
        pk=pk,
    )
    html = render_to_string('plantillas/orden_pdf.html', {
        'orden': orden,
        'medidas': orden.medidas.all(),
        'empresa': ConfiguracionGeneral.get_datos_empresa(),
        'logo_url': _build_logo_data_url(),
        'croquis_filas': range(11),
        'croquis_cols': range(20),
    })

    result = io.BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=result)
    if pisa_status.err:
        return HttpResponse('No se pudo generar el PDF de la orden.',
                            content_type='text/plain; charset=utf-8', status=500)

    response = HttpResponse(result.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="orden_fabricacion_{orden.numero_formateado}.pdf"'
    return response
