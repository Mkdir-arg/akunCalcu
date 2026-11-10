"""Tramos de perfil de marco de una orden de fabricación (REQ-070)."""
import logging

from plantillas.services.abertura_catalogo import seleccion_inicial
from plantillas.services.medidas import ancho_alto_mm
from pricing.models import DespiecePerfilesMarco, Perfil
from pricing.services.formula_parser import FormulaError, evaluar_formula

logger = logging.getLogger(__name__)

SIN_COLOR = 'SIN COLOR'


class MotivoExclusion(Exception):
    """Orden que no se puede calcular. `accion` es el texto del botón y `destino` dónde se corrige."""

    def __init__(self, texto, accion, destino='orden', ref=None):
        super().__init__(texto)
        self.texto = texto
        self.accion = accion
        self.destino = destino
        self.ref = ref


def _evaluar(formula, variables):
    if not formula:
        return 0.0
    try:
        return float(evaluar_formula(formula, variables))
    except FormulaError as exc:
        logger.warning('Fórmula inválida %r: %s', formula, exc)
        return 0.0


def numero_o_none(texto):
    """minimo_reutilizable es TextField: vacío o no numérico = None."""
    try:
        valor = float(str(texto or '').strip().replace(',', '.'))
    except ValueError:
        return None
    return valor if valor > 0 else None


def color_de(orden):
    return (orden.color or '').strip().upper() or SIN_COLOR


def _medidas(orden):
    filas = []
    for fila in orden.medidas.all():
        texto = (fila.medida or '').strip()
        if not texto:
            continue
        dimensiones = ancho_alto_mm(texto)
        if dimensiones is None:
            raise MotivoExclusion(f'La medida dice «{texto}»', 'Corregir medida')
        filas.append((fila, dimensiones))
    if not filas:
        raise MotivoExclusion('La orden no tiene medidas cargadas', 'Corregir medida')
    return filas


def tramos_de_orden(orden):
    """(tramos, motivo): motivo es un MotivoExclusion o None. Cada tramo lleva su 'cantidad' ya multiplicada."""
    try:
        return _tramos(orden), None
    except MotivoExclusion as motivo:
        return [], motivo


def _tramos(orden):
    marco_id = seleccion_inicial(orden).get('marco')
    if not marco_id:
        raise MotivoExclusion('Sin marco elegido del catálogo', 'Elegir abertura')
    medidas = _medidas(orden)
    despieces = list(DespiecePerfilesMarco.objects.filter(marco_id=marco_id))
    if not despieces:
        raise MotivoExclusion('El marco no tiene despiece cargado', 'Ver marco', 'marco', marco_id)

    color = color_de(orden)
    pedido = orden.pedido
    perfiles = {}
    tramos = []
    for fila, (ancho, alto) in medidas:
        variables = {'Ancho': ancho, 'Alto': alto, 'Cantidad': 1}
        for despiece in despieces:
            codigo = (despiece.perfil or '').strip()
            if not codigo:
                continue
            cantidad = _evaluar(despiece.formula_cantidad, variables)
            largo = _evaluar(despiece.formula_perfil, variables)
            if cantidad <= 0 or largo <= 0:
                continue
            if codigo not in perfiles:
                perfiles[codigo] = Perfil.objects.filter(codigo=codigo).first()
            perfil = perfiles[codigo]
            total = round(cantidad) * fila.cantidad
            if total <= 0:
                continue
            tramos.append({
                'codigo': codigo,
                'descripcion': (perfil.descripcion or '').strip() if perfil else '',
                'color': color,
                'largo_mm': int(round(largo)),
                'cantidad': total,
                'angulo': (despiece.angulo or '').strip(),
                'long_tira': perfil.long_tira if perfil and perfil.long_tira else None,
                'minimo': numero_o_none(perfil.minimo_reutilizable) if perfil else None,
                'orden_id': orden.pk,
                'orden': orden.numero_formateado,
                'pedido_id': pedido.pk,
                'pedido': pedido.numero,
                'cliente': pedido.cliente,
            })
    if not tramos:
        raise MotivoExclusion('El despiece del marco no da cortes para esa medida', 'Ver marco', 'marco', marco_id)
    return tramos
