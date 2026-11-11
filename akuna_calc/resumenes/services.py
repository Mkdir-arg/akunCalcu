"""Cálculo de los números del resumen de la dirección (REQ-071).

Todos los números salen de acá. GPT (en n8n) solo redacta a partir de este JSON:
no se le pasan datos crudos para que no invente cifras.
"""
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.utils import timezone

from agenda.models import EventoAgenda
from comercial.models import Venta
from gastos_diarios.models import NumeroAutorizado
from plantillas.models import HistorialPedidoFabrica, PedidoFabrica
from presupuestos.models import Presupuesto
from security.models import AuditLog
from solicitudes.models import SolicitudPresupuesto

PERIODO_DIA = 'dia'
PERIODO_SEMANA = 'semana'
PERIODOS = (PERIODO_DIA, PERIODO_SEMANA)

DIAS_SIN_RESPUESTA = 7
# Lo más viejo que esto son datos que nadie cerró: no sirve para el seguimiento diario.
DIAS_VENTANA = 30
LIMITE_LISTADO = 10
TIPOS_AGENDA = ('colocaciones', 'mediciones')


def destinatarios():
    """Números autorizados activos con «Recibe el resumen» marcado (se habilitan desde la web)."""
    return list(
        NumeroAutorizado.objects.filter(activo=True, recibe_resumen=True)
        .order_by('numero').values_list('numero', flat=True)
    )


def rango(periodo, fecha):
    """(desde, hasta) inclusivos. La semana va del lunes a `fecha`."""
    if periodo == PERIODO_SEMANA:
        return fecha - timedelta(days=fecha.weekday()), fecha
    return fecha, fecha


def _limites(desde, hasta):
    tz = timezone.get_current_timezone()
    inicio = timezone.make_aware(datetime.combine(desde, time.min), tz)
    fin = timezone.make_aware(datetime.combine(hasta + timedelta(days=1), time.min), tz)
    return inicio, fin


def _monto(valor):
    return float((valor or Decimal('0')).quantize(Decimal('0.01')))


def _nombre(user):
    if user is None:
        return 'Sin usuario'
    return user.get_full_name() or user.username


def _por_usuario(filas, campo_usuario, campo_monto=None):
    """Agrupa una lista de objetos por usuario → [{usuario, cantidad, monto}] ordenado por monto/cantidad."""
    grupos = {}
    for fila in filas:
        user = getattr(fila, campo_usuario)
        clave = _nombre(user)
        g = grupos.setdefault(clave, {'usuario': clave, 'cantidad': 0, 'monto': Decimal('0')})
        g['cantidad'] += 1
        if campo_monto:
            g['monto'] += getattr(fila, campo_monto) or Decimal('0')
    salida = sorted(grupos.values(), key=lambda g: (g['monto'], g['cantidad']), reverse=True)
    for g in salida:
        g['monto'] = _monto(g['monto'])
    return salida


def _presupuestos(inicio, fin, hoy):
    creados = list(
        Presupuesto.objects.filter(created_at__gte=inicio, created_at__lt=fin).select_related('created_by')
    )
    confirmados = list(
        Presupuesto.objects.filter(
            venta__created_at__gte=inicio, venta__created_at__lt=fin, venta__deleted_at__isnull=True,
        ).select_related('created_by', 'cliente')
    )
    tz = timezone.get_current_timezone()
    limite = timezone.make_aware(datetime.combine(hoy - timedelta(days=DIAS_SIN_RESPUESTA), time.max), tz)
    desde_ventana = timezone.make_aware(datetime.combine(hoy - timedelta(days=DIAS_VENTANA), time.min), tz)
    sin_respuesta_qs = (
        Presupuesto.objects.filter(estado='enviado', created_at__lte=limite, created_at__gte=desde_ventana)
        .select_related('cliente', 'created_by')
        .order_by('created_at')
    )
    sin_respuesta = list(sin_respuesta_qs[:LIMITE_LISTADO])
    return {
        'creados': {
            'cantidad': len(creados),
            'monto': _monto(sum((p.total for p in creados), Decimal('0'))),
            'por_vendedor': _por_usuario(creados, 'created_by', 'total'),
        },
        'confirmados': {
            'cantidad': len(confirmados),
            'monto': _monto(sum((p.total for p in confirmados), Decimal('0'))),
            'por_vendedor': _por_usuario(confirmados, 'created_by', 'total'),
        },
        'sin_respuesta': {
            'dias': DIAS_SIN_RESPUESTA,
            'ventana_dias': DIAS_VENTANA,
            'cantidad': sin_respuesta_qs.count(),
            'detalle': [
                {
                    'numero': p.numero,
                    'cliente': str(p.cliente) if p.cliente_id else '',
                    'vendedor': _nombre(p.created_by),
                    'monto': _monto(p.total),
                    'dias': (hoy - timezone.localtime(p.created_at).date()).days,
                }
                for p in sin_respuesta
            ],
        },
    }


