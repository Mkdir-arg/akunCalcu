# Workflow n8n — Gastos Diarios por WhatsApp (v2, Meta Cloud API)

> **Versión**: 2.0 (2026-10-30, FIX-026)
> **Workflow en n8n**: `VfdJhVTZmKj7HoES` — "WhatsApp Gastos Diarios AkunCalcu v2 (Meta Cloud API)"
> **Archivo JSON**: `docs/n8n/n8n-gastos-diarios-whatsapp-workflow.json` (copia exacta de lo publicado)
> **Reemplaza a**: v1 (Evolution API). Evolution se dio de baja el 2026-08-28 y el bot quedó sin entrada.

## Qué hace

1. Meta (WhatsApp Cloud API) llama al webhook `gastos-diarios-whatsapp` cada vez que
   el número de Akun recibe un mensaje **o** cambia el estado de un mensaje enviado.
2. Si es un **audio**: baja el `.ogg` por la Graph API, lo transcribe con Whisper y, si no había
   un borrador pendiente, GPT-4o-mini extrae los gastos (`descripcion + monto + tipo`).
3. Django crea los borradores (`/gastos-diarios/api/crear-borrador/`) y devuelve el próximo
   mensaje conversacional (pregunta el tipo o pide confirmación).
4. Si es **texto** (o un audio cuando ya hay borrador): va a `/gastos-diarios/api/responder/`,
   que lo interpreta como tipo de cuenta o como SI/NO.
5. La respuesta vuelve por WhatsApp como texto libre (válido: la persona nos acaba de escribir,
   ventana de 24 h de Meta).
6. Si Meta avisa que un mensaje saliente **falló** (`statuses[].status = failed`), el evento
   termina en el nodo **"Fallo de Envio"**, que lo manda a Django
   (`/security/salud/api/fallo-whatsapp/`). Django lo guarda en `FalloEnvioWhatsApp`, avisa al
   staff en la campana y lo muestra en `/security/salud/` («Envíos de WhatsApp»). Esto cubre
   también los recordatorios de agenda y de solicitudes, que antes fallaban en silencio.

## Variables de entorno (servicio n8n en Railway)

| Variable | Uso |
|---|---|
| `META_WA_TOKEN` | Token permanente del System User `akunbot-admin` (ya existe, lo usa la agenda) |
| `META_PHONE_NUMBER_ID` | `1119452454594540` = +54 9 11 3929-0550 (ya existe). Filtra los eventos del número de prueba |
| `META_VERIFY_TOKEN` | Opcional. Si no está, el workflow usa `akuna-gastos-2026` |
| `AKUNACALCU_WEB_URL` | URL pública de Django (ya existe) |
| `TELEGRAM_BOT_SECRET` | Mismo valor que en Django; va en el header `X-Bot-Secret` (ya existe) |

## Configuración en Meta (una sola vez)

En <https://developers.facebook.com> → la app de WhatsApp → **WhatsApp → Configuración → Webhook**:

1. **URL de devolución de llamada**: `https://n8n-production-9a1a.up.railway.app/webhook/gastos-diarios-whatsapp`
2. **Token de verificación**: `akuna-gastos-2026` (o el valor de `META_VERIFY_TOKEN` si se definió)
3. **Verificar y guardar** → Meta hace un GET y el workflow responde el `hub.challenge`.
4. En **Campos del webhook**, suscribirse a `messages` (es el único campo necesario; los
   estados de entrega llegan por el mismo campo).

El workflow tiene que estar **publicado** en n8n antes del paso 3, si no el GET devuelve 404.

## Payload que llega de Meta

```json
{
  "object": "whatsapp_business_account",
  "entry": [{ "changes": [{ "field": "messages", "value": {
    "metadata": { "phone_number_id": "1119452454594540" },
    "contacts": [{ "wa_id": "5491155555555", "profile": { "name": "Dario" } }],
    "messages": [{ "from": "5491155555555", "id": "wamid...", "type": "audio",
                   "audio": { "id": "1234567890", "mime_type": "audio/ogg; codecs=opus" } }]
  }}]}]
}
```

