"""Clasificación heurística de la tipología de una abertura.

A partir de la descripción libre del producto (y su cantidad de hojas) deriva un
código de tipología que consume el visor 3D del cotizador. Es una función pura
(sin acceso a base de datos) para poder testearla y reutilizarla desde el API.

Los códigos devueltos deben coincidir con las claves de ``TIPOS`` en
``static/js/viewer3d.js``.
"""

from __future__ import annotations

import unicodedata

TIPO_VENTANA_CORREDIZA = 'ventana_corrediza'
TIPO_VENTANA_BATIENTE = 'ventana_batiente'
TIPO_VENTANA_OSCILO = 'ventana_oscilo'
TIPO_VENTANA_PROYECTANTE = 'ventana_proyectante'
TIPO_PANO_FIJO = 'pano_fijo'
TIPO_PUERTA_BATIENTE = 'puerta_batiente'
TIPO_PUERTA_CORREDIZA = 'puerta_corrediza'

# Default seguro cuando no hay ninguna pista.
TIPO_DEFAULT = TIPO_PANO_FIJO


def _normalizar(texto) -> str:
    """Minúsculas y sin acentos, para matchear 'paño'->'pano', etc."""
    if not texto:
        return ''
    texto = unicodedata.normalize('NFKD', str(texto))
    texto = ''.join(c for c in texto if not unicodedata.combining(c))
    return texto.lower()


def clasificar_tipologia(descripcion, cantidad_hojas=None) -> str:
    """Devuelve el código de tipología para el visor 3D.

    Heurística por palabras clave sobre la descripción del producto. Si no hay
    match confiable, cae a un default seguro (paño fijo), usando la cantidad de
    hojas como pista (>= 2 hojas suele ser una corrediza).
    """
    desc = _normalizar(descripcion)

    es_puerta = 'puerta' in desc
    es_corrediza = any(k in desc for k in ('corrediz', 'corredera', 'scorrer', 'patio'))

    if es_puerta:
        return TIPO_PUERTA_CORREDIZA if es_corrediza else TIPO_PUERTA_BATIENTE

    if es_corrediza:
        return TIPO_VENTANA_CORREDIZA
    if 'oscilo' in desc:
        return TIPO_VENTANA_OSCILO
    if any(k in desc for k in ('proyect', 'banderola', 'toldo')):
        return TIPO_VENTANA_PROYECTANTE
    if any(k in desc for k in ('batiente', 'rebatible', 'abrir')):
        return TIPO_VENTANA_BATIENTE
    if any(k in desc for k in ('fij', 'pano')):
        return TIPO_PANO_FIJO

    # Sin match textual: pista por cantidad de hojas.
    try:
        n = int(cantidad_hojas) if cantidad_hojas is not None else 0
    except (TypeError, ValueError):
        n = 0
    if n >= 2:
        return TIPO_VENTANA_CORREDIZA
    return TIPO_DEFAULT
