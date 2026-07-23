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
  → IA clasifica "¿es pedido de presupuesto?" + extrae nombre/tel/email/mensaje
  → POST /solicitudes/api/crear/  (header X-Bot-Secret)
      → Django crea SolicitudPresupuesto + asigna vendedor round-robin (puntero en DB)
      → devuelve {nombre, email, whatsapp} del vendedor
  → n8n reenvía el mail al vendedor + le manda WhatsApp
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
- [x] Workflow de n8n documentado en `docs/n8n/`.

## Archivos

**Nuevos (app `solicitudes`):**
- `models.py` — `SolicitudPresupuesto` (+ manager `pendientes_recordatorio`) y
  `ConfiguracionSolicitudes` (singleton con el puntero del round-robin).
- `services.py` — `vendedores_pool()` y `asignar_siguiente_vendedor()` (round-robin atómico).
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

## Pendiente de despliegue (no hecho en esta sesión)

- Correr migraciones en Docker/Railway: `solicitudes/0001_initial`,
  `usuarios/0004_perfilaccesousuario_numero_whatsapp`, `usuarios/0005_seed_rol_vendedor`.
- Setear `SOLICITUDES_BOT_SECRET` en el entorno (Railway).
- Conectar credenciales en n8n (Gmail de la empresa + Evolution/WhatsApp) e importar el
  workflow de `docs/n8n/`.
- Asignar el rol "Vendedor" y su número de WhatsApp a los usuarios que correspondan.

## Tests

- `solicitudes`: 21 OK (modelo, round-robin, pool, 4 endpoints API, panel).
- Sin regresiones: `usuarios`/`agenda`/`gastos_diarios`/`security` = 88 OK.
