# Workflow n8n — Bot de Pedidos por Voz

> **Versión**: 2.0
> **Estado**: Listo para importar
> **Reemplaza**: Bot Telegram Audio Transcripción v1.0

---

## Qué hace este workflow

1. Usuario envía un **audio de voz** a @Akun_aberturas_bot describiendo su pedido
2. n8n transcribe el audio con **Whisper** (OpenAI)
3. **GPT-4o-mini** extrae los ítems del texto en formato estructurado
4. Django crea un **borrador** del pedido en la base de datos
5. El bot le devuelve al usuario el resumen y le pregunta: **"¿Confirmás? Respondé SÍ o NO"**
6. El usuario responde **SÍ** → el pedido queda confirmado en AkunCalcu
7. El usuario responde **NO** → el pedido queda cancelado

---

## Antes de importar: configurá las credenciales en n8n

1. **Telegram API** → ya la tenés configurada de v1.0
2. **OpenAI API** → ya la tenés configurada de v1.0
3. En el nodo **"Crear Borrador Django"** y **"Confirmar Pedido Django"**, reemplazá el header `X-Bot-Secret` con el valor `akuna-bot-secret-2024` (el mismo que está en docker-compose.yml)

---

## Diagrama del flujo

```
[Telegram Trigger]
        |
[IF: ¿Es audio?]
    |           |
   SÍ           NO
    |            |
[Get File]    [Code: Normalizar texto]
[Download]       |
[Transcribe]  [IF: ¿Es SÍ o NO?]
[GPT Parse]      |           |
[HTTP: crear]   SÍ           NO (ignorar)
[Telegram:       |
 resumen]    [HTTP: confirmar]
                 |
           [IF: ¿Confirmado?]
              |         |
             SÍ         NO
              |          |
         [Telegram:  [Telegram:
          confirmado] cancelado]
```

---

## JSON del Workflow — Copiar y pegar en n8n

> **Cómo importar**: n8n → menú (☰) → Import from JSON → pegar el JSON de abajo

