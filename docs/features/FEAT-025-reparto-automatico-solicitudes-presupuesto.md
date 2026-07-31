# FEAT-025 — Reparto automático de solicitudes de presupuesto (n8n + round-robin)

- **Estado:** Implementado
- **Fecha:** 2026-07-18
- **Requerimiento:** [REQ-037](../requerimientos/REQ-037-reparto-automatico-solicitudes-presupuesto.md)
- **App principal:** `solicitudes` (nueva) · toca `usuarios`, `security`, `akuna_calc`

## Qué hace

Automatiza el reparto de los pedidos de presupuesto que llegan por email a la casilla
de la empresa. Antes se distribuían a mano; ahora un workflow de n8n toma el mail, lo
clasifica/extrae con IA y lo empuja a AkunCalcu, que lo registra y **lo asigna por turnos
(round-robin) al próximo vendedor**, devolviendo sus datos para que n8n reenvíe el mail y
avise por WhatsApp. Un panel web permite seguir el estado de cada solicitud.

## Flujo

```
Gmail Trigger (casilla empresa)
  → si el subject es "Nuevo formulario web": parser del formulario de la página
    si no: IA clasifica "¿es pedido de presupuesto?" + extrae nombre/tel/email/mensaje
  → POST /solicitudes/api/crear/  (header X-Bot-Secret)
      → Django filtra spam (FIX-019): si lo es, queda "descartada" y NO consume turno
      → si no, crea SolicitudPresupuesto + asigna vendedor round-robin (puntero en DB)
      → devuelve {nombre, email, whatsapp} del vendedor + flag `notificar`
  → si notificar: n8n reenvía el mail al vendedor + le manda WhatsApp
Cron diario de n8n (08:00):
  → POST /solicitudes/api/recordatorios/  → un ítem por vendedor con el listado de sus pendientes
  → n8n manda UN WhatsApp por vendedor (listado en una línea) → POST /solicitudes/api/marcar-recordatorio/
Cierre de la solicitud ("contestada"):
  → manual (home del vendedor / panel) o automático al crear un presupuesto desde la solicitud (FEAT-028)
  → (la detección por respuesta de email se dio de baja: redundante con "atendida = tiene presupuesto")
```

## Criterios de aceptación (todos cumplidos)

- [x] Endpoint API que recibe la solicitud (nombre, email, teléfono, mensaje) autenticado
  con `X-Bot-Secret` y crea `SolicitudPresupuesto`.
- [x] Asignación automática round-robin con puntero persistido en DB (race-safe con
  `select_for_update`).
- [x] Pool = usuarios con Rol de sistema `vendedor` activo y email cargado.
- [x] El endpoint devuelve nombre/email/whatsapp del vendedor asignado.
- [x] Panel `/solicitudes/` con filtros (estado, vendedor) y paginación (20).
- [x] "Contestada" manual (botón del panel) y automática (endpoint por `gmail_thread_id`).
- [x] Reasignación manual a otro vendedor.
- [x] Recordatorio **1 vez por día a las 08:00**: un solo WhatsApp por vendedor con el listado
  de todas sus solicitudes sin contestar (no un mensaje por solicitud).
- [x] Workflow de n8n documentado en `docs/n8n/`. ⚠️ El JSON estuvo desincronizado del workflow
  real (8 nodos vs 11) hasta FIX-020, que lo regeneró desde el grafo en vivo. Si se vuelve a
  editar el workflow en la UI, **regenerar el JSON**: es el respaldo y la fuente del test
  `docs/n8n/test-nodos-reparto.js`.

## Archivos

**Nuevos (app `solicitudes`):**
- `models.py` — `SolicitudPresupuesto` (+ manager `pendientes_recordatorio`) y
  `ConfiguracionSolicitudes` (singleton con el puntero del round-robin).
  Estados: `asignada`, `contestada`, `sin_asignar`, `descartada` (este último de FIX-019).
- `services.py` — `vendedores_pool()` y `asignar_siguiente_vendedor()` (round-robin atómico).
- `spam.py` — `clasificar_spam()` (FIX-019): heurística por puntaje, 5 señales, umbral 2.
- `views.py` — panel (`solicitud_list`, `solicitud_marcar_contestada`, `solicitud_reasignar`)
  y 4 endpoints API (`api_crear`, `api_recordatorios`, `api_marcar_recordatorio`,
  `api_marcar_contestada`).
- `forms.py` — `ReasignarSolicitudForm`.
- `urls.py`, `admin.py`, `apps.py`, `tests.py` (21 tests).
- `templates/solicitudes/solicitud_list.html` — panel (design system + SweetAlert2).
- `migrations/0001_initial.py`.

