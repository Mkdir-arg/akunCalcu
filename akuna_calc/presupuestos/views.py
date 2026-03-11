import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

from pricing.services.calculator import calcular_precio, PricingError
from .models import Presupuesto, ItemPresupuesto, ComentarioPresupuesto
from .forms import PresupuestoForm, ItemPresupuestoForm, ComentarioForm


@login_required
def lista(request):
    qs = Presupuesto.objects.select_related('cliente', 'created_by')

    estado = request.GET.get('estado', '')
    cliente_q = request.GET.get('cliente', '')

    if estado:
        qs = qs.filter(estado=estado)
    if cliente_q:
        qs = qs.filter(
            cliente__nombre__icontains=cliente_q
        ) | qs.filter(
            cliente__apellido__icontains=cliente_q
        ) | qs.filter(
            cliente__razon_social__icontains=cliente_q
        )

    return render(request, 'presupuestos/lista.html', {
        'presupuestos': qs,
        'estado_actual': estado,
        'cliente_q': cliente_q,
        'estados': Presupuesto.ESTADO_CHOICES,
    })


@login_required
def crear(request):
    if request.method == 'POST':
        form = PresupuestoForm(request.POST)
        if form.is_valid():
            presupuesto = form.save(commit=False)
            presupuesto.numero = Presupuesto.generar_numero()
            presupuesto.created_by = request.user
            presupuesto.save()
            messages.success(request, f'Presupuesto {presupuesto.numero} creado.')
            return redirect('presupuestos:presupuestos-detalle', pk=presupuesto.pk)
    else:
        form = PresupuestoForm()
    return render(request, 'presupuestos/form.html', {'form': form, 'titulo': 'Nuevo Presupuesto'})


@login_required
def detalle(request, pk):
    presupuesto = get_object_or_404(
        Presupuesto.objects.select_related('cliente', 'created_by').prefetch_related('items', 'comentarios__autor'),
        pk=pk,
    )
    comentario_form = ComentarioForm()
    return render(request, 'presupuestos/detalle.html', {
        'presupuesto': presupuesto,
        'comentario_form': comentario_form,
    })


@login_required
def editar(request, pk):
    presupuesto = get_object_or_404(Presupuesto, pk=pk)
    if presupuesto.esta_bloqueado():
        messages.error(request, 'No se puede editar un presupuesto confirmado o cancelado.')
        return redirect('presupuestos:presupuestos-detalle', pk=pk)

    if request.method == 'POST':
        form = PresupuestoForm(request.POST, instance=presupuesto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Presupuesto actualizado.')
            return redirect('presupuestos:presupuestos-detalle', pk=pk)
    else:
        form = PresupuestoForm(instance=presupuesto)
    return render(request, 'presupuestos/form.html', {'form': form, 'titulo': 'Editar Presupuesto', 'presupuesto': presupuesto})


@login_required
def agregar_item(request, pk):
    presupuesto = get_object_or_404(Presupuesto, pk=pk)
    if presupuesto.esta_bloqueado():
        messages.error(request, 'No se pueden agregar ítems a un presupuesto confirmado o cancelado.')
        return redirect('presupuestos:presupuestos-detalle', pk=pk)

    if request.method == 'POST':
        data = request.POST
        config = {
            'marco_id': data.get('marco_id') and int(data['marco_id']),
            'hoja_id': data.get('hoja_id') and int(data['hoja_id']),
            'vidrio_codigo': data.get('vidrio_codigo') or None,
            'interior_id': data.get('interior_id') and int(data['interior_id']),
            'tratamiento_id': data.get('tratamiento_id') and int(data['tratamiento_id']),
            'ancho_mm': int(data.get('ancho_mm', 1200)),
            'alto_mm': int(data.get('alto_mm', 1500)),
            'margen_porcentaje': float(data.get('margen_porcentaje', 30)),
        }
        descripcion = data.get('descripcion', '').strip() or 'Abertura sin descripción'
        cantidad = max(1, int(data.get('cantidad', 1)))

        try:
            resultado = calcular_precio(config)
            orden = presupuesto.items.count()
            item = ItemPresupuesto.objects.create(
                presupuesto=presupuesto,
                descripcion=descripcion,
                cantidad=cantidad,
                ancho_mm=config['ancho_mm'],
                alto_mm=config['alto_mm'],
                margen_porcentaje=config['margen_porcentaje'],
                precio_unitario=resultado['precio_total'],
                resultado_json=resultado,
                orden=orden,
            )
            presupuesto.recalcular_total()
            messages.success(request, f'Ítem "{item.descripcion}" agregado.')
            return redirect('presupuestos:presupuestos-detalle', pk=pk)
        except PricingError as e:
            messages.error(request, f'Error al calcular: {e}')

    return render(request, 'presupuestos/item_form.html', {'presupuesto': presupuesto})


@login_required
@require_POST
def eliminar_item(request, pk, ipk):
    presupuesto = get_object_or_404(Presupuesto, pk=pk)
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
    presupuesto = get_object_or_404(Presupuesto, pk=pk)
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
    presupuesto = get_object_or_404(Presupuesto, pk=pk)
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
def pdf(request, pk):
    presupuesto = get_object_or_404(
        Presupuesto.objects.select_related('cliente', 'created_by').prefetch_related('items'),
        pk=pk,
    )
    return render(request, 'presupuestos/pdf.html', {'presupuesto': presupuesto})
