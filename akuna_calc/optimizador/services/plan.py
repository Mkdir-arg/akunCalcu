"""Armado del plan de corte de perfiles de marco (REQ-070)."""
import hashlib
import json
import math
from collections import OrderedDict, defaultdict

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.urls import NoReverseMatch, reverse

from plantillas.models import OrdenFabricacion
from plantillas.services import circuito
from plantillas.services.abertura_catalogo import seleccion_inicial
from ..models import PlanCorte
from .despiece import MotivoExclusion, color_de, tramos_de_orden
from .empaque import acomodar

ESTADOS_PEDIDO = ('en_fabrica', 'en_produccion')
ETAPAS_CANDIDATAS = ('por_fabricar', 'corte')
DISCO_POR_DEFECTO = 4
DESPUNTE_POR_DEFECTO = 10
CLASES_PEDIDO = 3
INTENTOS_NUMERO = 3


def _n(valor):
    """Entero si no tiene decimales (el JSON queda corto y el HTML sin '.0')."""
    valor = round(float(valor), 1)
    return int(valor) if valor == int(valor) else valor


def ordenes_candidatas():
    return (
        OrdenFabricacion.objects
        .filter(pedido__estado__in=ESTADOS_PEDIDO, etapa__in=ETAPAS_CANDIDATAS)
        .select_related('pedido', 'item_presupuesto')
        .prefetch_related('medidas')
        .order_by('pedido__numero', 'numero')
    )


def firma_de_ordenes(ordenes):
    """Hash de lo que condiciona el cálculo: medidas, marco y color de cada orden."""
    partes = []
    for orden in sorted(ordenes, key=lambda o: o.pk):
        medidas = [[(m.medida or '').strip(), m.cantidad] for m in orden.medidas.all() if (m.medida or '').strip()]
        partes.append([orden.pk, medidas, seleccion_inicial(orden).get('marco'), (orden.color or '').strip().upper()])
    return hashlib.sha1(json.dumps(partes, sort_keys=True).encode('utf-8')).hexdigest()


def _evaluar_orden(orden, largo_forzado):
    """(tramos, motivo): suma a los motivos de despiece el perfil sin largo de barra."""
    tramos, motivo = tramos_de_orden(orden)
    if motivo is None and not largo_forzado:
        for tramo in tramos:
            if not tramo['long_tira']:
                motivo = MotivoExclusion(
                    f'El perfil {tramo["codigo"]} no tiene largo de barra', 'Completar perfil', 'perfil', tramo['codigo'],
                )
                break
    return (tramos, motivo) if motivo is None else ([], motivo)


def _url_motivo(orden, motivo):
    try:
        if motivo.destino == 'marco':
            return reverse('config-marco-edit', args=[motivo.ref])
        if motivo.destino == 'perfil':
            return reverse('config-perfil-edit', args=[motivo.ref])
        return reverse('plantillas:orden_edit', args=[orden.pk])
    except NoReverseMatch:
        return reverse('plantillas:orden_edit', args=[orden.pk])


def resumen_pedidos(largo_forzado=None):
    """Para la pantalla «Nuevo plan»: por pedido, órdenes que entran / total y cortes."""
    pedidos = OrderedDict()
    for orden in ordenes_candidatas():
        fila = pedidos.setdefault(orden.pedido_id, {
            'pedido': orden.pedido, 'total': 0, 'entran': 0, 'cortes': 0,
            'fecha': None,
        })
        fila['total'] += 1
        tramos, motivo = _evaluar_orden(orden, largo_forzado)
        if motivo is None:
            fila['entran'] += 1
            fila['cortes'] += sum(t['cantidad'] for t in tramos)
        if orden.fecha_comprometida and (fila['fecha'] is None or orden.fecha_comprometida < fila['fecha']):
            fila['fecha'] = orden.fecha_comprometida
    filas = list(pedidos.values())
    for fila in filas:
        fila['etiqueta'] = f'{fila["entran"]} de {fila["total"]}'
        fila['tono'] = 'green' if fila['entran'] == fila['total'] else ('amber' if fila['entran'] else 'red')
    return filas


