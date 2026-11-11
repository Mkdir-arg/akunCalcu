from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, ListView, UpdateView

from . import motor
from .forms import (
    ConfiguracionAgenteForm,
    DiaCerradoForm,
    EntradaConocimientoForm,
    FranjaAtencionForm,
    FranjaTecnicoFormSet,
    MensajeSimuladoForm,
    SimulacionForm,
    TecnicoVisitaForm,
    ZonaTecnicoFormSet,
)
from .models import (
    DIAS_SEMANA,
    ConfiguracionAgente,
    Conversacion,
    DiaCerrado,
    EntradaConocimiento,
    FranjaAtencion,
    TecnicoVisita,
)


# ---------------------------------------------------------------------------
# Configuración general
# ---------------------------------------------------------------------------

@login_required
def configuracion(request):
    config = ConfiguracionAgente.obtener()
    if request.method == 'POST':
        form = ConfiguracionAgenteForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, 'Configuración del agente guardada.')
            return redirect('agente:configuracion')
    else:
        form = ConfiguracionAgenteForm(instance=config)
    return render(request, 'agente/configuracion.html', {'form': form, 'config': config})


# ---------------------------------------------------------------------------
# Horario de atención
# ---------------------------------------------------------------------------

def _render_horario(request, franja_form=None, dia_form=None, status=200):
    franjas = list(FranjaAtencion.objects.all())
    semana = [
        {'nombre': nombre, 'franjas': [f for f in franjas if f.dia_semana == numero]}
        for numero, nombre in DIAS_SEMANA
    ]
    return render(request, 'agente/horario.html', {
        'semana': semana,
        'dias_cerrados': DiaCerrado.objects.all(),
        'franja_form': franja_form or FranjaAtencionForm(),
        'dia_form': dia_form or DiaCerradoForm(),
    }, status=status)


@login_required
def horario(request):
    return _render_horario(request)


@login_required
@require_POST
def franja_crear(request):
    form = FranjaAtencionForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, 'Franja de atención agregada.')
        return redirect('agente:horario')
    return _render_horario(request, franja_form=form, status=400)


@login_required
def franja_editar(request, pk):
    franja = get_object_or_404(FranjaAtencion, pk=pk)
    if request.method == 'POST':
        form = FranjaAtencionForm(request.POST, instance=franja)
        if form.is_valid():
            form.save()
            messages.success(request, 'Franja de atención actualizada.')
            return redirect('agente:horario')
    else:
        form = FranjaAtencionForm(instance=franja)
    return render(request, 'agente/franja_form.html', {'form': form, 'franja': franja})


@login_required
@require_POST
def franja_eliminar(request, pk):
    franja = get_object_or_404(FranjaAtencion, pk=pk)
    franja.delete()
    messages.success(request, 'Franja de atención eliminada.')
    return redirect('agente:horario')


@login_required
@require_POST
def dia_cerrado_crear(request):
    form = DiaCerradoForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, 'Día cerrado agregado.')
        return redirect('agente:horario')
    return _render_horario(request, dia_form=form, status=400)


@login_required
@require_POST
def dia_cerrado_eliminar(request, pk):
    dia = get_object_or_404(DiaCerrado, pk=pk)
    dia.delete()
    messages.success(request, 'Día cerrado eliminado.')
    return redirect('agente:horario')


# ---------------------------------------------------------------------------
# Visitas técnicas
# ---------------------------------------------------------------------------

class TecnicoListView(LoginRequiredMixin, ListView):
    model = TecnicoVisita
    template_name = 'agente/tecnico_list.html'
    context_object_name = 'tecnicos'

    def get_queryset(self):
        return TecnicoVisita.objects.select_related('usuario').prefetch_related('franjas', 'zonas__provincia')


class TecnicoFormMixin(LoginRequiredMixin):
    model = TecnicoVisita
    form_class = TecnicoVisitaForm
    template_name = 'agente/tecnico_form.html'
    success_url = reverse_lazy('agente:tecnicos')
    mensaje_ok = ''

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        instancia = self.object if getattr(self, 'object', None) else None
        if 'franjas' not in context:
            context['franjas'] = FranjaTecnicoFormSet(instance=instancia, prefix='franjas')
        if 'zonas' not in context:
            context['zonas'] = ZonaTecnicoFormSet(instance=instancia, prefix='zonas')
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object() if self.kwargs.get('pk') else None
        form = self.get_form()
        instancia = form.instance
        franjas = FranjaTecnicoFormSet(request.POST, instance=instancia, prefix='franjas')
        zonas = ZonaTecnicoFormSet(request.POST, instance=instancia, prefix='zonas')
        if form.is_valid() and franjas.is_valid() and zonas.is_valid():
            with transaction.atomic():
                self.object = form.save()
                franjas.instance = self.object
                franjas.save()
                zonas.instance = self.object
                zonas.save()
            messages.success(request, self.mensaje_ok)
            return redirect(self.success_url)
        return self.render_to_response(
            self.get_context_data(form=form, franjas=franjas, zonas=zonas), status=400,
        )


