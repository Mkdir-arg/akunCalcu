"""Elevación 2D de una abertura en SVG, del lado del servidor (REQ-068).

Es el espejo en Python de `static/js/abertura-layout.js` (`computarLayout`) y
`static/js/elevacion.js` (`svgElevacion`): mismos paños, secciones por tirantes,
símbolos de apertura y colores. Existe porque el PDF de la Orden de Fabricación
lo arma xhtml2pdf, que no ejecuta JavaScript; el SVG lo rasteriza svglib (viene
con xhtml2pdf). Si cambia el dibujo de un lado, cambiarlo del otro (ADR-028).

Diferencias con el JS, por svglib: sin `dominant-baseline` (el texto se centra a
mano), mosquitero con rayas sueltas en vez de `<pattern>`, y cotas de las
secciones de tirantes, que el taller necesita para ubicar los travesaños.

Origen: esquina superior izquierda del marco, `y` hacia abajo. Izquierda y
derecha son de la abertura vista de frente, igual que en el cotizador.
"""
from html import escape
from typing import Any, Dict, List, Optional

from .aperturas import APERTURA_POR_CODIGO, _hoja_default, normalizar_apertura

TIPOS_LAYOUT = {
    'ventana_corrediza':   {'hojas': [2, 3, 4, 6], 'modo': 'slide',   'puerta': False},
    'ventana_batiente':    {'hojas': [1, 2],       'modo': 'swing',   'puerta': False},
    'ventana_oscilo':      {'hojas': [1],          'modo': 'tilt',    'puerta': False},
    'ventana_proyectante': {'hojas': [1],          'modo': 'project', 'puerta': False},
    'pano_fijo':           {'hojas': [1],          'modo': 'none',    'puerta': False},
    'puerta_batiente':     {'hojas': [1, 2],       'modo': 'swing',   'puerta': True},
    'puerta_corrediza':    {'hojas': [2, 3],       'modo': 'slide',   'puerta': True},
}

PERFIL_COLORES = {
    'blanco': '#f3f4f4', 'negro': '#1b1d1f', 'antracita': '#373b3f',
    'bronce': '#54422e', 'madera': '#6a4526', 'aluminio': '#bfc3c8',
}

COLOR = {
    'cota': '#1560a8',
    'contorno': '#111418',
    'simbolo': '#334155',
    'vidrio': '#dbe6ee',
    'ciego': '#9aa3ab',
    'malla': '#1d4ed8',
    'texto': '#111418',
}
FUENTE = 'Helvetica'


def map_color(descripcion: Any) -> str:
    d = str(descripcion or '').lower()
    if 'negro' in d or 'negra' in d:
        return 'negro'
    if 'bronce' in d:
        return 'bronce'
    if any(p in d for p in ('antracita', 'grafito', 'gris')):
        return 'antracita'
    if any(p in d for p in ('madera', 'roble', 'cedro', 'nogal', 'simil')):
        return 'madera'
    if any(p in d for p in ('anod', 'natural', 'aluminio', 'plata', 'crudo')):
        return 'aluminio'
    return 'blanco'


def _entero(valor: Any) -> int:
    try:
        return int(float(valor))
    except (TypeError, ValueError):
        return 0


def _repartir_secciones(secciones: List[Dict[str, Any]], total: float) -> Optional[List[Dict[str, Any]]]:
    suma = sum(_entero(s.get('medida_mm')) for s in secciones)
    if suma <= 0:
        return None
    cursor = 0.0
    salida = []
    for s in secciones:
        largo = _entero(s.get('medida_mm')) / suma * total
        salida.append({'desde': cursor, 'largo': largo, 'ciego': bool(s.get('ciego')),
                       'medida_mm': _entero(s.get('medida_mm'))})
        cursor += largo
    return salida