def _lista_por_largo(piezas):
    por_largo = OrderedDict()
    for pieza in sorted(piezas, key=lambda p: (-p['largo_mm'], p['orden'])):
        fila = por_largo.setdefault(pieza['largo_mm'], {'largo': pieza['largo_mm'], 'cantidad': 0, 'angulos': set(), 'ordenes': OrderedDict()})
        fila['cantidad'] += 1
        if pieza['angulo']:
            fila['angulos'].add(pieza['angulo'])
        fila['ordenes'][pieza['orden']] = fila['ordenes'].get(pieza['orden'], 0) + 1
    return [{
        'largo': f['largo'],
        'cantidad': f['cantidad'],
        'angulo': ' / '.join(sorted(f['angulos'])),
        'ordenes': ' · '.join(f'{numero} ×{cantidad}' for numero, cantidad in f['ordenes'].items()),
    } for f in por_largo.values()]


def _grupo(codigo, color, tramos, params, cls_pedido):
    largo_barra = params['largo_barra_mm'] or tramos[0]['long_tira']
    disco, despunte = params['disco_mm'], params['despunte_mm']
    recorte_min = params['recorte_min_mm'] or tramos[0]['minimo']
    piezas = [dict(t) for t in tramos]
    barras, no_entran = acomodar(piezas, largo_barra, disco, despunte)

    salida = []
    guardados = []
    for i, barra in enumerate(barras, start=1):
        sobrante = barra['sobrante']
        guarda = bool(recorte_min) and sobrante >= recorte_min
        if guarda:
            guardados.append(_n(sobrante))
        salida.append({
            'n': i,
            'piezas': [{
                'largo': p['largo_mm'], 'orden': p['orden'], 'pedido': p['pedido'], 'cls': cls_pedido[p['pedido_id']],
                'angulo': p['angulo'], 'ancho_pct': round((p['largo_mm'] + disco) / largo_barra * 100, 3),
                'corta': (p['largo_mm'] + disco) / largo_barra * 100 < 7,
            } for p in barra['piezas']],
            'despunte_pct': round(despunte / largo_barra * 100, 3),
            'sobrante': _n(sobrante),
            'guarda': guarda,
        })

    cortado = sum(p['largo_mm'] for b in barras for p in b['piezas'])
    consumo = sum(p['largo_mm'] + disco for b in barras for p in b['piezas'])
    en_barras = len(barras) * largo_barra
    minimo = math.ceil(consumo / (largo_barra - despunte)) if barras else 0
    desperdicio = en_barras - cortado - sum(guardados)
    primero = tramos[0]
    return {
        'codigo': codigo,
        'descripcion': primero['descripcion'],
        'color': color,
        'largo_barra': _n(largo_barra),
        'recorte_min': _n(recorte_min) if recorte_min else None,
        'barras': salida,
        'n_barras': len(barras),
        'minimo_teorico': minimo,
        'es_minimo': bool(barras) and len(barras) == minimo,
        'n_cortes': sum(len(b['piezas']) for b in barras),
        'cortado_mm': _n(cortado),
        'en_barras_mm': _n(en_barras),
        'desperdicio_mm': _n(desperdicio),
        'desperdicio_pct': round(desperdicio / en_barras * 100, 1) if en_barras else 0,
        'recortes': guardados,
        'lista': _lista_por_largo([p for b in barras for p in b['piezas']]),
        'no_entran': [{'largo': p['largo_mm'], 'orden': p['orden'], 'pedido': p['pedido']} for p in no_entran],
    }


def _cortes_por_orden(tramos_por_orden):
    detalle = {}
    for orden_id, tramos in tramos_por_orden.items():
        por_perfil = OrderedDict()
        for t in tramos:
            por_perfil.setdefault(t['codigo'], OrderedDict())
            largos = por_perfil[t['codigo']]
            largos[t['largo_mm']] = largos.get(t['largo_mm'], 0) + t['cantidad']
        detalle[orden_id] = [
            {'codigo': codigo, 'texto': ' · '.join(f'{largo} ×{cant}' for largo, cant in largos.items())}
            for codigo, largos in por_perfil.items()
        ]
    return detalle


