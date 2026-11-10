"""Croquis de la Orden de Fabricación dibujado desde el ítem de presupuesto (REQ-068).

Solo dibuja cuando el dibujo no puede contradecir a la orden: tiene que venir de un ítem
con snapshot del cotizador, y la abertura de la orden (tipo, hojas, lado) tiene que seguir
siendo la que se precargó de ese ítem. Si no, devuelve None y el PDF deja la grilla vacía.
Las cotas salen solo si la orden tiene una única medida y es la del ítem.
"""
import base64
import re

from plantillas.services.precarga import detalle_desde_snapshot
from plantillas.utils import cortar_a_max_length
from pricing.aperturas import describir_apertura
from pricing.elevacion import computar_layout, svg_elevacion

# Caja máxima del dibujo en la hoja A4, en mm.
CAJA_ANCHO_MM = 100
CAJA_ALTO_MM = 30


def _snapshot(item):
    resultado = item.resultado_json if isinstance(item.resultado_json, dict) else {}
    if resultado.get('tipo') == 'estructura':
        return None
    snapshot = resultado.get('snapshot_item')
    if not isinstance(snapshot, dict) or not snapshot:
        return None
    snapshot = dict(snapshot)
    snapshot.setdefault('ancho_mm', item.ancho_mm)
    snapshot.setdefault('alto_mm', item.alto_mm)
    return snapshot


def _iguales(a, b):
    return (a or '').strip().casefold() == (b or '').strip().casefold()


def _abertura_cambio(orden, item, snapshot, hojas_dibujo):
    """True si la orden ya no describe la abertura del ítem (se corrigió a mano)."""
    original = ((snapshot.get('producto') or {}).get('descripcion', '') or item.descripcion or '').strip()
    if not _iguales(orden.tipo_abertura, cortar_a_max_length(type(orden), 'tipo_abertura', original)):
        return True
    precarga = detalle_desde_snapshot(snapshot)
    # Lado vacío = orden anterior a la precarga del Detalle (REQ-063), no una corrección.
    if 'lado' in precarga and (orden.lado or '').strip() and not _iguales(orden.lado, precarga['lado']):
        return True
    hojas = (orden.cantidad_hojas or '').strip()
    if hojas.isdigit() and hojas_dibujo and int(hojas) != int(hojas_dibujo):
        return True
    return False


def _medida_coincide(medidas, ancho, alto):
    if len(medidas) != 1:
        return False
    m = re.fullmatch(r'\s*(\d+)\s*[xX×]\s*(\d+)\s*', medidas[0].medida or '')
    return bool(m) and (int(m.group(1)), int(m.group(2))) == (int(ancho), int(alto))


def _texto_panos(layout):
    if layout['modo'] == 'none':
        return '1 paño fijo'
    n = layout['n_hojas']
    return f'{n} hoja{"s" if n > 1 else ""}'


def _texto_travesano(dibujo):
    secciones = dibujo.get('tirantes') or []
    if len(secciones) < 2:
        return ''
    cantidad = len(secciones) - 1
    vertical = dibujo.get('tirantes_orientacion') == 'vertical'
    sentido = 'vertical' if vertical else 'horizontal'
    plural = 'es' if cantidad > 1 else ''
    orden = 'de izq. a der.' if vertical else 'de arriba abajo'
    medidas = ' + '.join(str(s['medida_mm']) for s in secciones)
    ciegos = sum(1 for s in secciones if s.get('ciego'))
    extra = f' · {ciegos} ciego{"s" if ciegos > 1 else ""}' if ciegos else ''
    return f'{cantidad} {sentido}{plural} · secciones {orden}: {medidas} mm{extra}'


def croquis_de_orden(orden, medidas):
    """Contexto del croquis para `_orden_hoja.html`, o None si queda la grilla vacía."""
    from presupuestos.pdf_descriptions import build_dibujo_params

    item = orden.item_presupuesto
    if item is None:
        return None
    snapshot = _snapshot(item)
    if snapshot is None:
        return None
    dibujo = build_dibujo_params(snapshot)
    if not dibujo:
        return None
    layout = computar_layout(dibujo)
    if _abertura_cambio(orden, item, snapshot, layout['n_hojas']):
        return None

    con_cotas = _medida_coincide(medidas, dibujo['ancho'], dibujo['alto'])
    svg = svg_elevacion(dibujo, cotas=con_cotas, caja_mm=(CAJA_ANCHO_MM, CAJA_ALTO_MM))
    tamano = re.search(r'width="([\d.]+)mm" height="([\d.]+)mm"', svg)

    return {
        'imagen': 'data:image/svg+xml;base64,' + base64.b64encode(svg.encode('utf-8')).decode('ascii'),
        # Texto con punto: el template localizado escribiría «36,3mm» y xhtml2pdf ignora ese CSS.
        'ancho_mm': tamano.group(1),
        'alto_mm': tamano.group(2),
        'con_cotas': con_cotas,
        'apertura': describir_apertura(dibujo.get('apertura')) or 'Sin apertura cargada',
        'panos': _texto_panos(layout),
        'travesano': _texto_travesano(dibujo),
        'mosquitero': bool(dibujo.get('mosquitero')),
    }
