from __future__ import annotations

from typing import Any, Dict, Iterable, List

from plantillas.models import OpcionalFabrica
from pricing.models import Hoja, Interior, Marco, Tratamiento, Vidrio


_GENERIC_DESCRIPTIONS = {
    '',
    'abertura sin descripcion',
    'abertura sin descripción',
}


def _clean_text(value: Any) -> str:
    if value is None:
        return ''
    return ' '.join(str(value).split()).strip()


def _normalize_text(value: Any) -> str:
    return _clean_text(value).casefold()


def _is_generic_description(value: Any) -> bool:
    return _normalize_text(value) in _GENERIC_DESCRIPTIONS


def _contains_text(haystack: Any, needle: Any) -> bool:
    haystack_text = _normalize_text(haystack)
    needle_text = _normalize_text(needle)
    return bool(haystack_text and needle_text and needle_text in haystack_text)


def _format_mm(value: Any) -> str:
    if value in (None, ''):
        return ''
    try:
        number = float(value)
    except (TypeError, ValueError):
        return _clean_text(value)

    if number.is_integer():
        return str(int(number))
    return f'{number:.2f}'.rstrip('0').rstrip('.')


def _humanize_list(values: Iterable[str]) -> str:
    items = [_clean_text(value) for value in values if _clean_text(value)]
    if not items:
        return ''
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f'{items[0]} y {items[1]}'
    return f"{', '.join(items[:-1])} y {items[-1]}"


def _format_option_label(option: Dict[str, Any]) -> str:
    code = _clean_text(option.get('codigo'))
    name = _clean_text(option.get('nombre'))
    if code and name and _normalize_text(code) != _normalize_text(name):
        return f'{code} - {name}'
    return name or code


def _serialize_entity(entity: Any, label_field: str) -> Dict[str, Any] | None:
    if not entity:
        return None

    label = _clean_text(getattr(entity, label_field, ''))
    if not label:
        return None

    return {
        'id': getattr(entity, 'pk', None),
        label_field: label,
    }


def _build_title(snapshot: Dict[str, Any]) -> str:
    manual_description = _clean_text(snapshot.get('descripcion_manual'))
    if not _is_generic_description(manual_description):
        return manual_description

    for entry, label_field in (
        (snapshot.get('producto'), 'descripcion'),
        (snapshot.get('marco'), 'descripcion'),
        (snapshot.get('hoja'), 'descripcion'),
    ):
        label = _clean_text((entry or {}).get(label_field))
        if label:
            return label

    return 'Abertura a medida'


def build_narrative_from_snapshot(snapshot: Dict[str, Any]) -> str:
    title = _build_title(snapshot)
    product_label = _clean_text((snapshot.get('producto') or {}).get('descripcion'))
    line_label = _clean_text((snapshot.get('linea') or {}).get('nombre'))
    extrusora_label = _clean_text((snapshot.get('extrusora') or {}).get('nombre'))
    marco_label = _clean_text((snapshot.get('marco') or {}).get('descripcion'))
    hoja_label = _clean_text((snapshot.get('hoja') or {}).get('descripcion'))
    interior_label = _clean_text((snapshot.get('interior') or {}).get('descripcion'))
    vidrio_label = _clean_text((snapshot.get('vidrio') or {}).get('descripcion'))
    tratamiento_label = _clean_text((snapshot.get('tratamiento') or {}).get('descripcion'))
    options = snapshot.get('opcionales') or []
    option_labels = [_format_option_label(option) for option in options]

    clauses: List[str] = []

    if line_label and extrusora_label:
        clauses.append(f'en línea {line_label} de {extrusora_label}')
    elif line_label:
        clauses.append(f'en línea {line_label}')
    elif extrusora_label:
        clauses.append(f'de {extrusora_label}')

    if product_label and not _contains_text(title, product_label):
        clauses.append(f'modelo {product_label}')

    if marco_label:
        clauses.append(f'con marco {marco_label}')

    if hoja_label:
        clauses.append(f'hoja {hoja_label}')

    if interior_label:
        clauses.append(f'interior {interior_label}')

    if vidrio_label:
        clauses.append(f'vidrio {vidrio_label}')

    if tratamiento_label:
        clauses.append(f'terminación {tratamiento_label.lower()}')

    width = _format_mm(snapshot.get('ancho_mm'))
    height = _format_mm(snapshot.get('alto_mm'))
    if width and height:
        clauses.append(f'medidas {width} x {height} mm')

    quantity = snapshot.get('cantidad') or 0
    if quantity and int(quantity) > 1:
        clauses.append(f'por {int(quantity)} unidades')

    if option_labels:
        clauses.append(f'con opcionales {_humanize_list(option_labels)}')

    sentence = title.rstrip(' .')
    if clauses:
        sentence = f'{sentence} {clauses[0]}'
        if len(clauses) > 1:
            sentence += ', ' + ', '.join(clauses[1:])

    return sentence.rstrip(' ,.') + '.'


