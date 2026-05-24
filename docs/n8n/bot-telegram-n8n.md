# Bot de Telegram con n8n - Sistema AkunCalcu

> **Fecha**: 2025-01-02  
> **Estado**: ✅ Operativo  
> **Versión**: 1.0

---

## 📋 Descripción General

Bot de Telegram integrado con n8n que recibe mensajes de audio, los transcribe usando OpenAI Whisper y responde automáticamente con el texto transcrito.

**Bot**: @Akun_aberturas_bot

---

## 🏗️ Arquitectura

### Stack Tecnológico

```
┌─────────────────────────────────────────┐
│  Telegram (Usuario)                     │
└──────────────┬──────────────────────────┘
               │ HTTPS
               ▼
┌─────────────────────────────────────────┐
│  ngrok (Túnel HTTPS)                    │
│  mya-hypernatural-dalton.ngrok-free.dev │
└──────────────┬──────────────────────────┘
               │ HTTP
               ▼
┌─────────────────────────────────────────┐
│  n8n (Workflow Engine)                  │
│  localhost:5678                         │
└──────────────┬──────────────────────────┘
               │
               ├──► Telegram API (descarga audio)
               └──► OpenAI Whisper (transcripción)
```

### Servicios Docker

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| `db` | 3308 | MySQL 8.0 |
| `web` | 8080 | Django AkunCalcu |
| `n8n` | 5678 | Workflow automation |
| `ngrok` | 4040 | Túnel HTTPS (dashboard) |

---

## 🔑 Credenciales

### Telegram Bot

```
Token: 8692614558:AAEX4KTGfjpD8OAN4foEmBqnu3r8NCGuGvY
Username: @Akun_aberturas_bot
Bot Name: Akun Aberturas Bot
```

**Configuración en n8n**:
1. Settings → Credentials → Add Credential
2. Tipo: Telegram API
3. Access Token: `8692614558:AAEX4KTGfjpD8OAN4foEmBqnu3r8NCGuGvY`

### OpenAI API

**Uso**: Transcripción de audio con modelo Whisper-1

**Configuración en n8n**:
1. Settings → Credentials → Add Credential
2. Tipo: OpenAI API
3. API Key: `[TU_OPENAI_API_KEY]`

### ngrok

```
Authtoken: 3AUwL5Yr7jjPQLeX8aIYbUuLHFG_3Kjtk5LZDpLtQAyvWv9Wg
URL Activa: https://mya-hypernatural-dalton.ngrok-free.dev
Dashboard: http://localhost:4040
```

---

## 🔄 Workflow n8n

### Flujo Completo

```
[Telegram Trigger]
    ↓ (recibe audio)
[Get File Info]
    ↓ (obtiene file_path)
[Download Audio]
    ↓ (descarga .ogg)
[Transcribe Audio]
    ↓ (Whisper → texto)
[Responder Transcripción]
    ↓ (envía respuesta)
```

### Configuración de Nodos

#### 1. Telegram Trigger
```yaml
Type: n8n-nodes-base.telegramTrigger
Updates: ["message"]
Webhook: https://mya-hypernatural-dalton.ngrok-free.dev/webhook/{id}
Output: message.voice.file_id
```

#### 2. Get File Info
```yaml
Type: n8n-nodes-base.telegram
Resource: file
Operation: get
File ID: ={{ $json.message.voice.file_id }}
Output: result.file_path
```

#### 3. Download Audio
```yaml
Type: n8n-nodes-base.httpRequest
Method: GET
URL: https://api.telegram.org/file/bot{TOKEN}/{file_path}
Response Format: file
Output: Binary data
```

#### 4. Transcribe Audio
```yaml
Type: @n8n/n8n-nodes-langchain.openAi
Resource: audio
Operation: transcribe
Binary Property: data
Language: es
Model: whisper-1
Output: text
```

#### 5. Responder Transcripción
```yaml
Type: n8n-nodes-base.telegram
Chat ID: ={{ $('Telegram Trigger').item.json.message.chat.id }}
Text: Transcripción del audio:\n\n{{ $json.text }}
```

### JSON del Workflow

