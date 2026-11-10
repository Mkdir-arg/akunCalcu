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

# Caja del dibujo en la hoja A4, en mm. El alto se adapta a lo que deja libre el resto de la
# hoja (ver `alto_disponible`), entre el mínimo y el máximo.
CAJA_ANCHO_MM = 110
CAJA_ALTO_MIN_MM = 20
CAJA_ALTO_MAX_MM = 70

# Medido renderizando la hoja con xhtml2pdf (REQ-068): sin revisión, nota ni características
# el dibujo puede llegar a 103 mm; cada bloque opcional resta lo suyo. Margen de 6 mm.
_ALTO_LIBRE_MM = 103 - 6
_REVISION_MM = 17
_NOTA_MM, _NOTA_RENGLON_MM, _NOTA_CHARS = 12, 5.5, 95
_CARACT_MM, _CARACT_FILA_MM = 10, 7
_MEDIDA_EXTRA_MM = 11
_TIPO_RENGLON_MM, _TIPO_CHARS = 7, 22


def _renglones(texto, ancho):
    lineas = (texto or '').strip().splitlines()
    return sum(max(1, -(-len(linea) // ancho)) for linea in lineas)


def alto_disponible(orden, n_medidas, n_caracteristicas):
    """Alto en mm que puede ocupar el dibujo sin que la hoja pase a una segunda página."""
    alto = _ALTO_LIBRE_MM
    if (orden.revision or 0) > 1:
        alto -= _REVISION_MM
    texto_nota = '\n'.join(t for t in (orden.nota, orden.estructura) if (t or '').strip())
    if texto_nota:
        alto -= _NOTA_MM + _NOTA_RENGLON_MM * (_renglones(texto_nota, _NOTA_CHARS) - 1)
    if n_caracteristicas:
        alto -= _CARACT_MM + _CARACT_FILA_MM * n_caracteristicas
    alto -= _MEDIDA_EXTRA_MM * max(n_medidas - 1, 0)
    alto -= _TIPO_RENGLON_MM * max(_renglones(orden.tipo_abertura or '—', _TIPO_CHARS) - 1, 0)
    if alto < 30:
        # En hojas muy cargadas la estimación se queda corta por 1-2 mm: se resta más.
        alto -= 2
    return max(CAJA_ALTO_MIN_MM, min(CAJA_ALTO_MAX_MM, alto))


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


def croquis_de_orden(orden, medidas, alto_mm=None):
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
    svg = svg_elevacion(dibujo, cotas=con_cotas, caja_mm=(CAJA_ANCHO_MM, alto_mm or 30))
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
