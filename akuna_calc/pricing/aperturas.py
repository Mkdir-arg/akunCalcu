"""Catálogo de aperturas (REQ-047).

Una *apertura* dice cómo abre la abertura: corrediza, paño de abrir, banderola,
etc., con el lado de la bisagra o el movimiento de cada hoja cuando corresponde.
Es distinta de la *familia* (`Producto.tipo_dibujo` / `pricing.tipologia`), que
define la malla 3D: banderola, brazo de empuje y proyectante con tijera comparten
familia pero tienen símbolos técnicos distintos.

Vive en código, no en la base: son símbolos fijos de carpintería. El espejo para
el dibujo está en `static/js/abertura-layout.js` (misma lista, mismos códigos).

Convención única del sistema: **izquierda y derecha son de la abertura vista de
frente, tal como se dibuja.** "Int./Ext." es otro eje (carril de una corrediza).
"""
from typing import Any, Dict, Iterable, List, Optional

LADOS = ('izq', 'der')
MOVIMIENTOS = ('izq', 'der')
CARRILES = ('int', 'ext')

# simbolo: ninguno | flechas | lateral | lateral_doble | oscilo | vertice_arriba
#          | vertice_abajo | rombo
# lado:     pide lado de bisagra (izq/der)
# por_hoja: pide movimiento y carril por hoja (corredizas)
# familias: tipologías (pricing.tipologia) con las que es compatible
APERTURAS: List[Dict[str, Any]] = [
    {'codigo': 'pano_fijo', 'nombre': 'Paño fijo', 'simbolo': 'ninguno',
     'hojas': [1], 'lado': False, 'por_hoja': False, 'familias': ['pano_fijo']},
    {'codigo': 'corrediza', 'nombre': 'Corrediza', 'simbolo': 'flechas',
     'hojas': [2, 3, 4, 6], 'lado': False, 'por_hoja': True, 'familias': ['ventana_corrediza']},
    {'codigo': 'abrir_1', 'nombre': 'Paño de abrir 1 hoja', 'simbolo': 'lateral',
     'hojas': [1], 'lado': True, 'por_hoja': False, 'familias': ['ventana_batiente']},
    {'codigo': 'abrir_2', 'nombre': 'Paño de abrir 2 hojas', 'simbolo': 'lateral_doble',
     'hojas': [2], 'lado': False, 'por_hoja': False, 'familias': ['ventana_batiente']},
    {'codigo': 'oscilobatiente', 'nombre': 'Oscilobatiente', 'simbolo': 'oscilo',
     'hojas': [1], 'lado': True, 'por_hoja': False, 'familias': ['ventana_oscilo', 'ventana_batiente']},
    {'codigo': 'banderola', 'nombre': 'Banderola', 'simbolo': 'vertice_arriba',
     'hojas': [1], 'lado': False, 'por_hoja': False, 'familias': ['ventana_proyectante']},
    {'codigo': 'brazo_empuje', 'nombre': 'Brazo de empuje', 'simbolo': 'vertice_abajo',
     'hojas': [1], 'lado': False, 'por_hoja': False, 'familias': ['ventana_proyectante']},
    {'codigo': 'proyectante_tijera', 'nombre': 'Proyectante con tijera', 'simbolo': 'rombo',
     'hojas': [1], 'lado': False, 'por_hoja': False, 'familias': ['ventana_proyectante']},
    {'codigo': 'puerta', 'nombre': 'Puerta 1 hoja', 'simbolo': 'lateral',
     'hojas': [1], 'lado': True, 'por_hoja': False, 'familias': ['puerta_batiente']},
    {'codigo': 'puerta_doble', 'nombre': 'Puerta 2 hojas', 'simbolo': 'lateral_doble',
     'hojas': [2], 'lado': False, 'por_hoja': False, 'familias': ['puerta_batiente']},
    {'codigo': 'puerta_corrediza', 'nombre': 'Puerta corrediza', 'simbolo': 'flechas',
     'hojas': [2, 3], 'lado': False, 'por_hoja': True, 'familias': ['puerta_corrediza']},
]

APERTURA_POR_CODIGO: Dict[str, Dict[str, Any]] = {a['codigo']: a for a in APERTURAS}
APERTURA_CHOICES = [(a['codigo'], a['nombre']) for a in APERTURAS]


