"""Llamada mínima a la API de OpenAI (Chat Completions) con salida JSON estructurada.

Sin SDK: usa urllib, igual que core/whatsapp.py. La API key se lee de OPENAI_API_KEY.
"""
import json
import os
from urllib import error, request

URL = 'https://api.openai.com/v1/chat/completions'
TIMEOUT_SEGUNDOS = 25


class OpenAIError(Exception):
    """Error al pedir una respuesta al modelo; el mensaje es apto para mostrar al usuario."""


class OpenAINoConfigurado(OpenAIError):
    pass


def _admite_reasoning_effort(modelo):
    return modelo.startswith(('gpt-5', 'o1', 'o3', 'o4'))


def pedir_json(modelo, mensajes, nombre_schema, schema):
    """Devuelve (contenido_json_como_texto, uso) o levanta OpenAIError."""
    api_key = os.environ.get('OPENAI_API_KEY', '').strip()
    if not api_key:
        raise OpenAINoConfigurado('Falta configurar la API key de OpenAI (variable OPENAI_API_KEY).')

    cuerpo = {
        'model': modelo,
        'messages': mensajes,
        'response_format': {
            'type': 'json_schema',
            'json_schema': {'name': nombre_schema, 'strict': True, 'schema': schema},
        },
    }
    if _admite_reasoning_effort(modelo):
        cuerpo['reasoning_effort'] = 'low'

    req = request.Request(
        URL,
        data=json.dumps(cuerpo).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {api_key}'},
        method='POST',
    )
    try:
        with request.urlopen(req, timeout=TIMEOUT_SEGUNDOS) as respuesta:
            datos = json.loads(respuesta.read().decode('utf-8'))
    except error.HTTPError as exc:
        detalle = ''
        try:
            detalle = json.loads(exc.read().decode('utf-8')).get('error', {}).get('message', '')
        except (ValueError, AttributeError):
            pass
        raise OpenAIError(f'OpenAI respondió con error {exc.code}. {detalle}'.strip()) from exc
    except (error.URLError, TimeoutError) as exc:
        raise OpenAIError('No se pudo conectar con OpenAI o tardó demasiado en responder.') from exc
    except ValueError as exc:
        raise OpenAIError('OpenAI devolvió una respuesta ilegible.') from exc

    try:
        mensaje = datos['choices'][0]['message']
    except (KeyError, IndexError, TypeError) as exc:
        raise OpenAIError('OpenAI devolvió una respuesta sin contenido.') from exc
    if mensaje.get('refusal'):
        raise OpenAIError(f"El modelo se negó a responder: {mensaje['refusal']}")
    return mensaje.get('content') or '', datos.get('usage') or {}
