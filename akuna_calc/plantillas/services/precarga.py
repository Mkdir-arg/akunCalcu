"""Precarga del bloque «Detalle» de la orden con lo que el cotizador ya sabe (REQ-063, M1).

Lee el `snapshot_item` que guarda cada ítem del presupuesto. Lo que no está en el snapshot
(PVC, terciarizados, snapshots viejos) queda vacío y el PDF lo muestra como casilla SÍ / NO.
"""
from pricing.services.calculator import orientacion_tirantes


LADOS = {'izq': 'Izquierda', 'der': 'Derecha'}


def _descripcion(snapshot, clave):
    return ((snapshot.get(clave) or {}).get('descripcion') or '').strip()


def detalle_desde_snapshot(snapshot):
    """Devuelve {campo_de_OrdenFabricacion: texto} solo con los campos que se pudieron resolver."""
    snapshot = snapshot if isinstance(snapshot, dict) else {}
    datos = {}

    opcionales = [o for o in snapshot.get('opcionales') or [] if isinstance(o, dict)]
    mosquiteros = [o.get('nombre', '').strip() for o in opcionales if o.get('tipo') == 'mosquitero']
    if mosquiteros:
        datos['mosquitero'] = 'SÍ'
        datos['mosquitero_modelo'] = ', '.join(m for m in mosquiteros if m)
    if any(o.get('tipo') == 'premarco' for o in opcionales):
        datos['premarco'] = 'SÍ'

    marco = _descripcion(snapshot, 'marco')
    if marco:
        datos['tipo_marco'] = marco
    hoja = _descripcion(snapshot, 'hoja')
    if hoja:
        datos['modelo_hoja'] = hoja

    apertura = snapshot.get('apertura') if isinstance(snapshot.get('apertura'), dict) else {}
    hojas = apertura.get('hojas')
    if isinstance(hojas, list) and hojas:
        datos['cantidad_hojas'] = str(len(hojas))
    if apertura.get('lado') in LADOS:
        datos['lado'] = LADOS[apertura['lado']]

    tirantes = snapshot.get('tirantes') if isinstance(snapshot.get('tirantes'), dict) else {}
    secciones = tirantes.get('secciones') or []
    if len(secciones) > 1:
        cantidad = len(secciones) - 1
        sentido = 'vertical' if orientacion_tirantes(tirantes) == 'vertical' else 'horizontal'
        plural = 'es' if cantidad > 1 else ''
        datos['travesano'] = f'SÍ ({cantidad} {sentido}{plural})'

    return datos