def build_technical_summary(snapshot: Dict[str, Any]) -> str:
    parts: List[str] = []

    quantity = snapshot.get('cantidad') or 0
    if quantity:
        unit_label = 'unidad' if int(quantity) == 1 else 'unidades'
        parts.append(f'{int(quantity)} {unit_label}')

    line_label = _clean_text((snapshot.get('linea') or {}).get('nombre'))
    product_label = _clean_text((snapshot.get('producto') or {}).get('descripcion'))
    width = _format_mm(snapshot.get('ancho_mm'))
    height = _format_mm(snapshot.get('alto_mm'))
    if line_label:
        parts.append(line_label)

    if product_label:
        parts.append(product_label)

    if width and height:
        parts.append(f'{width} x {height} mm')

    vidrio_label = _clean_text((snapshot.get('vidrio') or {}).get('descripcion'))
    if vidrio_label:
        parts.append(f'Vidrio {vidrio_label}')

    tratamiento_label = _clean_text((snapshot.get('tratamiento') or {}).get('descripcion'))
    if tratamiento_label:
        parts.append(f'Terminación {tratamiento_label}')

    option_labels = [_format_option_label(option) for option in (snapshot.get('opcionales') or [])]
    if option_labels:
        parts.append(f'Opcionales: {_humanize_list(option_labels)}')

    return ' · '.join(parts)


def build_compact_technical_summary(snapshot: Dict[str, Any]) -> str:
    parts: List[str] = []

    quantity = snapshot.get('cantidad') or 0
    if quantity:
        unit_label = 'unidad' if int(quantity) == 1 else 'unidades'
        parts.append(f'{int(quantity)} {unit_label}')

    line_label = _clean_text((snapshot.get('linea') or {}).get('nombre'))
    if line_label:
        parts.append(line_label)

    product_label = _clean_text((snapshot.get('producto') or {}).get('descripcion'))
    if product_label:
        parts.append(product_label)

    width = _format_mm(snapshot.get('ancho_mm'))
    height = _format_mm(snapshot.get('alto_mm'))
    if width and height:
        parts.append(f'{width} x {height} mm')

    vidrio_label = _clean_text((snapshot.get('vidrio') or {}).get('descripcion'))
    if vidrio_label:
        parts.append(f'Vidrio {vidrio_label}')

    tratamiento_label = _clean_text((snapshot.get('tratamiento') or {}).get('descripcion'))
    if tratamiento_label:
        parts.append(f'Terminación {tratamiento_label}')

    return ' · '.join(parts)


def _should_refresh_technical_summary(snapshot: Dict[str, Any], summary: Any) -> bool:
    summary_text = _clean_text(summary)
    if not summary_text:
        return True

    for label in (
        _clean_text((snapshot.get('linea') or {}).get('nombre')),
        _clean_text((snapshot.get('producto') or {}).get('descripcion')),
        _clean_text((snapshot.get('vidrio') or {}).get('descripcion')),
    ):
        if label and not _contains_text(summary_text, label):
            return True

    return False