def computar_layout(p: Dict[str, Any]) -> Dict[str, Any]:
    """Espejo de `computarLayout` (abertura-layout.js)."""
    tipo = p.get('tipo') if p.get('tipo') in TIPOS_LAYOUT else 'pano_fijo'
    t = TIPOS_LAYOUT[tipo]
    W = max(_entero(p.get('ancho')), 1)
    H = max(_entero(p.get('alto')), 1)
    pw = 60 if t['puerta'] else 55
    lf = 55 if t['puerta'] else 40
    n_hojas = _entero(p.get('hojas'))
    n_hojas = n_hojas if n_hojas in t['hojas'] else t['hojas'][0]
    hueco = {'x': pw, 'y': pw, 'w': max(W - 2 * pw, 1), 'h': max(H - 2 * pw, 1)}

    if t['modo'] == 'none':
        panos = [{'x': hueco['x'], 'y': hueco['y'], 'w': hueco['w'], 'h': hueco['h'], 'indice': 0}]
    else:
        col = hueco['w'] / n_hojas
        panos = [{'x': hueco['x'] + col * i, 'y': hueco['y'], 'w': col, 'h': hueco['h'], 'indice': i}
                 for i in range(n_hojas)]

    apertura = normalizar_apertura(p.get('apertura'), n_hojas)
    definicion = APERTURA_POR_CODIGO.get(apertura['codigo']) if apertura else None
    for i, pano in enumerate(panos):
        pano.update(simbolo=None, bisagra=None, movimiento=None, carril=None)
        if not definicion:
            continue
        simbolo = definicion['simbolo']
        if simbolo == 'flechas':
            hojas = apertura.get('hojas') or []
            h = hojas[i] if i < len(hojas) else _hoja_default(i, n_hojas)
            pano.update(simbolo='flechas', movimiento=h['movimiento'], carril=h['carril'])
        elif simbolo == 'lateral':
            pano.update(simbolo='lateral', bisagra=apertura.get('lado') or 'izq')
        elif simbolo == 'lateral_doble':
            pano.update(simbolo='lateral', bisagra='izq' if i == 0 else 'der')
        elif simbolo == 'oscilo':
            pano.update(simbolo='oscilo', bisagra=apertura.get('lado') or 'izq')
        elif simbolo in ('vertice_arriba', 'vertice_abajo', 'rombo'):
            pano['simbolo'] = simbolo

    tirantes = p.get('tirantes') if isinstance(p.get('tirantes'), list) and len(p['tirantes']) >= 2 else None
    vertical = p.get('tirantes_orientacion') == 'vertical'
    for pano in panos:
        inset = 0 if t['modo'] == 'none' else lf
        vidrio = {'x': pano['x'] + inset, 'y': pano['y'] + inset,
                  'w': max(pano['w'] - 2 * inset, 1), 'h': max(pano['h'] - 2 * inset, 1)}
        pano['vidrio'] = vidrio
        pano['secciones'] = None
        if tirantes:
            reparto = _repartir_secciones(tirantes, vidrio['w'] if vertical else vidrio['h'])
            if reparto:
                pano['secciones'] = [{
                    **r,
                    'x': vidrio['x'] + r['desde'] if vertical else vidrio['x'],
                    'y': vidrio['y'] if vertical else vidrio['y'] + r['desde'],
                    'w': r['largo'] if vertical else vidrio['w'],
                    'h': vidrio['h'] if vertical else r['largo'],
                } for r in reparto]

    mosquitero = None
    if p.get('mosquitero') and panos:
        u = panos[-1]
        a = max(60, min(u['w'] * 0.42, u['w']))
        mosquitero = {'x': u['x'] + u['w'] - a, 'y': u['y'], 'w': a, 'h': u['h']}

    anchos = []
    if len(panos) > 1:
        bordes = [0] + [x['x'] for x in panos[1:]] + [W]
        anchos = [{'desde': bordes[i], 'hasta': bordes[i + 1], 'valor': round(bordes[i + 1] - bordes[i])}
                  for i in range(len(bordes) - 1)]
        anchos[-1]['valor'] = W - sum(s['valor'] for s in anchos[:-1])

    color = p.get('color') if p.get('color') in PERFIL_COLORES else map_color(p.get('color_terminacion'))
    return {
        'tipo': tipo, 'modo': t['modo'], 'ancho_mm': W, 'alto_mm': H, 'pw': pw, 'lf': lf,
        'n_hojas': n_hojas, 'panos': panos, 'mosquitero': mosquitero,
        'cotas': {'alto': H, 'ancho_total': W, 'anchos': anchos,
                  'secciones': [_entero(s.get('medida_mm')) for s in tirantes] if tirantes else [],
                  'secciones_vertical': vertical},
        'apertura': apertura, 'color_perfil': PERFIL_COLORES[color],
    }


def _n(v: float) -> str:
    return f'{v:.1f}'.rstrip('0').rstrip('.')


def _linea(x1, y1, x2, y2, stroke, sw) -> str:
    return (f'<line x1="{_n(x1)}" y1="{_n(y1)}" x2="{_n(x2)}" y2="{_n(y2)}" '
            f'stroke="{stroke}" stroke-width="{_n(sw)}"/>')


def _rect(x, y, w, h, fill, stroke=None, sw=0) -> str:
    borde = f' stroke="{stroke}" stroke-width="{_n(sw)}"' if stroke else ''
    return f'<rect x="{_n(x)}" y="{_n(y)}" width="{_n(max(w, 1))}" height="{_n(max(h, 1))}" fill="{fill}"{borde}/>'


