"""Motor de conversación del agente.

Arma el contexto con la configuración real (firma, tono, canal, horario, base de conocimiento e
historial), pide al modelo una respuesta en JSON con forma fija y guarda las burbujas con su
«detrás de escena». En simulación las acciones solo se registran: nunca se ejecutan.
"""
import json

from django.utils import formats, timezone

from . import openai_cliente
from .horario import estado_horario
from .models import ConfiguracionAgente, Conversacion, EntradaConocimiento, Mensaje

MAX_HISTORIAL = 30

ACCION_NINGUNA = 'ninguna'
ACCIONES = {
    ACCION_NINGUNA: 'Ninguna',
    'derivar_direccion': 'Derivar a dirección',
    'derivar_visita_tecnica': 'Derivar a visita técnica',
}

SCHEMA_RESPUESTA = {
    'type': 'object',
    'additionalProperties': False,
    'required': ['mensajes', 'entradas_usadas', 'accion'],
    'properties': {
        'mensajes': {
            'type': 'array',
            'description': 'De 1 a 3 mensajes cortos, en el orden en que se envían.',
            'items': {'type': 'string'},
        },
        'entradas_usadas': {
            'type': 'array',
            'description': 'Números de las entradas de la base de conocimiento usadas en la respuesta.',
            'items': {'type': 'integer'},
        },
        'accion': {
            'type': 'object',
            'additionalProperties': False,
            'required': ['tipo', 'motivo'],
            'properties': {
                'tipo': {'type': 'string', 'enum': list(ACCIONES)},
                'motivo': {'type': 'string'},
            },
        },
    },
}

ESTILO_POR_CANAL = {
    Conversacion.CANAL_WHATSAPP: (
        'Es WhatsApp: mensajes cortos y naturales, como los escribe una persona desde el celular. '
        'Podés partir la respuesta en hasta 3 mensajes. Sin firma al final.'
    ),
    Conversacion.CANAL_INSTAGRAM: (
        'Es un mensaje directo de Instagram: corto, cercano, hasta 3 mensajes. Sin firma al final.'
    ),
    Conversacion.CANAL_EMAIL: (
        'Es un email: un solo mensaje, con saludo, párrafos breves y la firma al final.'
    ),
}


def momento_de(conversacion):
    return conversacion.fecha_hora_simulada or timezone.now()


def _texto_momento(momento):
    local = timezone.localtime(momento)
    return formats.date_format(local, 'l j \\d\\e F \\d\\e Y, H:i')


def _texto_horario(estado):
    if not estado.hay_horario:
        return 'No hay horario de atención cargado.'
    if estado.abierto:
        return 'Estamos dentro del horario de atención.'
    partes = ['Estamos fuera del horario de atención.']
    if estado.dia_cerrado:
        partes.append(f'Hoy está cerrado ({estado.dia_cerrado.motivo or "día cerrado"}).')
    if estado.proxima_apertura:
        partes.append(f'Próxima apertura: {_texto_momento(estado.proxima_apertura)}.')
    return ' '.join(partes)


def armar_prompt_sistema(config, conversacion, estado, entradas):
    lineas = [
        f'Sos {config.nombre_firma}, de Akun Aberturas (aberturas de aluminio y PVC). '
        'Atendés a clientes que escriben para consultar, pedir presupuestos o saber de sus pedidos.',
        'Escribís en español rioplatense, con voseo, como una persona real del equipo: cálido, '
        'claro y concreto, sin listas largas ni exceso de emojis.',
        ESTILO_POR_CANAL.get(conversacion.canal, ''),
    ]
    if config.instrucciones_tono.strip():
        lineas.append(f'Indicaciones de tono de Akun: {config.instrucciones_tono.strip()}')
    if conversacion.nombre_contacto:
        lineas.append(f'El cliente se llama {conversacion.nombre_contacto}.')
    lineas.append(f'Momento actual: {_texto_momento(momento_de(conversacion))}. {_texto_horario(estado)}')

    lineas.append(
        'Reglas: solo afirmás datos que estén en la base de conocimiento de abajo. Si te preguntan algo '
        'que no está, no lo inventes: decí que lo consultás y usá la acción derivar_direccion. '
        'No des precios ni plazos que no estén en la base. Si el cliente pide una medición o visita, '
        'usá derivar_visita_tecnica. Si se enoja, reclama o pide hablar con una persona, usá '
        'derivar_direccion. Si te preguntan directamente si sos un bot o una IA, no lo niegues.'
    )

    if entradas:
        lineas.append('Base de conocimiento (citá en entradas_usadas los números que uses):')
        for entrada in entradas:
            lineas.append(f'[{entrada.pk}] {entrada.tema}: {entrada.contenido}')
    else:
        lineas.append('La base de conocimiento está vacía.')
    return '\n\n'.join(linea for linea in lineas if linea)