def _serialize_options(options_data: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    option_ids: List[int] = []
    for option in options_data or []:
        option_id = option.get('id')
        if option_id in (None, ''):
            continue
        try:
            option_ids.append(int(option_id))
        except (TypeError, ValueError):
            continue

    if not option_ids:
        return []

    options_by_id = OpcionalFabrica.objects.filter(pk__in=option_ids, activo=True).in_bulk()
    serialized: List[Dict[str, Any]] = []
    for option_id in option_ids:
        option = options_by_id.get(option_id)
        if not option:
            continue
        serialized.append({
            'id': option.id,
            'codigo': _clean_text(option.codigo),
            'nombre': _clean_text(option.nombre),
            'tipo': _clean_text(option.tipo),
        })
    return serialized


def build_item_snapshot(config: Dict[str, Any], descripcion_manual: str, cantidad: int = 1) -> Dict[str, Any]:
    marco = (
        Marco.objects
        .select_related('producto__linea__extrusora')
        .filter(pk=config.get('marco_id'))
        .first()
    )
    producto = getattr(marco, 'producto', None)
    linea = getattr(producto, 'linea', None)
    extrusora = getattr(producto, 'extrusora', None)

    hoja = None
    if config.get('hoja_id'):
        hoja = Hoja.objects.filter(pk=config.get('hoja_id')).first()

    interior = None
    if config.get('interior_id'):
        interior = Interior.objects.filter(pk=config.get('interior_id')).first()

    vidrio = None
    if config.get('vidrio_codigo'):
        vidrio = Vidrio.objects.filter(pk=config.get('vidrio_codigo')).first()

    tratamiento = None
    if config.get('tratamiento_id'):
        tratamiento = Tratamiento.objects.filter(pk=config.get('tratamiento_id')).first()

    snapshot: Dict[str, Any] = {
        'descripcion_manual': _clean_text(descripcion_manual),
        'cantidad': int(cantidad or 1),
        'ancho_mm': config.get('ancho_mm'),
        'alto_mm': config.get('alto_mm'),
        'margen_porcentaje': config.get('margen_porcentaje'),
        'extrusora': _serialize_entity(extrusora, 'nombre'),
        'linea': _serialize_entity(linea, 'nombre'),
        'producto': _serialize_entity(producto, 'descripcion'),
        'marco': _serialize_entity(marco, 'descripcion'),
        'hoja': _serialize_entity(hoja, 'descripcion'),
        'interior': _serialize_entity(interior, 'descripcion'),
        'vidrio': {
            'codigo': _clean_text(getattr(vidrio, 'codigo', '')),
            'descripcion': _clean_text(getattr(vidrio, 'descripcion', '')),
        } if vidrio else None,
        'tratamiento': _serialize_entity(tratamiento, 'descripcion'),
        'opcionales': _serialize_options(config.get('opcionales') or []),
    }

    snapshot['titulo_item'] = _build_title(snapshot)
    snapshot['descripcion_narrativa'] = build_narrative_from_snapshot(snapshot)
    snapshot['resumen_tecnico'] = build_technical_summary(snapshot)
    return snapshot


def _build_legacy_snapshot(item: Any) -> Dict[str, Any]:
    result = item.resultado_json if isinstance(item.resultado_json, dict) else {}
    desglose = result.get('desglose') or {}
    vidrios = desglose.get('vidrios') or {}
    tratamiento = desglose.get('tratamiento') or {}
    opcionales = desglose.get('opcionales') or []

    snapshot: Dict[str, Any] = {
        'descripcion_manual': _clean_text(item.descripcion),
        'cantidad': item.cantidad,
        'ancho_mm': item.ancho_mm,
        'alto_mm': item.alto_mm,
        'margen_porcentaje': item.margen_porcentaje,
        'vidrio': {
            'codigo': _clean_text(vidrios.get('codigo')),
            'descripcion': _clean_text(vidrios.get('descripcion')),
        } if vidrios else None,
        'tratamiento': {
            'descripcion': _clean_text(tratamiento.get('descripcion')),
        } if tratamiento else None,
        'opcionales': [
            {
                'codigo': _clean_text(option.get('codigo')),
                'nombre': _clean_text(option.get('nombre')),
                'tipo': _clean_text(option.get('tipo')),
            }
            for option in opcionales
        ],
    }

    snapshot['titulo_item'] = _build_title(snapshot)
    snapshot['descripcion_narrativa'] = build_narrative_from_snapshot(snapshot)
    snapshot['resumen_tecnico'] = build_technical_summary(snapshot)
    return snapshot


def build_pdf_item_context(item: Any) -> Dict[str, Any]:
    result = item.resultado_json if isinstance(item.resultado_json, dict) else {}
    snapshot = result.get('snapshot_item') if isinstance(result, dict) else None

    if not isinstance(snapshot, dict):
        snapshot = _build_legacy_snapshot(item)
    else:
        snapshot = dict(snapshot)
        snapshot.setdefault('descripcion_manual', _clean_text(item.descripcion))
        snapshot.setdefault('cantidad', item.cantidad)
        snapshot.setdefault('ancho_mm', item.ancho_mm)
        snapshot.setdefault('alto_mm', item.alto_mm)
        snapshot.setdefault('margen_porcentaje', item.margen_porcentaje)
        snapshot.setdefault('opcionales', [])
        snapshot.setdefault('titulo_item', _build_title(snapshot))
        snapshot.setdefault('descripcion_narrativa', build_narrative_from_snapshot(snapshot))
        if _should_refresh_technical_summary(snapshot, snapshot.get('resumen_tecnico')):
            snapshot['resumen_tecnico'] = build_technical_summary(snapshot)
        else:
            snapshot.setdefault('resumen_tecnico', build_technical_summary(snapshot))

    return {
        'item': item,
        'titulo': snapshot.get('titulo_item') or _build_title(snapshot),
        'descripcion_narrativa': snapshot.get('descripcion_narrativa') or build_narrative_from_snapshot(snapshot),
        'resumen_compacto': build_compact_technical_summary(snapshot),
        'resumen_tecnico': snapshot.get('resumen_tecnico') or build_technical_summary(snapshot),
    }