def aperturas_compatibles(tipologia: Optional[str]) -> List[Dict[str, Any]]:
    """Aperturas cuya familia coincide con la tipología del producto."""
    return [a for a in APERTURAS if tipologia in a['familias']]


def aperturas_para_producto(tipologia: Optional[str], admitidas: Iterable[str]) -> List[str]:
    """Códigos que el cotizador debe ofrecer.

    Si el producto tiene aperturas admitidas cargadas en el ABM, manda esa lista
    (en el orden del catálogo). Si no tiene ninguna, ofrece todas las compatibles
    con su tipología: así nada cambia hasta que alguien configure el producto.
    """
    admitidas = set(admitidas or [])
    if admitidas:
        return [a['codigo'] for a in APERTURAS if a['codigo'] in admitidas]
    return [a['codigo'] for a in aperturas_compatibles(tipologia)]


_CLAVES_PUBLICAS = ('codigo', 'nombre', 'simbolo', 'hojas', 'lado', 'por_hoja')


def aperturas_publicas(codigos: Iterable[str]) -> List[Dict[str, Any]]:
    """Definiciones para el cotizador (sin `familias`), en el orden del catálogo."""
    codigos = set(codigos or [])
    return [
        {k: a[k] for k in _CLAVES_PUBLICAS}
        for a in APERTURAS if a['codigo'] in codigos
    ]


def _hojas_efectivas(definicion: Dict[str, Any], hojas: Any) -> int:
    try:
        n = int(hojas or 0)
    except (TypeError, ValueError):
        n = 0
    return n if n in definicion['hojas'] else definicion['hojas'][0]


def _hoja_default(indice: int, total: int) -> Dict[str, str]:
    # Igual que el visor 3D: las hojas pares corren al carril interior hacia la
    # derecha, las impares al exterior hacia la izquierda; la última siempre a la
    # izquierda para que las hojas se crucen y no se salgan del marco.
    if indice == total - 1:
        return {'movimiento': 'izq', 'carril': 'ext' if indice % 2 else 'int'}
    return {'movimiento': 'der' if indice % 2 == 0 else 'izq',
            'carril': 'int' if indice % 2 == 0 else 'ext'}


def normalizar_apertura(data: Any, hojas: Any = None) -> Optional[Dict[str, Any]]:
    """Limpia una apertura venida del cotizador o del snapshot.

    Devuelve un dict con solo las claves que aplican al tipo (`lado` si pide
    bisagra, `hojas` si se edita por hoja), completando defaults. Devuelve None
    si el código no existe, para que un dato roto no rompa el dibujo ni el PDF.
    """
    if not isinstance(data, dict):
        return None
    definicion = APERTURA_POR_CODIGO.get(str(data.get('codigo') or ''))
    if not definicion:
        return None

    salida: Dict[str, Any] = {'codigo': definicion['codigo']}

    if definicion['lado']:
        lado = str(data.get('lado') or '').lower()
        salida['lado'] = lado if lado in LADOS else 'izq'

    if definicion['por_hoja']:
        n = _hojas_efectivas(definicion, hojas if hojas is not None else len(data.get('hojas') or []))
        recibidas = data.get('hojas') if isinstance(data.get('hojas'), list) else []
        hojas_salida = []
        for i in range(n):
            base = _hoja_default(i, n)
            recibida = recibidas[i] if i < len(recibidas) and isinstance(recibidas[i], dict) else {}
            mov = str(recibida.get('movimiento') or '').lower()
            carril = str(recibida.get('carril') or '').lower()
            hojas_salida.append({
                'movimiento': mov if mov in MOVIMIENTOS else base['movimiento'],
                'carril': carril if carril in CARRILES else base['carril'],
            })
        salida['hojas'] = hojas_salida

    return salida


def apertura_default(codigo: str, hojas: Any = None) -> Optional[Dict[str, Any]]:
    return normalizar_apertura({'codigo': codigo}, hojas)


def describir_apertura(apertura: Optional[Dict[str, Any]]) -> str:
    """Texto corto para listados y PDF: 'Paño de abrir 1 hoja, bisagra izquierda'."""
    if not apertura:
        return ''
    definicion = APERTURA_POR_CODIGO.get(apertura.get('codigo') or '')
    if not definicion:
        return ''
    texto = definicion['nombre']
    if definicion['lado'] and apertura.get('lado'):
        texto += ', bisagra ' + ('izquierda' if apertura['lado'] == 'izq' else 'derecha')
    return texto