def armar_mensajes(conversacion, config, estado, entradas):
    mensajes = [{'role': 'system', 'content': armar_prompt_sistema(config, conversacion, estado, entradas)}]
    historial = list(
        conversacion.mensajes.exclude(rol=Mensaje.ROL_SISTEMA).order_by('-created_at', '-pk')[:MAX_HISTORIAL]
    )
    for mensaje in reversed(historial):
        rol = 'user' if mensaje.rol == Mensaje.ROL_CLIENTE else 'assistant'
        mensajes.append({'role': rol, 'content': mensaje.texto})
    return mensajes


def _interpretar(contenido, entradas_por_pk):
    """Convierte el JSON del modelo en (burbujas, detalle). Tolera respuestas fuera de formato."""
    try:
        datos = json.loads(contenido)
        burbujas = [str(m).strip() for m in datos['mensajes'] if str(m).strip()][:3]
        accion = datos['accion']
        tipo = accion.get('tipo') if accion.get('tipo') in ACCIONES else ACCION_NINGUNA
        usadas = [pk for pk in datos.get('entradas_usadas', []) if pk in entradas_por_pk]
        detalle = {
            'entradas_usadas': [{'id': pk, 'tema': entradas_por_pk[pk]} for pk in usadas],
            'accion': tipo,
            'accion_texto': ACCIONES[tipo],
            'motivo': str(accion.get('motivo', '')).strip(),
        }
        if not burbujas:
            raise ValueError('sin mensajes')
        return burbujas, detalle
    except (ValueError, KeyError, TypeError, AttributeError):
        texto = (contenido or '').strip() or '(respuesta vacía)'
        return [texto], {'formato_invalido': True, 'accion': ACCION_NINGUNA, 'accion_texto': ACCIONES[ACCION_NINGUNA]}


def responder(conversacion, texto_cliente):
    """Registra el mensaje del cliente, pide la respuesta al modelo y devuelve los mensajes nuevos."""
    config = ConfiguracionAgente.obtener()
    nuevos = [Mensaje.objects.create(conversacion=conversacion, rol=Mensaje.ROL_CLIENTE, texto=texto_cliente)]

    estado = estado_horario(momento_de(conversacion))
    if not estado.abierto:
        if estado.proxima_apertura:
            nota = f'Fuera de horario: en un canal real esta respuesta saldría el {_texto_momento(estado.proxima_apertura)}.'
        elif estado.hay_horario:
            nota = 'Fuera de horario y sin próxima apertura en las próximas semanas.'
        else:
            nota = 'No hay horario de atención cargado: en un canal real no se sabría cuándo responder.'
        nuevos.append(Mensaje.objects.create(conversacion=conversacion, rol=Mensaje.ROL_SISTEMA, texto=nota))

    entradas = list(EntradaConocimiento.objects.filter(activo=True))
    mensajes = armar_mensajes(conversacion, config, estado, entradas)
    try:
        contenido, uso = openai_cliente.pedir_json(config.modelo_ia, mensajes, 'respuesta_agente', SCHEMA_RESPUESTA)
    except openai_cliente.OpenAIError as exc:
        nuevos.append(Mensaje.objects.create(
            conversacion=conversacion, rol=Mensaje.ROL_SISTEMA, texto=str(exc),
            detalle={'error': True, 'modelo': config.modelo_ia},
        ))
        conversacion.save(update_fields=['updated_at'])
        return nuevos

    burbujas, detalle = _interpretar(contenido, {e.pk: e.tema for e in entradas})
    detalle.update({
        'modelo': config.modelo_ia,
        'tokens_entrada': uso.get('prompt_tokens'),
        'tokens_salida': uso.get('completion_tokens'),
        'simulacion': conversacion.es_simulacion,
    })
    for indice, burbuja in enumerate(burbujas):
        nuevos.append(Mensaje.objects.create(
            conversacion=conversacion, rol=Mensaje.ROL_ASISTENTE, texto=burbuja,
            detalle=detalle if indice == len(burbujas) - 1 else {},
        ))
    conversacion.save(update_fields=['updated_at'])
    return nuevos
