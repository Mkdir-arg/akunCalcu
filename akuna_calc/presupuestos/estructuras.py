"""Ítems estructura de un presupuesto (REQ-062): se guardan como un ItemPresupuesto más,
con `resultado_json['tipo'] == 'estructura'` y el detalle de cada módulo en JSON."""

import re

from pricing.services.calculator import PricingError
from pricing.services.estructura import calcular_estructura_detallada

from .pdf_descriptions import (
    ESTRUCTURA_SIN_NOMBRE, build_dibujo_params, build_item_snapshot, describir_estructura,
)


def _sin_estructura(texto):
    # tipologia.py clasifica como "no se dibuja" todo texto con esta palabra.
    return re.sub(r'estructura', '', texto, flags=re.IGNORECASE).strip()


def fields_item_estructura(presupuesto, data, descripcion, cantidad):
    """Campos de un ItemPresupuesto estructura desde el JSON del editor.

    Devuelve (fields, error). El precio se recalcula siempre acá: lo que mande el
    navegador no se usa. Mismo contrato que `_fields_item_desde_post`."""
    try:
        respuesta, norm = calcular_estructura_detallada(data)
    except PricingError as e:
        return None, f'Error al calcular la estructura: {e}'

    nombre = norm['nombre'] or (descripcion or '').strip() or ESTRUCTURA_SIN_NOMBRE
    comun = norm['comun']

    modulos = []
    for m in sorted(norm['modulos'], key=lambda m: int(m['etiqueta'][1:])):
        calculado = next(c for c in respuesta['modulos'] if c['indice'] == m['indice'])
        descripcion_modulo = f"{_sin_estructura(m['producto_descripcion']) or 'Abertura'} — {m['etiqueta']}"
        snapshot = build_item_snapshot(m['config_completa'], descripcion_modulo, cantidad)
        modulos.append({
            'etiqueta': m['etiqueta'], 'x': m['x'], 'y': m['y'], 'ancho': m['ancho'], 'alto': m['alto'],
            'config': m['config'],
            'resultado': {k: calculado[k] for k in ('precio_total', 'subtotal', 'margen', 'desglose', 'resumen')},
            'snapshot_item': snapshot,
            'dibujo': build_dibujo_params(snapshot),
        })

    union = respuesta['union']
    envolvente = respuesta['envolvente']
    primero = modulos[0]['snapshot_item']
    snapshot_item = {
        'cantidad': cantidad, 'ancho_mm': envolvente['ancho'], 'alto_mm': envolvente['alto'],
        'margen_porcentaje': comun['margen_porcentaje'],
        'extrusora': primero.get('extrusora'), 'linea': primero.get('linea'),
        'tratamiento': primero.get('tratamiento'),
    }
    resultado = {
        'tipo': 'estructura', 'version': 1,
        'precio_total': respuesta['precio_total'], 'subtotal': respuesta['subtotal'], 'margen': respuesta['margen'],
        'precio_unitario_base': respuesta['precio_total'],
        'recargo_renovacion_unitario_aplicado': 0,
        'recargo_renovacion_total_aplicado': 0,
        'resumen': {
            'total_modulos': round(respuesta['precio_total'] - union['precio_total'], 2),
            'total_union': union['precio_total'],
        },
        'snapshot_item': snapshot_item,
        'estructura': {
            'nombre': nombre, 'pared': norm['pared'], 'comun': comun,
            'perfil_union': union['perfil'], 'envolvente': envolvente, 'union': union,
            'modulos': modulos, 'juntas': respuesta['juntas'],
        },
    }
    textos = describir_estructura(resultado, cantidad)
    snapshot_item.update({
        'titulo_item': textos['titulo'],
        'resumen_tecnico': textos['resumen_tecnico'],
        'descripcion_manual': nombre,
    })

    precio_unitario = respuesta['precio_total']
    if presupuesto.tipo_obra == 'renovacion':
        recargo_unitario = float(presupuesto.recargo_renovacion_unitario or 0)
        resultado['recargo_renovacion_unitario_aplicado'] = recargo_unitario
        resultado['recargo_renovacion_total_aplicado'] = recargo_unitario * cantidad
        precio_unitario += recargo_unitario

    return {
        'descripcion': nombre[:300], 'cantidad': cantidad,
        'ancho_mm': envolvente['ancho'], 'alto_mm': envolvente['alto'],
        'margen_porcentaje': comun['margen_porcentaje'],
        'precio_unitario': precio_unitario, 'resultado_json': resultado,
    }, None