def _ventas(inicio, fin, inicio_ant, fin_ant):
    def totales(a, b):
        r = Venta.objects.filter(created_at__gte=a, created_at__lt=b, deleted_at__isnull=True).aggregate(
            cantidad=Count('id'), monto=Sum('valor_total'),
        )
        return {'cantidad': r['cantidad'], 'monto': _monto(r['monto'])}

    actual = totales(inicio, fin)
    anterior = totales(inicio_ant, fin_ant)
    variacion = None
    if anterior['monto']:
        variacion = round((actual['monto'] - anterior['monto']) * 100 / anterior['monto'], 1)
    return {**actual, 'periodo_anterior': anterior, 'variacion_pct': variacion}


def _fabrica(inicio, fin):
    cambios = (
        HistorialPedidoFabrica.objects.filter(tipo='estado_pedido', created_at__gte=inicio, created_at__lt=fin)
        .select_related('pedido', 'usuario')
        .order_by('created_at')
    )
    abiertos = (
        PedidoFabrica.objects.exclude(estado__in=PedidoFabrica.ESTADOS_CERRADOS)
        .prefetch_related('ordenes')
    )
    desde_ventana = timezone.localdate() - timedelta(days=DIAS_VENTANA)
    atrasados = [p for p in abiertos if p.esta_atrasado and p.fecha_comprometida >= desde_ventana]
    atrasados.sort(key=lambda p: p.fecha_comprometida)
    hoy = timezone.localdate()
    return {
        'cambios_estado': {
            'cantidad': cambios.count(),
            'detalle': [
                {'pedido': h.pedido.numero, 'cliente': h.pedido.cliente, 'desde': h.desde, 'hasta': h.hasta,
                 'usuario': _nombre(h.usuario)}
                for h in cambios[:LIMITE_LISTADO]
            ],
        },
        'atrasados': {
            'ventana_dias': DIAS_VENTANA,
            'cantidad': len(atrasados),
            'detalle': [
                {'pedido': p.numero, 'cliente': p.cliente, 'estado': p.get_estado_display(),
                 'fecha_comprometida': p.fecha_comprometida.isoformat(),
                 'dias_atraso': (hoy - p.fecha_comprometida).days}
                for p in atrasados[:LIMITE_LISTADO]
            ],
        },
    }


def _agenda(desde, hasta):
    eventos = (
        EventoAgenda.objects.filter(fecha_evento__gte=desde, fecha_evento__lte=hasta, tipo__in=TIPOS_AGENDA)
        .exclude(estado='cancelado')
        .select_related('colocador', 'tecnico')
    )
    por_persona = {}
    for e in eventos:
        if e.colocador_id:
            persona = e.colocador.nombre
        elif e.tecnico_id:
            persona = _nombre(e.tecnico)
        else:
            persona = 'Sin asignar'
        g = por_persona.setdefault(persona, {'persona': persona, 'colocaciones': 0, 'mediciones': 0})
        g[e.tipo] += 1
    return {
        'programados': len(eventos),
        'por_persona': sorted(por_persona.values(), key=lambda g: g['persona']),
    }