```json
{
  "name": "Bot Telegram Audio Transcripción",
  "nodes": [
    {
      "parameters": {
        "updates": ["message"]
      },
      "name": "Telegram Trigger",
      "type": "n8n-nodes-base.telegramTrigger",
      "typeVersion": 1.2,
      "position": [250, 300],
      "credentials": {
        "telegramApi": {
          "id": "1",
          "name": "Telegram API"
        }
      }
    },
    {
      "parameters": {
        "resource": "file",
        "operation": "get",
        "fileId": "={{ $json.message.voice.file_id }}"
      },
      "name": "Get File Info",
      "type": "n8n-nodes-base.telegram",
      "typeVersion": 1.2,
      "position": [450, 300]
    },
    {
      "parameters": {
        "url": "=https://api.telegram.org/file/bot8692614558:AAEX4KTGfjpD8OAN4foEmBqnu3r8NCGuGvY/{{ $json.result.file_path }}",
        "options": {
          "response": {
            "response": {
              "responseFormat": "file"
            }
          }
        }
      },
      "name": "Download Audio",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.2,
      "position": [650, 300]
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
      "name": "Transcribe Audio",
      "type": "@n8n/n8n-nodes-langchain.openAi",
      "typeVersion": 2.1,
      "position": [850, 300]
    },
    {
      "parameters": {
        "chatId": "={{ $('Telegram Trigger').item.json.message.chat.id }}",
        "text": "=Transcripción del audio:\n\n{{ $json.text }}"
      },
      "name": "Responder Transcripción",
      "type": "n8n-nodes-base.telegram",
      "typeVersion": 1.2,
      "position": [1050, 300]
    }
  ],
  "connections": {
    "Telegram Trigger": {
      "main": [[{"node": "Get File Info", "type": "main", "index": 0}]]
    },
    "Get File Info": {
      "main": [[{"node": "Download Audio", "type": "main", "index": 0}]]
    },
    "Download Audio": {
      "main": [[{"node": "Transcribe Audio", "type": "main", "index": 0}]]
    },
    "Transcribe Audio": {
      "main": [[{"node": "Responder Transcripción", "type": "main", "index": 0}]]
    }
  }
}
```

---

## 🐳 Configuración Docker

### docker-compose.yml

```yaml
services:
  n8n:
    image: n8nio/n8n
    restart: unless-stopped
    ports:
      - "5678:5678"
    environment:
      - WEBHOOK_URL=https://mya-hypernatural-dalton.ngrok-free.dev
      - N8N_EDITOR_BASE_URL=https://mya-hypernatural-dalton.ngrok-free.dev
    volumes:
      - n8n_data:/home/node/.n8n

  ngrok:
    image: ngrok/ngrok:latest
    restart: unless-stopped
    command:
      - "start"
      - "--all"
      - "--config"
      - "/etc/ngrok.yml"
    volumes:
      - ./ngrok.yml:/etc/ngrok.yml
    ports:
      - 4040:4040

volumes:
  n8n_data:
```

### ngrok.yml

```yaml
version: "2"
authtoken: 3AUwL5Yr7jjPQLeX8aIYbUuLHFG_3Kjtk5LZDpLtQAyvWv9Wg
tunnels:
  n8n:
    addr: n8n:5678
    proto: http
```

---

## 🚀 Instalación y Configuración

### 1. Levantar Servicios

```bash
cd C:\Users\mkdir\Proyectos\akunCalcu
docker-compose up -d
```

### 2. Verificar Estado

```bash
# Ver logs de n8n
docker-compose logs -f n8n

# Ver logs de ngrok
docker-compose logs -f ngrok

# Estado de contenedores
docker-compose ps
```

### 3. Configurar n8n

1. Abrir: http://localhost:5678
2. Crear cuenta (primera vez)
3. Importar workflow:
   - Menú → Import from File
   - Seleccionar JSON del workflow
4. Configurar credenciales:
   - Telegram API
   - OpenAI API
5. Activar workflow

### 4. Verificar Webhook

```bash
# Ver URL del webhook
curl https://api.telegram.org/bot8692614558:AAEX4KTGfjpD8OAN4foEmBqnu3r8NCGuGvY/getWebhookInfo
```

Debe mostrar:
```json
{
  "ok": true,
  "result": {
    "url": "https://mya-hypernatural-dalton.ngrok-free.dev/webhook/...",
    "has_custom_certificate": false,
    "pending_update_count": 0
  }
}
```

---

## 🧪 Pruebas

### Test 1: Mensaje de Texto

1. Abrir Telegram
2. Buscar: @Akun_aberturas_bot
3. Enviar: "Hola"
4. Verificar en n8n → Executions

**Resultado esperado**: Mensaje capturado en executions

### Test 2: Audio de Voz

1. Abrir Telegram
2. Buscar: @Akun_aberturas_bot
3. Grabar y enviar audio de voz
4. Esperar respuesta del bot

**Resultado esperado**: 
```
Transcripción del audio:

[texto transcrito del audio]
```

---

## 🔧 Comandos Útiles

### Docker

```bash
# Reiniciar n8n
docker-compose restart n8n

# Ver logs en tiempo real
docker-compose logs -f n8n

# Limpiar y empezar de cero
docker-compose down -v
docker-compose up -d

# Detener solo ngrok
docker-compose stop ngrok

# Acceder al contenedor
docker-compose exec n8n sh
```

### Telegram API

