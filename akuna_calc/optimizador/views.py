from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.pdf import contexto_base_pdf, pdf_response
from plantillas.models import OrdenFabricacion
from .forms import ParametrosPlanForm
from .models import PlanCorte
from .services import plan as servicio


def _prefetch_ordenes():
    """Lo que lee `firma_de_ordenes`, para que `esta_vigente()` no consulte por orden."""
    ordenes = OrdenFabricacion.objects.select_related('item_presupuesto').prefetch_related('medidas')
    return Prefetch('ordenes', queryset=ordenes)


def _contexto_nuevo(form):
    return {
        'form': form,
        'seleccion': [str(v) for v in (form['pedidos'].value() or [])],
        'resumen': servicio.resumen_pedidos(),
        'total_planes': PlanCorte.objects.count(),
        'pestana': 'nuevo',
    }


def _render_nuevo(request, form):
    return render(request, 'optimizador/nuevo.html', _contexto_nuevo(form))


@login_required
def nuevo(request):
    return _render_nuevo(request, ParametrosPlanForm())


@login_required
@require_POST
def calcular(request):
    form = ParametrosPlanForm(request.POST)
    if not form.is_valid():
        return _render_nuevo(request, form)
    params = form.params()
    pedidos = list(form.cleaned_data['pedidos'])
    resultado = servicio.calcular(pedidos, params)
    return render(request, 'optimizador/resultado.html', {
        'resultado': resultado,
        'form': form,
        'pedidos_ids': [p.pk for p in pedidos],
        'pasar_a_corte': form.cleaned_data['pasar_a_corte'],
        'pestana': 'nuevo',
    })


@login_required
@require_POST
def guardar(request):
    form = ParametrosPlanForm(request.POST)
    if not form.is_valid():
        return _render_nuevo(request, form)
    try:
        plan = servicio.guardar(
            list(form.cleaned_data['pedidos']), form.params(), request.user, form.cleaned_data['pasar_a_corte'],
        )
    except ValidationError as error:
        messages.error(request, ' '.join(error.messages))
        return redirect('optimizador:nuevo')
    messages.success(request, f'{plan} guardado.')
    return redirect('optimizador:detalle', pk=plan.pk)


@login_required
def lista(request):
    planes = PlanCorte.objects.select_related('usuario').prefetch_related(_prefetch_ordenes())
    page_obj = Paginator(planes, 20).get_page(request.GET.get('page'))
    for plan in page_obj:
        plan.vigente = plan.esta_vigente()
    return render(request, 'optimizador/lista.html', {
        'planes': page_obj, 'page_obj': page_obj, 'total_planes': page_obj.paginator.count, 'pestana': 'planes',
    })


@login_required
def detalle(request, pk):
    plan = get_object_or_404(PlanCorte.objects.prefetch_related(_prefetch_ordenes()), pk=pk)
    return render(request, 'optimizador/detalle.html', {
        'plan': plan, 'resultado': plan.resultado, 'vigente': plan.esta_vigente(), 'pestana': 'planes',
    })


@login_required
def pdf(request, pk):
    plan = get_object_or_404(PlanCorte, pk=pk)
    contexto = contexto_base_pdf()
    contexto.update({'plan': plan, 'resultado': plan.resultado})
    return pdf_response(
        'optimizador/planilla_pdf.html', contexto, f'plan-corte-{plan.numero_formateado}.pdf',
        error_message='No se pudo generar la planilla de corte.',
    )
