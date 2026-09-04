"""Lectura de las cotizaciones PDF que genera el software de REHAU (aberturas de PVC).

El PDF siempre tiene la misma estructura: cabecera con cliente, número y fecha; un bloque por
ítem con la etiqueta "Tipología: Vn", la descripción en varias líneas y la fila
`UNITARIO U$S · UNIDADES · TOTAL U$S`; y al pie los totales. Las medidas están solo en el
dibujo (imagen), no en el texto, así que no se importan.

La extracción de texto (`extraer_texto`) y el parser (`parsear_cotizacion`) están separados:
el parser trabaja sobre texto plano y se testea con las muestras sin abrir un PDF.
"""
import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import List, Optional

MAX_PAGINAS = 40
TOLERANCIA_TOTAL = Decimal('0.05')

RE_PRECIO = re.compile(r'^\s*([\d.]+,\d{2})\s*U\$S\s+(\d+)\s+([\d.]+,\d{2})\s*U\$S\s*$')
RE_TIPOLOGIA = re.compile(r'^\s*Tipolog[ií]a:\s*(\S+)')
RE_RUIDO = re.compile(
    r'^\s*(UNITARIO\s+UNIDADES\s+TOTAL|UNITARIO|UNIDADES|TOTAL|Pag\.?\s*\d+'
    r'|TOTAL\s+(UNIDADES|M2|ML|NETO|PROYECTO)\b.*|\d+\s*%\s*I\.V\.A.*)\s*$'
)
RE_INICIO = re.compile(r'De acuerdo a su requerimiento.*:\s*$')
RE_CABECERA = {
    'numero': re.compile(r'PRESUPUESTO\s+N[º°o]:\s*(\d+)'),
    'cliente': re.compile(r'NOMBRE DEL CLIENTE:\s*(.+?)(?:\s+PRESUPUESTO\s+N|\s*$)', re.MULTILINE),
    'fecha': re.compile(r'FECHA:\s*(\d{2}/\d{2}/\d{4})'),
    'total_neto': re.compile(r'TOTAL NETO:\s*([\d.]+,\d{2})\s*U\$S'),
}


class ImportacionError(Exception):
    """El archivo no se pudo leer o no es una cotización REHAU."""


@dataclass
class ItemRehau:
    tipologia: str
    descripcion: str
    cantidad: int
    valor_usd: Decimal
    total_usd: Decimal

    @property
    def total_coincide(self) -> bool:
        return (self.valor_usd * self.cantidad).quantize(Decimal('0.01')) == self.total_usd


@dataclass
class CotizacionRehau:
    numero: Optional[str] = None
    cliente: Optional[str] = None
    fecha: Optional[str] = None
    total_neto: Optional[Decimal] = None
    items: List[ItemRehau] = field(default_factory=list)
    advertencias: List[str] = field(default_factory=list)

    @property
    def suma_items(self) -> Decimal:
        return sum((item.total_usd for item in self.items), Decimal('0'))


def _decimal_ar(texto: str) -> Decimal:
    """'1.469,56' -> Decimal('1469.56')."""
    try:
        return Decimal(texto.replace('.', '').replace(',', '.'))
    except InvalidOperation as exc:
        raise ImportacionError(f'Importe ilegible en el PDF: {texto!r}') from exc


def _formato_ar(valor: Decimal) -> str:
    entero, _, dec = f'{valor:,.2f}'.partition('.')
    return f"{entero.replace(',', '.')},{dec}"


def _limpiar(texto: str) -> str:
    texto = re.sub(r'\.{2,}', '.', texto)
    texto = re.sub(r'\.(?=[A-Za-zÁÉÍÓÚáéíóúÑñ])', '. ', texto)
    return re.sub(r'\s+', ' ', texto).strip()


