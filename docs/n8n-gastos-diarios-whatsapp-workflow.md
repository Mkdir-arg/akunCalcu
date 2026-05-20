# Workflow n8n — Gastos Diarios por WhatsApp

> **Version**: 1.0
> **Estado**: Listo para importar y ajustar
> **Archivo JSON**: `docs/n8n-gastos-diarios-whatsapp-workflow.json`

## Que hace este workflow

1. Recibe un webhook de Evolution API con un audio o un texto de WhatsApp.
2. Si es audio, descarga el archivo y lo transcribe con Whisper.
3. GPT-4o-mini extrae una lista de gastos en formato `descripcion + monto`.
4. Django crea borradores en `gastos_diarios` usando el endpoint real del proyecto.
5. El workflow responde por WhatsApp con el resumen y pide confirmacion.
6. Si el usuario responde `SI`, los borradores pasan a estado `en_espera`.
7. Si el usuario responde `NO`, los borradores se eliminan.

## Endpoints Django reales que usa

Estos endpoints ya existen en el proyecto:

| Endpoint | Metodo | Uso |
|---|---|---|
| `http://web:8000/gastos-diarios/api/crear-borrador/` | `POST` | Crea gastos en estado `borrador` |
| `http://web:8000/gastos-diarios/api/confirmar/` | `POST` | Pasa borradores a `en_espera` o los elimina |

Si n8n no corre en la misma red interna que Django, reemplaza `http://web:8000` por la URL interna o publica correcta.

## Payload real esperado por Django

### Crear borrador

```json
{
  "numero_origen": "5491155555555",
  "audio_id": "ABCD-1234",
  "transcripcion": "cargame nafta quince mil y cafe dos mil quinientos",
  "gastos": [
    {
      "descripcion": "Nafta",
      "monto": 15000
    },
    {
      "descripcion": "Cafe",
      "monto": 2500
    }
  ]
}
```

### Confirmar o cancelar

```json
{
  "numero_origen": "5491155555555",
  "accion": "si"
}
```

Valores validos para `accion`: `si` o `no`.

## Antes de importar en n8n

1. Crea o reutiliza la credencial `OpenAI API` en n8n.
2. Reemplaza `REEMPLAZAR_EVOLUTION_API_KEY` por tu API key de Evolution.
3. Reemplaza `MI_INSTANCIA` por el nombre real de la instancia en Evolution API.
4. Reemplaza `X-Bot-Secret` si cambiaste el valor de `TELEGRAM_BOT_SECRET` en Django.
5. Configura Evolution para que el webhook apunte al path del nodo `Webhook Evolution`.
6. Asegurate de que el webhook de Evolution entregue una URL descargable del audio en alguno de estos campos: `data.mediaUrl`, `message.audioMessage.url` o equivalente.

## Webhook esperado desde Evolution

El nodo `Normalizar Evento` intenta adaptarse a estructuras comunes de Evolution y usa:

- `remoteJid` para detectar el numero de origen.
- `message.audioMessage` o `mediaUrl` para detectar audio.
- `conversation` o `extendedTextMessage.text` para respuestas `SI/NO`.

Si tu webhook llega con otro formato, ajusta solo el nodo `Normalizar Evento`.

## Archivo para importar

El JSON listo para importar esta en [docs/n8n-gastos-diarios-whatsapp-workflow.json](c:/Users/mkdir/Proyectos/akunCalcu/docs/n8n-gastos-diarios-whatsapp-workflow.json).

## Nota practica

No borre [docs/n8n-pedidos-workflow.md](c:/Users/mkdir/Proyectos/akunCalcu/docs/n8n-pedidos-workflow.md) porque documenta otra integracion ya implementada y referenciada por la feature de pedidos.# Workflow n8n — Gastos Diarios por WhatsApp

> Version: 1.0
> Estado: Listo para importar con ajustes de URLs y credenciales

## Que hace este workflow

1. Recibe un webhook desde Evolution API cuando entra un mensaje de WhatsApp.
2. Si el mensaje tiene audio, descarga el archivo y lo transcribe con Whisper.
3. GPT extrae una lista de gastos con `descripcion` y `monto`.
4. Django crea un borrador en `gastos_diarios` con estado `borrador`.
5. WhatsApp responde con un resumen y pide confirmacion: `SI` o `NO`.
6. Si el usuario responde `SI`, Django pasa esos borradores a `en_espera`.
7. Si responde `NO`, Django elimina los borradores.

## Archivo para importar

Importa este archivo en n8n:

`docs/n8n-gastos-diarios-whatsapp-workflow.json`

## Ajustes obligatorios antes de activarlo

Reemplaza estos valores en el workflow importado:

1. `https://TU_DJANGO_URL` por la URL real de Django.
2. `https://TU_EVOLUTION_URL` por la URL real de Evolution API.
3. `TU_INSTANCIA_EVOLUTION` por el nombre exacto de tu instancia en Evolution.
4. `REEMPLAZAR_CON_EVOLUTION_API_KEY` por tu API key de Evolution.
5. `REEMPLAZAR_CON_TELEGRAM_BOT_SECRET` por el mismo valor de `TELEGRAM_BOT_SECRET` usado por Django.
6. La credencial `OpenAI API` en los nodos de Whisper y GPT.

## Endpoints Django reales

Estos endpoints ya existen en el proyecto:

1. `POST /gastos-diarios/api/crear-borrador/`
2. `POST /gastos-diarios/api/confirmar/`

El token se valida con el header:

```text
X-Bot-Secret: <TELEGRAM_BOT_SECRET>
```

## Payload real para crear borrador

```json
{
  "numero_origen": "5491155555555",
  "audio_id": "ABCD1234",
  "transcripcion": "nafta veinte mil y peaje mil quinientos",
  "gastos": [
    {
      "descripcion": "Nafta",
      "monto": 20000
    },
    {
      "descripcion": "Peaje",
      "monto": 1500
    }
  ]
}
```

## Payload real para confirmar

```json
{
  "numero_origen": "5491155555555",
  "accion": "si"
}
```

o

```json
{
  "numero_origen": "5491155555555",
  "accion": "no"
}
```

## Suposiciones del workflow

El webhook de Evolution tiene que traer un payload donde pueda resolverse al menos esto:

1. Numero de origen.
2. Texto del mensaje cuando es una respuesta `SI` o `NO`.
3. URL del audio cuando el mensaje es de voz.
4. Un identificador del mensaje o audio.

El nodo `Normalizar Evento` ya intenta leer variantes comunes de Evolution, pero si tu payload viene con otra forma vas a tener que ajustar solo ese nodo.

## Recomendacion operativa

No borre el documento del workflow de pedidos por Telegram porque sigue siendo documentacion valida de una feature ya implementada. Este archivo nuevo queda separado para WhatsApp + gastos diarios.