def _solicitudes(inicio, fin):
    asignadas = SolicitudPresupuesto.objects.filter(fecha_asignacion__gte=inicio, fecha_asignacion__lt=fin)
    contestadas = SolicitudPresupuesto.objects.filter(fecha_contestada__gte=inicio, fecha_contestada__lt=fin)
    filas = {}
    for s in asignadas.select_related('vendedor'):
        clave = _nombre(s.vendedor)
        filas.setdefault(clave, {'vendedor': clave, 'asignadas': 0, 'contestadas': 0})['asignadas'] += 1
    for s in contestadas.select_related('vendedor'):
        clave = _nombre(s.vendedor)
        filas.setdefault(clave, {'vendedor': clave, 'asignadas': 0, 'contestadas': 0})['contestadas'] += 1
    return {
        'recibidas': SolicitudPresupuesto.objects.filter(fecha_recepcion__gte=inicio, fecha_recepcion__lt=fin).count(),
        'asignadas': asignadas.count(),
        'contestadas': contestadas.count(),
        'sin_contestar_total': SolicitudPresupuesto.objects.filter(estado=SolicitudPresupuesto.ESTADO_ASIGNADA).count(),
        'por_vendedor': sorted(filas.values(), key=lambda f: f['vendedor']),
    }


def _actividad(inicio, fin):
    filas = (
        AuditLog.objects.filter(
            timestamp__gte=inicio, timestamp__lt=fin, action__in=('CREATE', 'UPDATE', 'DELETE'),
            user__isnull=False,
        )
        .values('user__username', 'user__first_name', 'user__last_name')
        .annotate(
            total=Count('id'),
            altas=Count('id', filter=Q(action='CREATE')),
            cambios=Count('id', filter=Q(action='UPDATE')),
            bajas=Count('id', filter=Q(action='DELETE')),
        )
        .order_by('-total')
    )
    return [
        {
            'usuario': f"{f['user__first_name']} {f['user__last_name']}".strip() or f['user__username'],
            'acciones': f['total'], 'altas': f['altas'], 'cambios': f['cambios'], 'bajas': f['bajas'],
        }
        for f in filas
    ]


def calcular_datos(periodo, fecha=None):
    """Arma el JSON del resumen para `periodo` ('dia' o 'semana') que termina en `fecha`."""
    if periodo not in PERIODOS:
        raise ValueError(f'Período inválido: {periodo}')
    fecha = fecha or timezone.localdate()
    desde, hasta = rango(periodo, fecha)
    inicio, fin = _limites(desde, hasta)
    inicio_ant, fin_ant = _limites(desde - timedelta(days=7), hasta - timedelta(days=7))

    presupuestos = _presupuestos(inicio, fin, fecha)
    ventas = _ventas(inicio, fin, inicio_ant, fin_ant)
    datos = {
        'periodo': periodo,
        'desde': desde.isoformat(),
        'hasta': hasta.isoformat(),
        'presupuestos': presupuestos,
        'ventas': ventas,
        'fabrica': _fabrica(inicio, fin),
        'agenda': _agenda(desde, hasta),
        'solicitudes': _solicitudes(inicio, fin),
        'actividad': _actividad(inicio, fin),
    }
    datos['sin_actividad'] = not (
        presupuestos['creados']['cantidad'] or presupuestos['confirmados']['cantidad']
        or ventas['cantidad'] or datos['fabrica']['cambios_estado']['cantidad'] or datos['actividad']
        or datos['agenda']['programados'] or datos['solicitudes']['recibidas']
    )
    if periodo == PERIODO_SEMANA:
        datos['ranking'] = {
            'por_monto_confirmado': presupuestos['confirmados']['por_vendedor'],
            'por_presupuestos_creados': sorted(
                presupuestos['creados']['por_vendedor'], key=lambda g: g['cantidad'], reverse=True,
            ),
        }
    return datos