def _texto(x, y, valor, size, color, rotar=False, negrita=False) -> str:
    # svglib ignora dominant-baseline: se baja la línea de base ~1/3 del cuerpo.
    base = y + size * 0.35
    peso = ' font-weight="bold"' if negrita else ''
    giro = f' transform="rotate(-90 {_n(x)} {_n(y)})"' if rotar else ''
    return (f'<text x="{_n(x)}" y="{_n(base)}" fill="{color}" font-size="{_n(size)}" font-family="{FUENTE}"'
            f'{peso} text-anchor="middle"{giro}>{escape(str(valor))}</text>')


def _perfil(x, y, w, h, grosor, fill, size) -> str:
    fino = size * 0.1
    return (_rect(x + grosor / 2, y + grosor / 2, w - grosor, h - grosor, 'none', fill, grosor)
            + _rect(x, y, w, h, 'none', COLOR['contorno'], fino)
            + _rect(x + grosor, y + grosor, w - 2 * grosor, h - 2 * grosor, 'none', COLOR['contorno'], fino))


def _cota_h(x1, x2, y, valor, size) -> str:
    if x2 - x1 <= 0:
        return ''
    t, sw = size * 0.9, size * 0.09
    return (_linea(x1, y, x2, y, COLOR['cota'], sw) + _linea(x1, y - t, x1, y + t, COLOR['cota'], sw)
            + _linea(x2, y - t, x2, y + t, COLOR['cota'], sw)
            + _texto((x1 + x2) / 2, y - t * 2.8, valor, size * 4.2, COLOR['cota']))


def _cota_v(y1, y2, x, valor, size) -> str:
    if y2 - y1 <= 0:
        return ''
    t, sw = size * 0.9, size * 0.09
    return (_linea(x, y1, x, y2, COLOR['cota'], sw) + _linea(x - t, y1, x + t, y1, COLOR['cota'], sw)
            + _linea(x - t, y2, x + t, y2, COLOR['cota'], sw)
            + _texto(x - t * 2.8, (y1 + y2) / 2, valor, size * 4.2, COLOR['cota'], rotar=True))


def _flecha(cx, cy, direccion, largo, size) -> str:
    h, mitad = size * 1.6, largo / 2
    x1, x2 = cx - mitad, cx + mitad
    px, s = (x2, -1) if direccion == 'der' else (x1, 1)
    punta = f'{_n(px)},{_n(cy)} {_n(px + s * h)},{_n(cy - h * 0.62)} {_n(px + s * h)},{_n(cy + h * 0.62)}'
    return _linea(x1, cy, x2, cy, COLOR['cota'], size * 0.2) + f'<polygon points="{punta}" fill="{COLOR["cota"]}"/>'


def _simbolo(pano, v, size) -> str:
    sw, c = size * 0.16, COLOR['simbolo']
    L, R, T, B = v['x'], v['x'] + v['w'], v['y'], v['y'] + v['h']
    mid_x, mid_y = L + v['w'] / 2, T + v['h'] / 2

    def lateral(bisagra):
        if bisagra == 'der':
            return _linea(R, T, L, mid_y, c, sw) + _linea(R, B, L, mid_y, c, sw)
        return _linea(L, T, R, mid_y, c, sw) + _linea(L, B, R, mid_y, c, sw)

    def vertice_arriba():
        return _linea(L, B, mid_x, T, c, sw) + _linea(R, B, mid_x, T, c, sw)

    simbolo = pano['simbolo']
    if simbolo == 'lateral':
        return lateral(pano['bisagra'])
    if simbolo == 'oscilo':
        return lateral(pano['bisagra']) + vertice_arriba()
    if simbolo == 'vertice_arriba':
        return vertice_arriba()
    if simbolo == 'vertice_abajo':
        return _linea(L, T, mid_x, B, c, sw) + _linea(R, T, mid_x, B, c, sw)
    if simbolo == 'rombo':
        return (_linea(mid_x, T, R, mid_y, c, sw) + _linea(R, mid_y, mid_x, B, c, sw)
                + _linea(mid_x, B, L, mid_y, c, sw) + _linea(L, mid_y, mid_x, T, c, sw))
    if simbolo == 'flechas':
        direccion = 'der' if pano['movimiento'] == 'der' else 'izq'
        etiqueta = 'Ext.' if pano['carril'] == 'ext' else 'Int.'
        return (_flecha(mid_x, T + v['h'] * 0.42, direccion, min(v['w'] * 0.42, 420), size)
                + _texto(mid_x, T + v['h'] * 0.58, etiqueta, size * 2.8, COLOR['cota'], negrita=True))
    return ''