```json
{
  "name": "Bot Telegram Pedidos AkunCalcu v2",
  "nodes": [
    {
      "parameters": {
        "updates": ["message"]
      },
      "id": "telegram-trigger",
      "name": "Telegram Trigger",
      "type": "n8n-nodes-base.telegramTrigger",
      "typeVersion": 1.2,
      "position": [200, 400],
      "credentials": {
        "telegramApi": {
          "id": "1",
          "name": "Telegram API"
        }
      }
    },
    {
      "parameters": {
        "conditions": {
          "options": {
            "caseSensitive": false,
            "leftValue": "",
            "typeValidation": "loose"
          },
          "conditions": [
            {
              "id": "cond-voice",
              "leftValue": "={{ $json.message.voice?.file_id ?? $json.message.audio?.file_id ?? '' }}",
              "rightValue": "",
              "operator": {
                "type": "string",
                "operation": "isNotEmpty"
              }
            }
          ],
          "combinator": "and"
        }
      },
      "id": "if-audio",
      "name": "IF Audio",
      "type": "n8n-nodes-base.if",
      "typeVersion": 2,
      "position": [420, 400]
    },
    {
      "parameters": {
        "resource": "file",
        "operation": "get",
        "fileId": "={{ $('Telegram Trigger').item.json.message.voice?.file_id ?? $('Telegram Trigger').item.json.message.audio?.file_id }}"
      },
      "id": "get-file-info",
      "name": "Get File Info",
      "type": "n8n-nodes-base.telegram",
      "typeVersion": 1.2,
      "position": [640, 260],
      "credentials": {
        "telegramApi": {
          "id": "1",
          "name": "Telegram API"
        }
      }
    },
    {
      "parameters": {
        "url": "=https://api.telegram.org/file/bot{{ $credentials.telegramApi.accessToken }}/{{ $json.result.file_path }}",
        "options": {
          "response": {
            "response": {
              "responseFormat": "file"
            }
          }
        }
      },
      "id": "download-audio",
      "name": "Download Audio",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.2,
      "position": [860, 260]
    },
    {
      "parameters": {
        "resource": "audio",
        "operation": "transcribe",
        "binaryPropertyName": "data",
        "options": {
          "language": "es"
        }
      },
      "id": "transcribe-audio",
      "name": "Transcribe Audio",
      "type": "@n8n/n8n-nodes-langchain.openAi",
      "typeVersion": 2.1,
      "position": [1080, 260],
      "credentials": {
        "openAiApi": {
          "id": "2",
          "name": "OpenAI API"
        }
      }
    },
    {
      "parameters": {
        "resource": "text",
        "operation": "message",
        "modelId": {
          "__rl": true,
          "value": "gpt-4o-mini",
          "mode": "list"
        },
        "messages": {
          "values": [
            {
              "content": "=Eres un asistente que extrae ítems de pedidos de aberturas (ventanas, puertas, persianas, etc.).\n\nAnaliza el siguiente texto y devuelve ÚNICAMENTE un JSON array. Cada elemento debe tener:\n- \"descripcion\": string con la descripción del producto\n- \"cantidad\": número entero (si no se menciona cantidad, usar 1)\n\nTexto: {{ $json.text }}\n\nResponde SOLO con el JSON array, sin texto adicional, sin markdown, sin ```json.\nEjemplo de respuesta válida: [{\"descripcion\":\"Ventana corrediza aluminio\",\"cantidad\":3},{\"descripcion\":\"Puerta vidrio templado\",\"cantidad\":1}]"
            }
          ]
        },
        "options": {}
      },
      "id": "parsear-items-gpt",
      "name": "Parsear Items GPT",
      "type": "@n8n/n8n-nodes-langchain.openAi",
      "typeVersion": 2.1,
      "position": [1300, 260],
      "credentials": {
        "openAiApi": {
          "id": "2",
          "name": "OpenAI API"
        }
      }
    },
    {
      "parameters": {
        "jsCode": "// Obtener la transcripción original y el texto del GPT\nconst transcripcion = $('Transcribe Audio').item.json.text;\nconst gptRespuesta = $input.item.json.message.content;\n\nlet items = [];\ntry {\n  items = JSON.parse(gptRespuesta);\n} catch(e) {\n  // Si el JSON falla, crear un item con el texto completo\n  items = [{ descripcion: transcripcion, cantidad: 1 }];\n}\n\n// Obtener datos del usuario de Telegram\nconst mensaje = $('Telegram Trigger').item.json.message;\nconst chatId = mensaje.chat.id;\nconst username = mensaje.from.username || mensaje.from.first_name || '';\n\nreturn [{\n  json: {\n    chat_id: chatId,\n    telegram_username: username,\n    transcripcion: transcripcion,\n    items: items\n  }\n}];"
      },
      "id": "procesar-json",
      "name": "Procesar JSON Items",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [1520, 260]
    },
    {
      "parameters": {
        "method": "POST",
        "url": "http://web:8000/pedidos/api/crear-borrador/",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            {
              "name": "Content-Type",
              "value": "application/json"
            },
            {
              "name": "X-Bot-Secret",
              "value": "akuna-bot-secret-2024"
            }
          ]
        },
        "sendBody": true,
        "specifyBody": "json",
        "jsonBody": "={{ JSON.stringify($json) }}",
        "options": {}
      },
      "id": "crear-borrador-django",
      "name": "Crear Borrador Django",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.2,
      "position": [1740, 260]
    },
    {
      "parameters": {
        "chatId": "={{ $('Telegram Trigger').item.json.message.chat.id }}",
        "text": "=🛒 *Tu pedido tiene {{ $json.total_items }} ítem(s):*\n\n{{ $json.items_texto }}\n\n¿Confirmás el pedido? Respondé *SÍ* para confirmar o *NO* para cancelar.",
        "additionalFields": {
          "parse_mode": "Markdown"
        }
      },
      "id": "enviar-resumen",
      "name": "Enviar Resumen",
      "type": "n8n-nodes-base.telegram",
      "typeVersion": 1.2,
      "position": [1960, 260],
      "credentials": {
        "telegramApi": {
          "id": "1",
          "name": "Telegram API"
        }
      }
    },
    {
      "parameters": {
        "jsCode": "// Normalizar texto de respuesta\nconst mensaje = $('Telegram Trigger').item.json.message;\nconst texto = (mensaje.text || '').toLowerCase().trim();\nconst chatId = mensaje.chat.id;\n\nlet accion = 'otro';\nif (['si', 'sí', 'yes', 's'].includes(texto)) {\n  accion = 'si';\n} else if (['no', 'n'].includes(texto)) {\n  accion = 'no';\n}\n\nreturn [{\n  json: {\n    chat_id: chatId,\n    accion: accion,\n    texto_original: texto\n  }\n}];"
      },
      "id": "normalizar-texto",
      "name": "Normalizar Texto",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [640, 560]
    },
    {
      "parameters": {
        "conditions": {
          "options": {
            "caseSensitive": false,
            "leftValue": "",
            "typeValidation": "loose"
          },
          "conditions": [
            {
              "id": "cond-sino",
              "leftValue": "={{ $json.accion }}",
              "rightValue": "otro",
              "operator": {
                "type": "string",
                "operation": "notEquals"
              }
            }
          ],
          "combinator": "and"
        }
      },
      "id": "if-si-no",
      "name": "IF Si o No",
      "type": "n8n-nodes-base.if",
      "typeVersion": 2,
      "position": [860, 560]
    },
    {
      "parameters": {
        "method": "POST",
        "url": "http://web:8000/pedidos/api/confirmar/",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            {
              "name": "Content-Type",
              "value": "application/json"
            },
            {
              "name": "X-Bot-Secret",
              "value": "akuna-bot-secret-2024"
            }
          ]
        },
        "sendBody": true,
        "specifyBody": "json",
        "jsonBody": "={{ JSON.stringify({ chat_id: $json.chat_id, accion: $json.accion }) }}",
        "options": {}
      },
      "id": "confirmar-django",
      "name": "Confirmar Pedido Django",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.2,
      "position": [1080, 560]
    },
    {
      "parameters": {
        "conditions": {
          "options": {
            "caseSensitive": false,
            "leftValue": "",
            "typeValidation": "loose"
          },
          "conditions": [
            {
              "id": "cond-confirmado",
              "leftValue": "={{ $json.estado }}",
              "rightValue": "confirmado",
              "operator": {
                "type": "string",
                "operation": "equals"
              }
            }
          ],
          "combinator": "and"
        }
      },
      "id": "if-confirmado",
      "name": "IF Confirmado",
      "type": "n8n-nodes-base.if",
      "typeVersion": 2,
      "position": [1300, 560]
    },
    {
      "parameters": {
        "chatId": "={{ $('Normalizar Texto').item.json.chat_id }}",
        "text": "=✅ *Pedido #{{ $json.pedido_id }} confirmado.*\n\nQuedó registrado en el sistema. ¡Gracias!",
        "additionalFields": {
          "parse_mode": "Markdown"
        }
      },
      "id": "telegram-confirmado",
      "name": "Telegram Confirmado",
      "type": "n8n-nodes-base.telegram",
      "typeVersion": 1.2,
      "position": [1520, 460],
      "credentials": {
        "telegramApi": {
          "id": "1",
          "name": "Telegram API"
        }
      }
    },
    {
      "parameters": {
        "chatId": "={{ $('Normalizar Texto').item.json.chat_id }}",
        "text": "❌ *Pedido cancelado.*\n\nSi querés hacer un nuevo pedido, enviá un audio de voz.",
        "additionalFields": {
          "parse_mode": "Markdown"
        }
      },
      "id": "telegram-cancelado",
      "name": "Telegram Cancelado",
      "type": "n8n-nodes-base.telegram",
      "typeVersion": 1.2,
      "position": [1520, 660],
      "credentials": {
        "telegramApi": {
          "id": "1",
          "name": "Telegram API"
        }
      }
    }
  ],
  "connections": {
    "Telegram Trigger": {
      "main": [
        [
          {
            "node": "IF Audio",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "IF Audio": {
      "main": [
        [
          {
            "node": "Get File Info",
            "type": "main",
            "index": 0
          }
        ],
        [
          {
            "node": "Normalizar Texto",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Get File Info": {
      "main": [
        [
          {
            "node": "Download Audio",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Download Audio": {
      "main": [
        [
          {
            "node": "Transcribe Audio",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Transcribe Audio": {
      "main": [
        [
          {
            "node": "Parsear Items GPT",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Parsear Items GPT": {
      "main": [
        [
          {
            "node": "Procesar JSON Items",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Procesar JSON Items": {
      "main": [
        [
          {
            "node": "Crear Borrador Django",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Crear Borrador Django": {
      "main": [
        [
          {
            "node": "Enviar Resumen",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Normalizar Texto": {
      "main": [
        [
          {
            "node": "IF Si o No",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "IF Si o No": {
      "main": [
        [
          {
            "node": "Confirmar Pedido Django",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Confirmar Pedido Django": {
      "main": [
        [
          {
            "node": "IF Confirmado",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "IF Confirmado": {
      "main": [
        [
          {
            "node": "Telegram Confirmado",
            "type": "main",
            "index": 0
          }
        ],
        [
          {
            "node": "Telegram Cancelado",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  },
  "settings": {
    "executionOrder": "v1"
  }
}
```

---

## Importante: ajustar IDs de credenciales

En el JSON de arriba las credenciales tienen `"id": "1"` (Telegram) y `"id": "2"` (OpenAI).
Si en tu n8n las credenciales tienen otros IDs, tenés dos opciones:

**Opción A (recomendada):** Importar el JSON y luego hacer clic en cada nodo que use credenciales → seleccionar manualmente la credencial correcta desde el dropdown.

**Opción B:** Antes de importar, ir a n8n → Settings → Credentials → ver el ID real de cada credencial y reemplazarlo en el JSON.

---

## URL de Django que usa n8n

| Endpoint | Método | Qué hace |
|----------|--------|----------|
| `http://web:8000/pedidos/api/crear-borrador/` | POST | Crea el pedido en estado "pendiente" |
| `http://web:8000/pedidos/api/confirmar/` | POST | Confirma o cancela el pedido |

> `web` es el nombre del servicio Django en Docker. Si n8n corre fuera de Docker, usar `http://localhost:8080` en vez de `http://web:8000`.

---

## Token de autenticación

Todos los llamados de n8n a Django llevan el header:

```
X-Bot-Secret: akuna-bot-secret-2024
```

Este valor está configurado en `docker-compose.yml` como variable de entorno `TELEGRAM_BOT_SECRET` del servicio `web`.
Si lo cambiás en docker-compose, cambialo también en los nodos de n8n.

---

## Ejemplo de conversación completa

```
Usuario: 🎤 [audio] "Quiero 3 ventanas corredizas de aluminio y 2 puertas de vidrio"

Bot:     🛒 Tu pedido tiene 2 ítem(s):

         • 3x Ventanas corredizas de aluminio
         • 2x Puertas de vidrio

         ¿Confirmás el pedido? Respondé SÍ para confirmar o NO para cancelar.

Usuario: sí

Bot:     ✅ Pedido #47 confirmado.
         Quedó registrado en el sistema. ¡Gracias!
```

---

## Ver los pedidos en AkunCalcu

Una vez configurado, los pedidos se ven en:
**http://localhost:8080/pedidos/**
