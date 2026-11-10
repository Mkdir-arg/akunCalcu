"""Lectura de la columna «Medida» de las órdenes de fabricación."""
import re

_PATRON = re.compile(r'\s*(\d[\d.,]*)\s*[xX×]\s*(\d[\d.,]*)\s*')


def ancho_alto(medida):
    """Parte 'ancho x alto' solo si ambos lados son números; si no, todo va en ancho."""
    texto = (medida or '').strip()
    m = _PATRON.fullmatch(texto)
    return (m.group(1), m.group(2)) if m else (texto, '')


def _a_mm(texto):
    """'1.500,5' -> 1500.5 (punto de miles, coma decimal). None si no es un número."""
    limpio = texto.replace('.', '').replace(',', '.')
    try:
        return float(limpio)
    except ValueError:
        return None


def ancho_alto_mm(medida):
    """(ancho, alto) en mm como números, o None si la medida no tiene la forma 'ancho x alto'."""
    ancho, alto = ancho_alto(medida)
    if not alto:
        return None
    ancho_mm, alto_mm = _a_mm(ancho), _a_mm(alto)
    if ancho_mm is None or alto_mm is None:
        return None
    return ancho_mm, alto_mm