def _partes(L: Dict[str, Any], ox: float, oy: float, size: float) -> List[str]:
    partes = [_perfil(ox, oy, L['ancho_mm'], L['alto_mm'], L['pw'], L['color_perfil'], size)]
    for pano in L['panos']:
        v = {k: pano['vidrio'][k] + (ox if k == 'x' else oy if k == 'y' else 0) for k in pano['vidrio']}
        if pano['secciones']:
            for s in pano['secciones']:
                partes.append(_rect(ox + s['x'], oy + s['y'], s['w'], s['h'],
                                    COLOR['ciego'] if s['ciego'] else COLOR['vidrio'], COLOR['contorno'], size * 0.12))
        else:
            partes.append(_rect(v['x'], v['y'], v['w'], v['h'], COLOR['vidrio'], COLOR['contorno'], size * 0.08))
        if L['modo'] == 'none':
            partes.append(_texto(v['x'] + v['w'] / 2, v['y'] + v['h'] / 2, 'FIJO', size * 3, COLOR['cota'], negrita=True))
        else:
            partes.append(_perfil(ox + pano['x'], oy + pano['y'], pano['w'], pano['h'], L['lf'], L['color_perfil'], size))
        if pano['simbolo']:
            partes.append(_simbolo(pano, v, size))

    m = L['mosquitero']
    if m:
        paso = max(size * 0.9, 14)
        x = ox + m['x'] + paso
        while x < ox + m['x'] + m['w']:
            partes.append(_linea(x, oy + m['y'], x, oy + m['y'] + m['h'], COLOR['malla'], size * 0.12))
            x += paso
        partes.append(_rect(ox + m['x'], oy + m['y'], m['w'], m['h'], 'none', COLOR['contorno'], size * 0.1))
    return partes


def svg_elevacion(params: Dict[str, Any], cotas: bool = True, caja_mm: Optional[tuple] = None) -> str:
    """Espejo de `svgElevacion` (elevacion.js). Devuelve un `<svg>` completo con `xmlns`.

    `caja_mm=(ancho, alto)` fija el tamaño impreso en mm dentro de esa caja, manteniendo la
    proporción: xhtml2pdf toma el tamaño del propio SVG e ignora el CSS del `<img>`.
    """
    L = computar_layout(params or {})
    W, H = L['ancho_mm'], L['alto_mm']
    size = max(W, H) / 52
    secciones = L['cotas']['secciones']
    sec_h = bool(secciones) and not L['cotas']['secciones_vertical']
    sec_v = bool(secciones) and L['cotas']['secciones_vertical']

    m_izq = size * 8.5 if cotas else size
    m_der = size * 8 if cotas and sec_h else size
    m_arriba = size * 7.5 if cotas and sec_v else size
    m_abajo = size * (13.5 if L['cotas']['anchos'] else 8) if cotas else size
    ox, oy = m_izq, m_arriba
    partes = _partes(L, ox, oy, size)

    if cotas:
        partes.append(_cota_v(oy, oy + H, ox - size * 3.2, L['cotas']['alto'], size))
        y1 = oy + H + size * 5.6
        for c in L['cotas']['anchos']:
            partes.append(_cota_h(ox + c['desde'], ox + c['hasta'], y1, c['valor'], size))
        y2 = y1 + size * 5.8 if L['cotas']['anchos'] else y1
        partes.append(_cota_h(ox, ox + W, y2, L['cotas']['ancho_total'], size))
        # Secciones de tirantes: sobre el vidrio del primer paño, que es donde se reparten.
        reparto = L['panos'][0]['secciones'] or []
        for s in reparto:
            if sec_h:
                partes.append(_cota_v(oy + s['y'], oy + s['y'] + s['h'], ox + W + size * 5.6, s['medida_mm'], size))
            else:
                partes.append(_cota_h(ox + s['x'], ox + s['x'] + s['w'], oy - size * 1.2, s['medida_mm'], size))

    vb_w, vb_h = W + m_izq + m_der, H + m_arriba + m_abajo
    if caja_mm:
        escala = min(caja_mm[0] / vb_w, caja_mm[1] / vb_h)
        ancho, alto = f'{vb_w * escala:.1f}mm', f'{vb_h * escala:.1f}mm'
    else:
        ancho, alto = _n(vb_w), _n(vb_h)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {_n(vb_w)} {_n(vb_h)}" '
            f'width="{ancho}" height="{alto}">{"".join(partes)}</svg>')
