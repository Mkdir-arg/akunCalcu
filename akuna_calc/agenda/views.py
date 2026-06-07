import calendar as _calendar
import json
import os

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import EventoAgendaForm
from .models import EventoAgenda


NOMBRES_MES = [
    '', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
]


def _validar_token(request):
    token = request.headers.get('X-Bot-Secret', '')
    secret = os.environ.get('TELEGRAM_BOT_SECRET', '')
    return bool(secret) and token == secret


class EventoListView(LoginRequiredMixin, ListView):
    model = EventoAgenda
    template_name = 'agenda/evento_list.html'
    context_object_name = 'eventos'
    paginate_by = 20

    def get_queryset(self):
        return EventoAgenda.objects.prefetch_related('destinatarios')


class EventoCreateView(LoginRequiredMixin, CreateView):
    model = EventoAgenda
    form_class = EventoAgendaForm
    template_name = 'agenda/evento_form.html'
    success_url = reverse_lazy('agenda:lista')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "Evento agendado correctamente.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Nuevo evento'
        return ctx


class EventoUpdateView(LoginRequiredMixin, UpdateView):
    model = EventoAgenda
    form_class = EventoAgendaForm
    template_name = 'agenda/evento_form.html'
    success_url = reverse_lazy('agenda:lista')

    def form_valid(self, form):
        messages.success(self.request, "Evento actualizado correctamente.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Editar evento'
        return ctx


class EventoDeleteView(LoginRequiredMixin, DeleteView):
    model = EventoAgenda
    success_url = reverse_lazy('agenda:lista')

    def form_valid(self, form):
        messages.success(self.request, "Evento eliminado.")
        return super().form_valid(form)


@login_required
def calendario(request):
    hoy = timezone.localdate()
    try:
        anio = int(request.GET.get('anio', hoy.year))
        mes = int(request.GET.get('mes', hoy.month))
    except (TypeError, ValueError):
        anio, mes = hoy.year, hoy.month
    if not 1 <= mes <= 12:
        anio, mes = hoy.year, hoy.month

    eventos = list(
        EventoAgenda.objects.filter(activo=True).exclude(estado='cancelado')
    )

    cal = _calendar.Calendar(firstweekday=0)  # lunes primero
    semanas = []
    for semana in cal.monthdatescalendar(anio, mes):
        fila = []
        for dia in semana:
            fila.append({
                'fecha': dia,
                'in_month': dia.month == mes,
                'is_today': dia == hoy,
                'eventos': [e for e in eventos if e.ocurre_en(dia)],
            })
        semanas.append(fila)

    mes_prev, anio_prev = (12, anio - 1) if mes == 1 else (mes - 1, anio)
    mes_next, anio_next = (1, anio + 1) if mes == 12 else (mes + 1, anio)

    return render(request, 'agenda/evento_calendar.html', {
        'semanas': semanas,
        'anio': anio,
        'mes': mes,
        'nombre_mes': NOMBRES_MES[mes],
        'mes_prev': mes_prev, 'anio_prev': anio_prev,
        'mes_next': mes_next, 'anio_next': anio_next,
        'hoy': hoy,
    })


# --- API para n8n ---

@csrf_exempt
@require_POST
def api_pendientes(request):
    if not _validar_token(request):
        return JsonResponse({'error': 'No autorizado'}, status=401)

    eventos = EventoAgenda.objects.pendientes()
    data = []
    for evento in eventos:
        destinatarios = [
            {'numero': n.numero, 'nombre': n.nombre}
            for n in evento.destinatarios.all() if n.activo
        ]
        if not destinatarios:
            continue
        data.append({
            'id': evento.pk,
            'titulo': evento.titulo,
            'descripcion': evento.descripcion,
            'tipo': evento.tipo,
            'mensaje': evento.mensaje(),
            'destinatarios': destinatarios,
        })

    return JsonResponse({'ok': True, 'eventos': data, 'cantidad': len(data)})


@csrf_exempt
@require_POST
def api_marcar_enviado(request):
    if not _validar_token(request):
        return JsonResponse({'error': 'No autorizado'}, status=401)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    ids = payload.get('ids', [])
    if not isinstance(ids, list):
        return JsonResponse({'error': 'ids debe ser una lista'}, status=400)

    marcados = 0
    for evento in EventoAgenda.objects.filter(pk__in=ids):
        evento.marcar_enviado()
        marcados += 1

    return JsonResponse({'ok': True, 'marcados': marcados})
