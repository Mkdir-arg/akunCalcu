"""Envío de plantillas de WhatsApp con documento adjunto, directo a la Cloud API de Meta (REQ-057).

Meta solo entrega texto libre dentro de las 24 h en que la persona escribió; fuera de esa ventana
exige una plantilla aprobada. Por eso el PDF viaja como encabezado DOCUMENT de una plantilla.
"""
import json
import os
import re
import uuid
from urllib import error, request

GRAPH_URL = 'https://graph.facebook.com'
TIMEOUT_SEGUNDOS = 20


class EnvioWhatsAppError(Exception):
    pass


class WhatsAppNoConfigurado(EnvioWhatsAppError):
    pass


def _config():
    token = os.environ.get('META_WA_TOKEN', '').strip()
    phone_id = os.environ.get('META_PHONE_NUMBER_ID', '').strip()
    if not token or not phone_id:
        raise WhatsAppNoConfigurado('El envío por WhatsApp no está configurado (faltan META_WA_TOKEN o META_PHONE_NUMBER_ID).')
    version = os.environ.get('META_WA_API_VERSION', 'v21.0').strip() or 'v21.0'
    return token, phone_id, f'{GRAPH_URL}/{version}'


def esta_configurado():
    try:
        _config()
    except WhatsAppNoConfigurado:
        return False
    return True


def _post(url, token, body, content_type):
    req = request.Request(url, data=body, method='POST', headers={
        'Authorization': f'Bearer {token}',
        'Content-Type': content_type,
    })
    try:
        with request.urlopen(req, timeout=TIMEOUT_SEGUNDOS) as respuesta:
            return json.loads(respuesta.read().decode('utf-8') or '{}')
    except error.HTTPError as exc:
        try:
            detalle = json.loads(exc.read().decode('utf-8')).get('error', {})
            mensaje = detalle.get('error_user_msg') or detalle.get('message') or str(exc)
            codigo = detalle.get('code')
        except (ValueError, AttributeError):
            mensaje, codigo = str(exc), None
        raise EnvioWhatsAppError(f'Meta rechazó el envío{f" ({codigo})" if codigo else ""}: {mensaje}') from exc
    except (error.URLError, TimeoutError) as exc:
        raise EnvioWhatsAppError(f'No se pudo conectar con WhatsApp: {exc}') from exc


def subir_pdf(contenido, nombre_archivo):
    """Sube el PDF a Meta y devuelve el media id (vale 30 días; se reutiliza para varios destinatarios)."""
    token, phone_id, base = _config()
    limite = uuid.uuid4().hex
    partes = [
        f'--{limite}\r\nContent-Disposition: form-data; name="messaging_product"\r\n\r\nwhatsapp\r\n'.encode(),
        f'--{limite}\r\nContent-Disposition: form-data; name="type"\r\n\r\napplication/pdf\r\n'.encode(),
        (f'--{limite}\r\nContent-Disposition: form-data; name="file"; filename="{nombre_archivo}"\r\n'
         'Content-Type: application/pdf\r\n\r\n').encode() + contenido + b'\r\n',
        f'--{limite}--\r\n'.encode(),
    ]
    respuesta = _post(f'{base}/{phone_id}/media', token, b''.join(partes), f'multipart/form-data; boundary={limite}')
    media_id = respuesta.get('id')
    if not media_id:
        raise EnvioWhatsAppError('Meta no devolvió el id del archivo subido.')
    return media_id


def _limpiar_parametro(valor):
    # Meta rechaza parámetros de plantilla con saltos de línea, tabs o más de 4 espacios seguidos.
    return re.sub(r'\s+', ' ', str(valor or '')).strip() or '-'


def enviar_plantilla_documento(numero, plantilla, idioma, media_id, nombre_archivo, parametros):
    """Envía la plantilla con el documento en el encabezado. Devuelve el id del mensaje de Meta."""
    token, phone_id, base = _config()
    cuerpo = {
        'messaging_product': 'whatsapp',
        'to': re.sub(r'\D', '', numero),
        'type': 'template',
        'template': {
            'name': plantilla,
            'language': {'code': idioma},
            'components': [
                {'type': 'header', 'parameters': [
                    {'type': 'document', 'document': {'id': media_id, 'filename': nombre_archivo}},
                ]},
                {'type': 'body', 'parameters': [
                    {'type': 'text', 'text': _limpiar_parametro(valor)} for valor in parametros
                ]},
            ],
        },
    }
    respuesta = _post(f'{base}/{phone_id}/messages', token, json.dumps(cuerpo).encode('utf-8'), 'application/json')
    mensajes = respuesta.get('messages') or [{}]
    return mensajes[0].get('id', '')
