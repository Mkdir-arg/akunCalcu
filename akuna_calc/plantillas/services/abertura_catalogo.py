"""Abertura de la orden elegida del catálogo de pricing (REQ-067).

Mismas reglas que las APIs del cotizador (`pricing/catalog_views.py`): cada nivel se filtra por el
anterior y lo bloqueado no se ofrece. El navegador manda IDs; acá se validan y se traducen a los
textos que la orden imprime, para que no se pueda guardar una combinación que no existe.
"""
from django.core.exceptions import ValidationError
from django.db import connection

from pricing.models import Extrusora, Hoja, Linea, Marco, Producto, Tratamiento, Vidrio

CADENA = ('extrusora', 'linea', 'producto', 'marco', 'hoja', 'vidrio')
CLAVES = CADENA + ('tratamiento',)
# Campo de la orden que sale de cada nivel (extrusora no se imprime).
CAMPO_TEXTO = {
    'linea': 'linea', 'producto': 'tipo_abertura', 'marco': 'tipo_marco',
    'hoja': 'modelo_hoja', 'vidrio': 'tipo_vidrio', 'tratamiento': 'color',
}


def _texto(valor):
    return (valor or '').strip()


def _id(valor, etiqueta):
    try:
        return int(valor)
    except (TypeError, ValueError):
        raise ValidationError(f'{etiqueta} inválido.')


def vidrios_de_hoja(hoja_id):
    """Códigos de vidrio admitidos por la hoja (tabla legacy `vidrio_hojas`, igual que la API)."""
    with connection.cursor() as cursor:
        cursor.execute('SELECT vidrio_codigo FROM vidrio_hojas WHERE hoja_id = %s', [hoja_id])
        return [row[0] for row in cursor.fetchall()]


def resolver_cadena(ids):
    """ids: {'extrusora': '3', 'linea': '7', …} (vacío = no elegido).

    Devuelve (textos, seleccion): textos = {campo_orden: texto} para TODA la cadena (lo no elegido
    queda vacío, para no dejar un dato de otra línea); seleccion = {clave: id} de lo elegido.
    """
    elegidos = {clave: _texto(str(ids.get(clave) or '')) for clave in CADENA}
    for i, clave in enumerate(CADENA[1:], start=1):
        if elegidos[clave] and not elegidos[CADENA[i - 1]]:
            raise ValidationError('La abertura está incompleta: elegí los desplegables en orden.')

    textos = {campo: '' for clave, campo in CAMPO_TEXTO.items() if clave in CADENA}
    textos['cantidad_hojas'] = ''
    seleccion = {}
    if not elegidos['extrusora']:
        return textos, seleccion

    extrusora = Extrusora.objects.exclude(bloqueado='Si').filter(pk=_id(elegidos['extrusora'], 'Extrusora')).first()
    if extrusora is None:
        raise ValidationError('La extrusora elegida no está en el catálogo.')
    seleccion['extrusora'] = extrusora.pk

    padre = extrusora
    pasos = (
        ('linea', Linea, 'extrusora_id', 'nombre', 'La línea no corresponde a la extrusora.'),
        ('producto', Producto, 'linea_id', 'descripcion', 'El producto no corresponde a la línea.'),
        ('marco', Marco, 'producto_id', 'descripcion', 'El marco no corresponde al producto.'),
        ('hoja', Hoja, 'marco_id', 'descripcion', 'La hoja no corresponde al marco.'),
    )
    for clave, modelo, fk, campo, error in pasos:
        if not elegidos[clave]:
            return textos, seleccion
        objeto = modelo.objects.exclude(bloqueado='Si').filter(
            pk=_id(elegidos[clave], clave.capitalize()), **{fk: padre.pk},
        ).first()
        if objeto is None:
            raise ValidationError(error)
        seleccion[clave] = objeto.pk
        textos[CAMPO_TEXTO[clave]] = _texto(getattr(objeto, campo))
        padre = objeto

    hoja = padre
    if hoja.cantidad:
        textos['cantidad_hojas'] = str(hoja.cantidad)
    else:
        textos.pop('cantidad_hojas')  # El catálogo no la sabe: queda la que se cargó a mano.

    if elegidos['vidrio']:
        codigo = elegidos['vidrio']
        vidrio = Vidrio.objects.exclude(bloqueado='Si').filter(pk=codigo).first()
        if vidrio is None or codigo not in vidrios_de_hoja(hoja.pk):
            raise ValidationError('El vidrio no corresponde a la hoja.')
        seleccion['vidrio'] = vidrio.pk
        textos['tipo_vidrio'] = _texto(vidrio.descripcion)
    return textos, seleccion


def resolver_color(tratamiento_id):
    """(texto, id) del color elegido; ('', None) si se dejó sin terminación."""
    if not _texto(str(tratamiento_id or '')):
        return '', None
    tratamiento = Tratamiento.objects.exclude(bloqueado='Si').filter(pk=_id(tratamiento_id, 'Color')).first()
    if tratamiento is None:
        raise ValidationError('El color elegido no está en el catálogo.')
    return _texto(tratamiento.descripcion), tratamiento.pk


def seleccion_inicial(orden):
    """IDs para preseleccionar los desplegables.

    Primero lo guardado en la orden. Si no hay, los del ítem del presupuesto de origen, pero solo si
    la orden sigue diciendo lo mismo (en una estructura el ítem no es el módulo, y a mano se puede
    haber cambiado).
    """
    if orden.seleccion_catalogo:
        return {k: v for k, v in orden.seleccion_catalogo.items() if k in CLAVES}
    item = orden.item_presupuesto
    resultado = item.resultado_json if item is not None and isinstance(item.resultado_json, dict) else {}
    snapshot = resultado.get('snapshot_item') if isinstance(resultado.get('snapshot_item'), dict) else {}

    def entidad(clave):
        valor = snapshot.get(clave)
        return valor if isinstance(valor, dict) else {}

    if _texto(entidad('marco').get('descripcion')) != _texto(orden.tipo_marco) or not entidad('marco').get('id'):
        return {}
    seleccion = {}
    for clave in ('extrusora', 'linea', 'producto', 'marco', 'hoja', 'tratamiento'):
        if entidad(clave).get('id'):
            seleccion[clave] = entidad(clave)['id']
    if entidad('vidrio').get('codigo'):
        seleccion['vidrio'] = entidad('vidrio')['codigo']
    return seleccion