def _calcular(pedidos, params):
    pedidos = sorted(pedidos, key=lambda p: p.numero)
    cls_pedido = {p.pk: f'p{(i % CLASES_PEDIDO) + 1}' for i, p in enumerate(pedidos)}
    largo_forzado = params['largo_barra_mm']

    incluidas, excluidas, tramos_por_orden = [], [], OrderedDict()
    ordenes = [o for o in ordenes_candidatas() if o.pedido_id in cls_pedido]
    for orden in ordenes:
        tramos, motivo = _evaluar_orden(orden, largo_forzado)
        if motivo is not None:
            excluidas.append({
                'orden': orden.numero_formateado, 'orden_id': orden.pk, 'pedido': orden.pedido.numero,
                'motivo': motivo.texto, 'accion': motivo.accion, 'url': _url_motivo(orden, motivo),
            })
            continue
        incluidas.append(orden)
        tramos_por_orden[orden.pk] = tramos

    por_grupo = OrderedDict()
    for tramos in tramos_por_orden.values():
        for t in tramos:
            for _ in range(t['cantidad']):
                por_grupo.setdefault((t['codigo'], t['color']), []).append(t)
    grupos = [_grupo(codigo, color, piezas, params, cls_pedido) for (codigo, color), piezas in sorted(por_grupo.items())]

    cortes = _cortes_por_orden(tramos_por_orden)
    cantidad_por_pedido = defaultdict(int)
    for orden in incluidas:
        cantidad_por_pedido[orden.pedido_id] += 1
    en_barras = sum(g['en_barras_mm'] for g in grupos)
    desperdicio = sum(g['desperdicio_mm'] for g in grupos)
    resultado = {
        'params': {k: (_n(v) if v is not None else None) for k, v in params.items()},
        'pedidos': [{
            'id': p.pk, 'numero': p.numero, 'cliente': p.cliente, 'cls': cls_pedido[p.pk],
            'ordenes': cantidad_por_pedido.get(p.pk, 0),
        } for p in pedidos],
        'n_ordenes': len(incluidas),
        'grupos': grupos,
        'excluidas': excluidas,
        'ordenes': [{
            'numero': o.numero_formateado, 'pedido': o.pedido.numero, 'cliente': o.pedido.cliente,
            'medida': ' | '.join((m.medida or '').strip() for m in o.medidas.all() if (m.medida or '').strip()),
            'cantidad': sum(m.cantidad for m in o.medidas.all() if (m.medida or '').strip()),
            'cortes': cortes[o.pk],
        } for o in incluidas],
        'totales': {
            'barras': sum(g['n_barras'] for g in grupos),
            'cortes': sum(g['n_cortes'] for g in grupos),
            'cortado_m': round(sum(g['cortado_mm'] for g in grupos) / 1000, 1),
            'en_barras_m': round(en_barras / 1000, 1),
            'desperdicio_m': round(desperdicio / 1000, 2),
            'desperdicio_pct': round(desperdicio / en_barras * 100, 1) if en_barras else 0,
            'recortes': sorted((r for g in grupos for r in g['recortes']), reverse=True),
            'es_minimo': bool(grupos) and all(g['es_minimo'] for g in grupos),
            'no_entran': sum(len(g['no_entran']) for g in grupos),
        },
    }
    return resultado, incluidas


def normalizar_params(disco_mm=DISCO_POR_DEFECTO, despunte_mm=DESPUNTE_POR_DEFECTO, largo_barra_mm=None, recorte_min_mm=None):
    return {
        'disco_mm': float(disco_mm), 'despunte_mm': float(despunte_mm),
        'largo_barra_mm': int(largo_barra_mm) if largo_barra_mm else None,
        'recorte_min_mm': int(recorte_min_mm) if recorte_min_mm else None,
    }


def calcular(pedidos, params):
    """Resultado serializable del plan para los pedidos elegidos (no guarda nada)."""
    return _calcular(pedidos, params)[0]


def guardar(pedidos, params, usuario, pasar_a_corte=True):
    """Recalcula, guarda el plan y (opcional) pasa a Corte las órdenes incluidas que están por fabricar."""
    with transaction.atomic():
        resultado, incluidas = _calcular(pedidos, params)
        if not incluidas or not resultado['grupos']:
            raise ValidationError('No hay órdenes para cortar: ninguna de las elegidas se puede calcular.')
        plan = None
        for intento in range(INTENTOS_NUMERO):
            try:
                with transaction.atomic():
                    plan = PlanCorte.objects.create(
                        numero=PlanCorte.generar_numero(), usuario=usuario, disco_mm=params['disco_mm'],
                        despunte_mm=params['despunte_mm'], largo_barra_mm=params['largo_barra_mm'],
                        recorte_min_mm=params['recorte_min_mm'], resultado=resultado, firma=firma_de_ordenes(incluidas),
                    )
                break
            except IntegrityError:
                if intento == INTENTOS_NUMERO - 1:
                    raise
        plan.pedidos.set(pedidos)
        plan.ordenes.set(incluidas)
        if pasar_a_corte:
            for orden in incluidas:
                if orden.etapa == 'por_fabricar':
                    circuito.cambiar_etapa(orden, usuario, 'corte', nota=f'Plan de corte {plan.numero_formateado}')
        return plan
