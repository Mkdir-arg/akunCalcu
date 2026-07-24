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

Estado en la instancia de n8n (2026-07-23):
- **"Solicitudes Presupuesto - Reparto AkunCalcu"** (id `PlXLIyyN2wyFYICD`) — credenciales
  Gmail + OpenAI cableadas. Detecta **2 vías**: formulario web (determinístico) y mail directo
  (IA). Gmail Trigger **v1.4**, `simple:false` (trae el cuerpo), **maxResults 20** + **readStatus
  both** (no pierde en ráfaga ni si el mail se abrió) y `q` que incluye el formulario y descarta
  ruido. Ojo: `simple:false` devuelve el mensaje **parseado** (`subject`, `text` =cuerpo plano,
  `from`=objeto con `.text`), NO el formato crudo (`payload.headers/parts`). **Inactivo**: falta
  poner el toggle "Active" en ON (esta versión de n8n no permite activar por API). ⚠️ El `.json`
  de backup quedó **desactualizado** (2 vías); la fuente de verdad es el workflow vivo
  `PlXLIyyN2wyFYICD`.
- **"Solicitudes Presupuesto - Recordatorios AkunCalcu"** (id `M5N22elKbX2w6SMQ`) — **Activo**.
  Corre **1 vez por día a las 08:00** y manda **un solo WhatsApp por vendedor** con el listado de
  todas sus solicitudes sin contestar.

Ya NO hace falta importar los `.json` (quedan como backup). Pendiente para el flujo completo:
setear `EVOLUTION_APIKEY` en el servicio n8n, aprobar las plantillas de Meta, y activar el
workflow de Reparto. Nota: fijar `N8N_ENCRYPTION_KEY` en Railway o cada redeploy rompe las
credenciales de n8n.

---

## Workflow 1 — Reparto (principal)

```
Nuevo mail (Gmail Trigger, simple:false → trae el cuerpo)
  → Extraer mail (Code: subject, from, body de texto plano, gmail_thread_id)
  → ¿Es Formulario Web? (IF: asunto contiene "Nuevo formulario web")
       ├─ SÍ → Parsear Formulario (Code, regex sobre los campos del form) ─┐
       └─ NO → IA Clasificar y Extraer (OpenAI sobre el CUERPO) → Parsear IA → Es Presupuesto? ─┤(sí)
                                                                                                 ▼
                                                              Crear Solicitud (POST /solicitudes/api/crear/)
                                                                → Es Nueva? (duplicada=false) ──sí──▶
                                                                     ├─ Reenviar al Vendedor (Gmail)
                                                                     └─ WhatsApp al Vendedor (sendTemplate 'nueva_solicitud')
```

**Dos vías de entrada (ambas detectadas):**
- **Formulario web**: llega desde la propia casilla (`from:me`) con asunto fijo *"Nuevo formulario
  web"* y cuerpo con campos etiquetados (Nombre / E-mail / Teléfono / Barrio-Localidad / consulta).
  Se parsea **determinísticamente** (sin depender de la IA → funciona aunque OpenAI falle).
- **Mail directo del cliente** (texto libre): lo clasifica/extrae la **IA sobre el cuerpo completo**.

**Notas clave:**
- El Gmail Trigger va en **`simple:false`** para traer el cuerpo (antes iba `simple:true` → solo
  `snippet`, y por eso la IA no clasificaba bien).
- El `q` **ya NO usa `-from:me`** (eso excluía al formulario, que viene de la propia casilla). El
  anti-loop se mantiene con `-subject:"Nuevo pedido de presupuesto"` (el reenvío ya no vuelve al
  inbox porque el email del vendedor está bien cargado).
- **Es Nueva** usa `duplicada` (idempotencia por `gmail_thread_id`) → un solo aviso aunque el
  trigger dispare de más. La API responde `vendedor{...}` + `solicitud{nombre_cliente,telefono,...}`
  para que el reenvío/WhatsApp tengan los datos venga por la vía que venga.

## Workflow 2 — Recordatorios (resumen diario)

```
Todos los días 8:00 (Schedule cron 0 8 * * *)
  → Obtener Recordatorios (POST /solicitudes/api/recordatorios/ → 1 ítem por vendedor)
  → Hay Recordatorios? (IF cantidad > 0)
       └─ sí → Preparar Envios → WhatsApp Enviar (sendTemplate 'recordatorio_solicitud', UN WhatsApp por vendedor)
                 → Recolectar IDs → Marcar Recordatorio (POST /solicitudes/api/marcar-recordatorio/)
```

Django agrupa por vendedor y arma el listado en **una sola línea** (`Cliente (tel) · Cliente (tel) · …`)
porque Meta no permite saltos de línea en los parámetros de plantilla. El `{{1}}` de
`recordatorio_solicitud` recibe ese listado. Conviene que la plantilla tenga texto en plural
(ej. "tenés pedidos de presupuesto sin responder: {{1}}").

---

## Endpoints Django (app `solicitudes`)

Todos POST, auth por header `X-Bot-Secret` = env `SOLICITUDES_BOT_SECRET`.

| Endpoint | Uso |
|---|---|
| `/solicitudes/api/crear/` | Crea la solicitud + asigna vendedor round-robin. Idempotente por `gmail_thread_id`. |
| `/solicitudes/api/recordatorios/` | Resumen diario: un ítem por vendedor con el listado (una línea) de sus solicitudes asignadas sin contestar. |
| `/solicitudes/api/marcar-recordatorio/` | Marca enviado el recordatorio de los ids dados. |
| `/solicitudes/api/marcar-contestada/` | Marca contestada (manual desde el home/panel). También se cierra sola al crear un presupuesto desde la solicitud (FEAT-028). |

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

### Marcar contestada — request (manual; acepta solicitud_id o gmail_thread_id)
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

**"Contestada" — cómo se cierra una solicitud:**
- **Manual:** botón "Marcar contestada" en el home del vendedor o en el panel `/solicitudes/`.
- **Automática:** al **crear un presupuesto desde la solicitud** (FEAT-028) la solicitud queda
  vinculada y pasa a contestada sola.
- La detección por **respuesta de email** (un tercer workflow que miraba el hilo de Gmail) se
  **dio de baja**: quedó redundante con "atendida = tiene presupuesto".

---

## Notas

- El reparto round-robin lo decide **Django** (no n8n): puntero en DB con `select_for_update`.
  n8n es solo transporte (ADR-014).
- La creación es **idempotente** por `gmail_thread_id`: si n8n reintenta el mismo mail, no
  duplica la solicitud.
- Los `.json` usan placeholders (`REEMPLAZAR_*`) en lugar de secretos reales. No commitear
  apikeys de Evolution/Meta.