```bash
# Verificar webhook
curl "https://api.telegram.org/bot8692614558:AAEX4KTGfjpD8OAN4foEmBqnu3r8NCGuGvY/getWebhookInfo"

# Eliminar webhook
curl "https://api.telegram.org/bot8692614558:AAEX4KTGfjpD8OAN4foEmBqnu3r8NCGuGvY/deleteWebhook"

# Obtener actualizaciones (polling)
curl "https://api.telegram.org/bot8692614558:AAEX4KTGfjpD8OAN4foEmBqnu3r8NCGuGvY/getUpdates"
```

---

## ❌ Troubleshooting

### Error: "HTTPS URL must be provided"

**Causa**: n8n no tiene configurada la URL de ngrok

**Solución**:
```yaml
# docker-compose.yml
environment:
  - WEBHOOK_URL=https://mya-hypernatural-dalton.ngrok-free.dev
  - N8N_EDITOR_BASE_URL=https://mya-hypernatural-dalton.ngrok-free.dev
```

### Error: "404 Not Found" en webhook

**Causa**: Webhook registrado con URL incorrecta

**Solución**:
```bash
# 1. Eliminar webhook
curl "https://api.telegram.org/bot{TOKEN}/deleteWebhook"

# 2. Reiniciar n8n
docker-compose restart n8n

# 3. Desactivar y reactivar workflow en n8n
```

### Error: "No binary file found"

**Causa**: Falta descargar el audio antes de transcribir

**Solución**: Verificar que el workflow tenga estos nodos en orden:
1. Get File Info
2. Download Audio
3. Transcribe Audio

### ngrok: "endpoint already online"

**Causa**: Dos instancias de ngrok corriendo

**Solución**:
```bash
# Detener contenedor de ngrok
docker-compose stop ngrok

# O usar solo el manual
ngrok http 5678
```

---

## 📊 Monitoreo

### URLs de Acceso

| Servicio | URL | Descripción |
|----------|-----|-------------|
| n8n | http://localhost:5678 | Interfaz de n8n |
| n8n (público) | https://mya-hypernatural-dalton.ngrok-free.dev | A través de ngrok |
| ngrok dashboard | http://localhost:4040 | Ver peticiones en tiempo real |
| AkunCalcu | http://localhost:8080 | Sistema principal |

### Logs Importantes

```bash
# Ver todas las peticiones a n8n
docker-compose logs -f n8n | grep "POST /webhook"

# Ver errores
docker-compose logs n8n | grep "ERROR"

# Ver transcripciones exitosas
docker-compose logs n8n | grep "Transcribe Audio"
```

---

## 🔐 Seguridad

### ⚠️ IMPORTANTE

Los siguientes tokens están expuestos y deben ser revocados en producción:

1. **Telegram Bot Token**: `8692614558:AAEX4KTGfjpD8OAN4foEmBqnu3r8NCGuGvY`
   - Revocar en @BotFather: `/revoke`
   
2. **ngrok Authtoken**: `3AUwL5Yr7jjPQLeX8aIYbUuLHFG_3Kjtk5LZDpLtQAyvWv9Wg`
   - Regenerar en: https://dashboard.ngrok.com

### Mejores Prácticas

- ✅ Usar variables de entorno para tokens
- ✅ No hardcodear credenciales en workflows
- ✅ Rotar tokens periódicamente
- ✅ Limitar acceso al bot (whitelist de usuarios)
- ✅ Usar HTTPS siempre (ngrok o dominio propio)

---

## 🚀 Próximas Mejoras

### Fase 2: Procesamiento Inteligente

- [ ] Extraer información estructurada del audio (cliente, productos, cantidades)
- [ ] Confirmar pedido antes de guardar
- [ ] Guardar transcripciones en base de datos MySQL

### Fase 3: Integración con AkunCalcu

- [ ] Crear pedidos automáticamente desde el bot
- [ ] Consultar estado de pedidos
- [ ] Notificaciones de cambios de estado

### Fase 4: Funcionalidades Avanzadas

- [ ] Respuestas contextuales con IA
- [ ] Soporte para imágenes (OCR)
- [ ] Múltiples idiomas
- [ ] Reportes y estadísticas

---

## 📚 Referencias

- [n8n Documentation](https://docs.n8n.io)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [OpenAI Whisper API](https://platform.openai.com/docs/guides/speech-to-text)
- [ngrok Documentation](https://ngrok.com/docs)

---

## 📝 Changelog

### v1.0 - 2025-01-02
- ✅ Configuración inicial de n8n con Docker
- ✅ Integración con Telegram Bot API
- ✅ Túnel HTTPS con ngrok
- ✅ Transcripción de audio con OpenAI Whisper
- ✅ Workflow completo funcional

---

**Autor**: Sistema AkunCalcu  
**Última actualización**: 2025-01-02  
**Estado**: ✅ Operativo