**Modificados:**
- `usuarios/models.py` — FK `PerfilAccesoUsuario.numero_whatsapp → gastos_diarios.NumeroAutorizado`.
- `usuarios/forms.py` + `templates/usuarios/user_form.html` — select del número de WhatsApp.
- `usuarios/access_control.py` — módulo de menú `solicitudes`, subrutas y rutas API públicas.
- `usuarios/migrations/0004_perfilaccesousuario_numero_whatsapp.py`,
  `0005_seed_rol_vendedor.py` (crea el rol `vendedor`).
- `security/middleware.py` — `/solicitudes/api/` exento de seguridad y auditoría.
- `akuna_calc/settings.py` (INSTALLED_APPS), `akuna_calc/urls.py` (include), `.env.example`
  (`SOLICITUDES_BOT_SECRET`).

## Decisiones técnicas

- **Round-robin en Django, no en n8n** (ADR-014): la decisión de a quién le toca vive en la
  DB (`ConfiguracionSolicitudes.ultimo_vendedor`), tomada con `select_for_update` para que
  dos mails simultáneos no reciban el mismo vendedor. n8n queda como transporte.
- **WhatsApp del vendedor reusa `NumeroAutorizado`** (los mismos números de Gastos Diarios /
  Agenda) vía FK en el perfil de acceso, en vez de un campo de texto nuevo.
- **Secret dedicado** `SOLICITUDES_BOT_SECRET` (separado de Telegram/Backup), mismo patrón
  `X-Bot-Secret`.
- **Idempotencia** por `gmail_thread_id`: si n8n reintenta, no duplica la solicitud.
- **Rol `vendedor` sembrado por migración** (no existía en el repo).
- **Filtro anti-spam en Django, no en n8n** (FIX-019): `api_crear` es el único punto por el
  que pasan todas las solicitudes (formulario web + rama IA + orígenes futuros) y es donde se
  consume el turno de la rotación. Ver `solicitudes/spam.py`.

## Estado en producción (verificado 2026-07-31)

Desplegado y funcionando. Ambos workflows de n8n están **activos**:
`PlXLIyyN2wyFYICD` (Reparto, Gmail trigger cada minuto) y `M5N22elKbX2w6SMQ`
(Recordatorios, cron 08:00 ARG). Migraciones aplicadas, `SOLICITUDES_BOT_SECRET` seteado en
los servicios `web` y `n8n`, credenciales de Gmail/OpenAI/Evolution conectadas.

Pool de rotación real: **Valeria Tullio** (`akunaberturasventas@gmail.com`) y
**Veronica Malicoutakis** (`akunaberturasadm@gmail.com`). Round-robin verificado alternando
correctamente en las solicitudes 60 a 63.

**Pendientes conocidos (fuera del alcance de FEAT-025, FIX-019 y FIX-020):**
- **Nadie avisa cuando el reparto se cae.** El 30/07 la credencial OAuth de Gmail expiró y el
  trigger estuvo **25 horas sin poder leer la casilla** sin que nada lo reportara: un trigger que
  no puede leer no genera ejecución, así que en n8n no se ve nada rojo. Falta un Error Trigger o
  un chequeo diario de "horas sin lecturas". Ver también la nota de las credenciales de Google,
  que caducan cada 7 días si la app OAuth está en modo Testing.
- Los nodos `Crear Solicitud`, `Reenviar al Vendedor` y `WhatsApp al Vendedor` tienen
  `onError: continueRegularOutput`: si Django está caído, la ejecución queda marcada
  **"success"** y el pedido se pierde sin alerta. "0 errores" en n8n no es garantía de nada
  en este workflow.
- Con `maxResults: 20` ya funcionando de verdad (FIX-020), un poll con 20 mails dispara hasta
  20 llamadas a OpenAI, 20 POST, 20 mails y 20 WhatsApp — atención al rate limit de Meta.
- `api_marcar_contestada` no está automatizado: ningún workflow detecta la respuesta del
  vendedor en el hilo de Gmail. El cierre es manual (panel/home) o vía FEAT-028.
- El WhatsApp sale con `status: PENDING` (template `nueva_solicitud` de Evolution/Cloud API);
  no hay confirmación de entrega.
- El filtro `q` del Gmail trigger no tiene `in:inbox`, así que también procesa mails enviados
  desde la cuenta (cada uno pasa por GPT-4o-mini). Gasto evitable.

## Tests

- `solicitudes`: **39 OK** (modelo, round-robin, pool, 4 endpoints API, panel, y 19 del
  clasificador anti-spam de FIX-019 con los casos reales de producción).
- Sin regresiones: `solicitudes`/`core`/`usuarios`/`presupuestos` = 201 OK.
