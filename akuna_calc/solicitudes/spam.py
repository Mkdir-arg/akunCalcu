"""Clasificador heurístico de spam para las solicitudes que entran por la API.

El formulario público de la web es un imán de spam (link-building, promoción en
otros idiomas, bots que prueban el form) y esos pedidos venían consumiendo un
turno del round-robin, más el mail y el WhatsApp del vendedor de turno.

Se puntúa por señales independientes y hacen falta DOS para descartar: un pedido
real con una sola rareza (un teléfono mal tipeado, un mensaje escueto) sigue
entrando normalmente. No se valida el dominio del email a propósito: hay clientes
reales que lo escriben con typos (`albacvilas@yahoo.ccom.ar`).
"""

import re
import unicodedata

UMBRAL_SPAM = 2

# Cirílico, griego, árabe, hebreo, CJK, kana, hangul y thai. Para una aberturera
# de Buenos Aires, un mensaje en estas escrituras no es un cliente.
_RE_NO_LATINO = re.compile(
    '[Ѐ-ӿͰ-Ͽ؀-ۿ֐-׿'
    '一-鿿぀-ヿ가-힯฀-๿]'
)

_RE_URL = re.compile(r'(https?://|www\.)', re.IGNORECASE)

# Raíces sin acentos: se buscan como substring sobre el mensaje normalizado.
RAICES_ABERTURAS = (
    'ventan', 'puerta', 'porton', 'abertura', 'presupuest', 'cotiz', 'vidri',
    'dvh', 'mosquiter', 'corrediz', 'banderol', 'balcon', 'mampar', 'barand',
    'celosi', 'persian', 'premarco', 'marco', 'medida', 'aluminio', 'pvc',
    'modena', 'reja', 'cerramiento', 'colocaci', 'raja', 'hoja', 'vidriera',
    'obra', 'precio', 'presupuesto', 'cambiar', 'instalar', 'cocina', 'bano',
)


def _normalizar(texto):
    """Baja a minúsculas y saca tildes, dejando intactas las escrituras no latinas."""
    descompuesto = unicodedata.normalize('NFKD', texto or '')
    return ''.join(c for c in descompuesto if not unicodedata.combining(c)).lower()


def _telefono_sospechoso(telefono):
    """True si el número no es plausible como teléfono argentino.

    Normaliza el prefijo internacional (54), el 9 de móvil y el 0 de larga
    distancia: lo que queda tiene que ser un número de 10 dígitos.
    """
    digitos = re.sub(r'\D', '', telefono or '')
    if not digitos:
        return False  # el formulario puede no traer teléfono; no es señal de spam
    if digitos.startswith('00'):
        return True
    if digitos.startswith('54'):
        digitos = digitos[2:]
        if digitos.startswith('9'):
            digitos = digitos[1:]
    if digitos.startswith('0'):
        digitos = digitos[1:]
    return len(digitos) != 10


def _email_sospechoso(email):
    """True si la parte local del email tiene el patrón de evasión de Gmail
    (Gmail ignora los puntos, así que los bots generan direcciones sembradas)."""
    local = (email or '').split('@')[0]
    if not local:
        return False
    return local.count('.') >= 4 or local.endswith('.')


def _menciona_aberturas(mensaje):
    normalizado = _normalizar(mensaje)
    return any(raiz in normalizado for raiz in RAICES_ABERTURAS)


def clasificar_spam(nombre_cliente='', email='', telefono='', mensaje=''):
    """Devuelve (es_spam, motivo) para una solicitud entrante.

    `motivo` es la lista de señales detectadas, en texto, para dejar registro en
    las notas de la solicitud y poder auditar la heurística.
    """
    senales = []

    if _RE_NO_LATINO.search(f'{nombre_cliente} {mensaje}'):
        senales.append('escritura no latina')
    if _telefono_sospechoso(telefono):
        senales.append('teléfono no plausible')
    if _RE_URL.search(mensaje or ''):
        senales.append('link en el mensaje')
    if _email_sospechoso(email):
        senales.append('email con patrón de evasión')
    if not _menciona_aberturas(mensaje):
        senales.append('sin vocabulario de aberturas')

    return len(senales) >= UMBRAL_SPAM, ', '.join(senales)