Para texto viene `"type": "text", "text": { "body": "si" }`. Para estados viene
`"statuses": [{ "id": "wamid...", "status": "failed", "recipient_id": "549...", "errors": [...] }]`.

El nodo `Normalizar Evento` es el único que conoce esta forma; si Meta cambia el payload,
se ajusta solo ese nodo.

## Nodos

| Nodo | Qué hace |
|---|---|
| Webhook Verificacion Meta (GET) | Responde el `hub.challenge` si el `hub.verify_token` coincide; 403 si no |
| Webhook Meta (POST) | Recibe eventos; responde 200 al instante (Meta reintenta si tarda) |
| Normalizar Evento | Aplana `entry/changes/value` a un item por mensaje o por envío fallido |
| Es Mensaje | Mensajes → flujo normal; fallos de envío → "Fallo de Envio" |
| IF Audio | Audio → transcripción; texto → respuesta conversacional |
| Obtener URL Audio / Descargar Audio | `GET /v21.0/{media_id}` → `GET url` con Bearer (la url vence a los 5 min) |
| Transcribe Audio | Whisper (credencial OpenAI de n8n), idioma `es` |
| Responder Audio → IF Manejado | Si había borrador, el audio se trata como respuesta y no se extraen gastos |
| Parsear Gastos GPT → Procesar JSON Gastos → IF Hay Gastos | Extrae gastos; si no hay, "WhatsApp Reintentar" |
| Crear Borrador Django → Armar Resumen → WhatsApp Enviar Resumen | Crea borradores y manda el resumen |
| Normalizar Respuesta → Responder Django → WhatsApp Responder | Rama de texto |

Los envíos por WhatsApp usan `POST https://graph.facebook.com/v21.0/{META_PHONE_NUMBER_ID}/messages`
con `type: 'text'`. Los nodos de descarga, transcripción y envío tienen `onError: continueRegularOutput`
para que una falla termine en un "No pude transcribir el audio" y no en silencio.
`Responder Django` y `Crear Borrador Django` **no** lo tienen a propósito: un número no autorizado
(403) corta la ejecución sin responderle nada.

## Endpoints Django

| Endpoint | Método | Uso |
|---|---|---|
| `/gastos-diarios/api/crear-borrador/` | `POST` | Crea gastos en estado `borrador`, devuelve `mensaje` |
| `/gastos-diarios/api/responder/` | `POST` | Interpreta texto (tipo o SI/NO), devuelve `manejado` y `mensaje` |
| `/gastos-diarios/api/confirmar/` | `POST` | Alternativa directa con `accion: si/no` (no la usa el workflow) |
| `/security/salud/api/fallo-whatsapp/` | `POST` | Registra un mensaje no entregado (`message_id`, `numero_destino`, `errores`). Valida `X-Bot-Secret` contra `HEALTH_BOT_SECRET`, no contra el de Telegram |

Todos validan el header `X-Bot-Secret` contra `TELEGRAM_BOT_SECRET` y que `numero_origen`
esté en `NumeroAutorizado` activo. `numero_origen` es el `wa_id` de Meta (ej. `5491155555555`,
mismo formato que usaba Evolution).

## Cómo verificar que anda

1. Ejecuciones del workflow en n8n: tiene que aparecer una por cada mensaje recibido.
2. Audio de prueba desde un número autorizado → llega el resumen con los gastos y la pregunta.
3. Responder `SI` → "Listo. Tus gastos quedaron cargados..." y el gasto aparece en
   `/gastos-diarios/` con estado *En espera*.
4. Si un recordatorio de agenda no llega, mirar «Envíos de WhatsApp» en `/security/salud/` o el
   admin de *Fallos de envío de WhatsApp*.

## Historial

- **v1 (2026-05)**: entrada y salida por Evolution API (`/webhook/meta` de Evolution → n8n).
- **2026-08-28**: Evolution dada de baja; los envíos de agenda pasaron a Meta directo, pero la
  entrada de este bot quedó rota (0 ejecuciones).
- **v2 (2026-10-30, FIX-026)**: entrada y salida por Meta Cloud API directo; registro de envíos fallidos.