class TecnicoCreateView(TecnicoFormMixin, CreateView):
    mensaje_ok = 'Técnico agregado.'


class TecnicoUpdateView(TecnicoFormMixin, UpdateView):
    mensaje_ok = 'Técnico actualizado.'


class TecnicoDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        tecnico = get_object_or_404(TecnicoVisita, pk=pk)
        nombre = str(tecnico)
        tecnico.delete()
        messages.success(request, f"Técnico '{nombre}' eliminado.")
        return redirect('agente:tecnicos')


# ---------------------------------------------------------------------------
# Base de conocimiento
# ---------------------------------------------------------------------------

class ConocimientoListView(LoginRequiredMixin, ListView):
    model = EntradaConocimiento
    template_name = 'agente/conocimiento_list.html'
    context_object_name = 'entradas'
    paginate_by = 20

    def get_queryset(self):
        queryset = EntradaConocimiento.objects.all()
        q = self.request.GET.get('q', '').strip()
        if q:
            queryset = queryset.filter(Q(tema__icontains=q) | Q(contenido__icontains=q))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        q = self.request.GET.get('q', '').strip()
        context['q'] = q
        context['query_sin_page'] = urlencode({'q': q}) if q else ''
        return context


class ConocimientoCreateView(LoginRequiredMixin, CreateView):
    model = EntradaConocimiento
    form_class = EntradaConocimientoForm
    template_name = 'agente/conocimiento_form.html'
    success_url = reverse_lazy('agente:conocimiento')

    def form_valid(self, form):
        messages.success(self.request, 'Entrada agregada a la base de conocimiento.')
        return super().form_valid(form)


class ConocimientoUpdateView(LoginRequiredMixin, UpdateView):
    model = EntradaConocimiento
    form_class = EntradaConocimientoForm
    template_name = 'agente/conocimiento_form.html'
    success_url = reverse_lazy('agente:conocimiento')

    def form_valid(self, form):
        messages.success(self.request, 'Entrada actualizada.')
        return super().form_valid(form)


class ConocimientoDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        entrada = get_object_or_404(EntradaConocimiento, pk=pk)
        tema = entrada.tema
        entrada.delete()
        messages.success(request, f"Entrada '{tema}' eliminada.")
        return redirect('agente:conocimiento')


# ---------------------------------------------------------------------------
# Simulador de conversación
# ---------------------------------------------------------------------------

def _mensaje_a_dict(mensaje):
    return {
        'id': mensaje.pk,
        'rol': mensaje.rol,
        'texto': mensaje.texto,
        'hora': timezone.localtime(mensaje.created_at).strftime('%H:%M'),
        'detalle': mensaje.detalle or {},
    }


def _simulacion_o_404(pk):
    return get_object_or_404(Conversacion, pk=pk, es_simulacion=True)


class SimuladorListView(LoginRequiredMixin, ListView):
    model = Conversacion
    template_name = 'agente/simulador_list.html'
    context_object_name = 'simulaciones'
    paginate_by = 20

    def get_queryset(self):
        return (
            Conversacion.objects.filter(es_simulacion=True)
            .select_related('iniciada_por')
            .annotate(cantidad_mensajes=Count('mensajes'))
            .order_by('-updated_at')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = SimulacionForm()
        return context


@login_required
@require_POST
def simulacion_nueva(request):
    form = SimulacionForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Revisá los datos de la simulación.')
        return redirect('agente:simulador')
    conversacion = form.save(commit=False)
    conversacion.es_simulacion = True
    conversacion.iniciada_por = request.user
    conversacion.save()
    return redirect('agente:simulacion', pk=conversacion.pk)


@login_required
def simulacion(request, pk):
    conversacion = _simulacion_o_404(pk)
    config = ConfiguracionAgente.obtener()
    mensajes = [_mensaje_a_dict(m) for m in conversacion.mensajes.all()]
    return render(request, 'agente/simulacion.html', {
        'conversacion': conversacion,
        'config': config,
        'mensajes_json': mensajes,
        'momento': motor.momento_de(conversacion),
    })


@login_required
@require_POST
def simulacion_enviar(request, pk):
    conversacion = _simulacion_o_404(pk)
    form = MensajeSimuladoForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'error': 'Escribí un mensaje (hasta 2000 caracteres).'}, status=400)
    nuevos = motor.responder(conversacion, form.cleaned_data['texto'])
    return JsonResponse({'mensajes': [_mensaje_a_dict(m) for m in nuevos]})
