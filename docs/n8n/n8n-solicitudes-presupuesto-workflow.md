# Workflow n8n — Reparto automático de solicitudes de presupuesto

> **Feature:** [FEAT-025](../features/FEAT-025-reparto-automatico-solicitudes-presupuesto.md) · **Requerimiento:** REQ-037
> **Estado:** Recordatorios creado en la instancia (inactivo); Reparto listo para importar.

Automatiza el reparto de los pedidos de presupuesto que llegan por email a la casilla de
la empresa. Son **dos workflows**:

1. **Reparto** (principal): Gmail → IA clasifica/extrae → AkunCalcu asigna vendedor
   round-robin → reenvía el mail + avisa por WhatsApp.
2. **Recordatorios**: cada 1 hora, avisa por WhatsApp las solicitudes que siguen sin
   contestar.

Archivos importables:
- [n8n-solicitudes-reparto.json](./n8n-solicitudes-reparto.json)
- [n8n-solicitudes-recordatorios.json](./n8n-solicitudes-recordatorios.json)

En la instancia de n8n ya quedó creado (inactivo) **"Solicitudes Presupuesto - Recordatorios
AkunCalcu"** (id `LZZaucnhQhXZne8Y`). El de Reparto quedó para importar (la instancia estaba
respondiendo intermitente al momento de crearlo).

---

## Workflow 1 — Reparto (principal)

```
Nuevo mail (Gmail Trigger)
  → IA Clasificar y Extraer (OpenAI gpt-4o-mini, JSON)
  → Parsear IA (Code)
  → Es Presupuesto? (IF)
       └─ sí → Crear Solicitud (POST /solicitudes/api/crear/)
                 ├─ Reenviar al Vendedor (Gmail: envía mail al vendedor asignado)
                 └─ WhatsApp al Vendedor (Evolution sendTemplate 'nueva_solicitud')
```

La IA recibe el email entero (JSON de Gmail) y devuelve:
```json
{ "es_presupuesto": true, "nombre_cliente": "", "email": "", "telefono": "", "asunto": "", "mensaje": "" }
```
`Crear Solicitud` recibe la respuesta de AkunCalcu con el vendedor asignado
(`vendedor.email`, `vendedor.whatsapp`, `vendedor.nombre`) y de ahí salen el reenvío y el
WhatsApp.

## Workflow 2 — Recordatorios (ya creado, inactivo)

```
Cada 1 hora (Schedule)
  → Obtener Recordatorios (POST /solicitudes/api/recordatorios/)
  → Hay Recordatorios? (IF cantidad > 0)
       └─ sí → Preparar Envios → WhatsApp Enviar (sendTemplate 'recordatorio_solicitud')
                 → Recolectar IDs → Marcar Recordatorio (POST /solicitudes/api/marcar-recordatorio/)
```

---

## Endpoints Django (app `solicitudes`)

Todos POST, auth por header `X-Bot-Secret` = env `SOLICITUDES_BOT_SECRET`.

| Endpoint | Uso |
|---|---|
| `/solicitudes/api/crear/` | Crea la solicitud + asigna vendedor round-robin. Idempotente por `gmail_thread_id`. |
| `/solicitudes/api/recordatorios/` | Devuelve solicitudes sin contestar hace ≥1h (con WhatsApp del vendedor). |
| `/solicitudes/api/marcar-recordatorio/` | Marca enviado el recordatorio de los ids dados. |
| `/solicitudes/api/marcar-contestada/` | Marca contestada (auto: cuando el vendedor responde en el hilo). |

### Crear — request
```json
{ "nombre_cliente": "Juan Pérez", "email": "juan@mail.com", "telefono": "11...", "asunto": "Ventana", "mensaje": "Quiero presupuesto", "gmail_thread_id": "18f..." }
```
### Crear — response
```json
{ "ok": true, "duplicada": false, "solicitud_id": 12, "estado": "asignada",
  "vendedor": { "nombre": "Ana", "email": "ana@akun.com", "whatsapp": "5491100000001" },
  "mensaje_whatsapp": "📩 Nuevo pedido de presupuesto\n👤 Juan Pérez\n..." }
```
Si no hay vendedores en la rotación: `estado: "sin_asignar"`, `vendedor: null`.

### Marcar contestada — request (auto, por hilo)
```json
{ "gmail_thread_id": "18f..." }
```

---

## ⚠️ WhatsApp: hace falta plantilla de Meta aprobada

El WhatsApp de Akun es **Evolution + Meta Cloud API oficial**. Los mensajes proactivos (el
vendedor no escribió al bot en las últimas 24h) **exigen una plantilla aprobada por Meta**,
no texto libre (mismo caso que los recordatorios de Agenda, error Meta 131047). Por eso los
nodos usan `sendTemplate`. Hay que crear y aprobar en Meta:

| Plantilla | Categoría | Idioma | Params del body |
|---|---|---|---|
| `nueva_solicitud` | Utility | es_AR | `{{1}}` = vendedor, `{{2}}` = cliente + contacto |
| `recordatorio_solicitud` | Utility | es_AR | `{{1}}` = detalle (cliente/contacto/asunto) |

Ejemplo de cuerpo `nueva_solicitud`: *"Hola {{1}}, te asignaron un nuevo pedido de
presupuesto: {{2}}. Respondelo cuando puedas."*

Hasta tener las plantillas aprobadas, el reenvío por **Gmail** al vendedor sí funciona
(no depende de Meta); solo el aviso por WhatsApp queda pendiente.

---

## Puesta en marcha (checklist)

**En AkunCalcu / Railway (deploy — pendiente):**
1. Correr migraciones: `solicitudes/0001_initial`, `usuarios/0004_perfilaccesousuario_numero_whatsapp`, `usuarios/0005_seed_rol_vendedor`.
2. Setear env `SOLICITUDES_BOT_SECRET` (mismo valor en Django y en n8n).
3. Asignar el rol **Vendedor** a los usuarios que reciben pedidos y cargarles su
   **Número de WhatsApp** (Configuración → Usuarios; el número sale de "Números autorizados").

**En n8n:**
4. Crear la credencial **Gmail OAuth2** de la casilla de la empresa (requiere login de Google).
   Adjuntarla a los nodos `Nuevo mail` y `Reenviar al Vendedor`.
5. En el nodo `IA Clasificar y Extraer`, elegir la credencial **OpenAI account** (ya existe).
6. Setear env vars del servicio n8n: `AKUNACALCU_WEB_URL` (URL pública de Django),
   `SOLICITUDES_BOT_SECRET`, `EVOLUTION_APIKEY` (misma apikey que usan los otros workflows).
7. Crear y aprobar en Meta las plantillas `nueva_solicitud` y `recordatorio_solicitud`.
8. Importar `n8n-solicitudes-reparto.json`, revisar y **activar** ambos workflows.

**Detección de "contestada" automática (opcional, v2):**
- Un tercer workflow con Gmail Trigger sobre respuestas del vendedor (o sobre el label
  "Enviados") que, al detectar una respuesta en el hilo, llame a
  `POST /solicitudes/api/marcar-contestada/` con el `gmail_thread_id`. Mientras tanto, la
  solicitud se marca contestada a mano desde el panel `/solicitudes/`.

---

## Notas

- El reparto round-robin lo decide **Django** (no n8n): puntero en DB con `select_for_update`.
  n8n es solo transporte (ADR-014).
- La creación es **idempotente** por `gmail_thread_id`: si n8n reintenta el mismo mail, no
  duplica la solicitud.
- Los `.json` usan placeholders (`REEMPLAZAR_*`) en lugar de secretos reales. No commitear
  apikeys de Evolution/Meta.