def _armar_descripcion(tipologia: str, lineas: List[str]) -> str:
    """Devuelve "V1 · <título>. <componente>, <componente>, ...".

    El título de REHAU termina en " ." (a veces partido en dos líneas); lo que sigue son
    los componentes, uno por línea.
    """
    titulo_lineas: List[str] = []
    resto = list(lineas)
    while resto:
        linea = resto.pop(0)
        if linea.rstrip().endswith('.'):
            titulo_lineas.append(linea.rstrip().rstrip('.').rstrip())
            break
        titulo_lineas.append(linea)
    componentes = [c.strip() for c in resto if c.strip()]
    titulo = _limpiar(' '.join(titulo_lineas))
    partes = [p for p in (titulo, ', '.join(componentes)) if p]
    cuerpo = '. '.join(partes)
    return f'{tipologia} · {cuerpo}' if tipologia else cuerpo


def extraer_texto(archivo) -> str:
    """Texto de todas las páginas del PDF, en orden. `archivo` es un file-like."""
    from pypdf import PdfReader

    try:
        lector = PdfReader(archivo, strict=False)
        if lector.is_encrypted:
            lector.decrypt('')
        if len(lector.pages) > MAX_PAGINAS:
            raise ImportacionError(f'El PDF tiene más de {MAX_PAGINAS} páginas; no parece una cotización.')
        paginas = [pagina.extract_text() or '' for pagina in lector.pages]
    except ImportacionError:
        raise
    except Exception as exc:  # pypdf lanza de todo ante un archivo roto
        raise ImportacionError('No se pudo leer el PDF. ¿Está dañado o protegido?') from exc
    texto = '\n'.join(paginas)
    if not texto.strip():
        raise ImportacionError(
            'El PDF no tiene texto (¿es un escaneo o una foto?). '
            'Solo se pueden importar los PDF generados por el software de REHAU.'
        )
    return texto


def parsear_cotizacion(texto: str) -> CotizacionRehau:
    cotizacion = CotizacionRehau()
    for clave, regex in RE_CABECERA.items():
        coincidencia = regex.search(texto)
        if coincidencia:
            valor = coincidencia.group(1).strip()
            setattr(cotizacion, clave, _decimal_ar(valor) if clave == 'total_neto' else valor)

    lineas = texto.splitlines()
    en_items = not any(RE_INICIO.search(linea) for linea in lineas)
    tipologias: List[str] = []
    bloques: List[dict] = []
    buffer: List[str] = []
    for linea in lineas:
        if not en_items:
            en_items = bool(RE_INICIO.search(linea))
            continue
        coincidencia = RE_TIPOLOGIA.match(linea)
        if coincidencia:
            tipologias.append(coincidencia.group(1))
            continue
        if not linea.strip() or RE_RUIDO.match(linea):
            continue
        coincidencia = RE_PRECIO.match(linea)
        if coincidencia:
            bloques.append({
                'lineas': buffer,
                'valor_usd': _decimal_ar(coincidencia.group(1)),
                'cantidad': int(coincidencia.group(2)),
                'total_usd': _decimal_ar(coincidencia.group(3)),
            })
            buffer = []
            continue
        buffer.append(linea.strip())

    if not bloques:
        raise ImportacionError(
            'No se encontraron ítems en el PDF. ¿Es una cotización generada por el software de REHAU?'
        )

    if len(tipologias) != len(bloques):
        tipologias = [''] * len(bloques)
        cotizacion.advertencias.append('No se pudieron asociar las etiquetas de tipología (Vn) a los ítems.')

    for posicion, (tipologia, bloque) in enumerate(zip(tipologias, bloques), start=1):
        item = ItemRehau(
            tipologia=tipologia,
            descripcion=_armar_descripcion(tipologia, bloque['lineas']),
            cantidad=bloque['cantidad'],
            valor_usd=bloque['valor_usd'],
            total_usd=bloque['total_usd'],
        )
        if not item.total_coincide:
            cotizacion.advertencias.append(
                f'Ítem {tipologia or posicion}: unitario × unidades no coincide con el total del PDF.'
            )
        cotizacion.items.append(item)

    if cotizacion.total_neto is not None and abs(cotizacion.total_neto - cotizacion.suma_items) > TOLERANCIA_TOTAL:
        cotizacion.advertencias.append(
            f'El total neto del PDF ({_formato_ar(cotizacion.total_neto)} U$S) no coincide con la suma de los '
            f'ítems detectados ({_formato_ar(cotizacion.suma_items)} U$S). Puede faltar un ítem.'
        )
    return cotizacion
