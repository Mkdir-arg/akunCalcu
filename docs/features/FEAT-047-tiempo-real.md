# FEAT-047 — Actualización en vivo por polling

- **Estado:** Implementado (rama `development`, sin desplegar a `main`)
- **Fecha:** 2026-10-29
- **Requerimiento:** [REQ-065](../requerimientos/REQ-065-tiempo-real-polling.md)
- **Decisión:** [ADR-024](../team/decisions.md)
- **Apps:** `core` (infraestructura) y un `live.py` por app
- **Migración:** sí, `core` (modelos `Aviso` y `EdicionActiva`); se aplica sola en el deploy (`RUN_MIGRATIONS_ON_STARTUP=true`)

## Qué hace

La pantalla consulta cada 20 s a `GET /core/api/live/` y se actualiza sola. Se pausa con la pestaña
oculta (`visibilitychange`) y espera más tras un error (backoff hasta 120 s).

### API

- **Registro por app** (`<app>/live.py`, autodescubierto): `core.live.register(key, queryset, date_field='updated_at', permission=None)`.
  `queryset` es una función `f(user)` ya filtrada por lo que ese usuario puede ver; `permission` es el
  código de acceso (sin acceso, la fuente no se devuelve). El endpoint hace **una consulta agregada**
  (`Max(date_field)` y `Count`) por fuente, hasta un máximo de claves por pedido.
- **Fuentes registradas:** `presupuestos`, `ventas`, `clientes`, `compras`, `eventos`, `facturas`, `gastos`,
  `pedidos_voz`, `pedidos_fabrica`, `catalogo-productos`, `fabrica-*` (perfiles, vidrios, accesorios,
  productos, marcos, hojas, materiales-ciegos), `backups`, `auditoria`, `salud`, `solicitudes`,
  `usuarios`, `usuarios_perfiles`, `inicio_solicitudes` y `avisos`.
- **Marcado en el HTML:**
  - `data-live="clave[,clave2]"`: ante un cambio aparece el banner «Hay cambios · Actualizar».
  - `data-live-partial` (en el mismo elemento): en lugar del banner se recarga su contenido con `?partial=1`
    (la vista devuelve solo el fragmento). No se actualiza si el foco está dentro.
  - `data-live-edit="app.modelo:pk"` (+ `data-live-edit-label`): muestra «X también está editando este …».
- **Respuesta:** `sources` (por clave `{max, count}`), `avisos` (no leídos), `dolar`, `kpis`, `edit`, `server_time`.
- **Endpoints:** `GET /core/api/live/?keys=…&edit=…` (`@login_required`) y `POST /core/api/avisos/leido/`
  (`id=<n>` o `id=all`, solo avisos propios).
- **Avisos:** modelo `core.Aviso` (usuario, tipo `info|exito|alerta|error`, texto, url, leído, fecha) y helper
  `core.avisos.crear_aviso(usuarios, texto, tipo='info', url='')`. Se llama desde vistas o servicios, no con signals.
- **Presencia:** modelo `core.EdicionActiva` (usuario, tipo de contenido, objeto, `last_seen`), caduca a los 60 s.
  Está en la base y no en memoria porque el caché local no se comparte entre los 3 workers de gunicorn.

### Avisos que se disparan

| Evento | Quién lo recibe | Dónde |
|---|---|---|
| Presupuesto confirmado | usuarios relevantes (tipo `exito`) | `presupuestos/views.py` |
| Pedido por voz nuevo, pendiente de confirmar | usuarios con acceso al módulo | `pedidos/views.py` |
| Backup fallido | administración | `security/views.py` |
| Solicitud de presupuesto nueva/asignada | el asignado | `solicitudes/views.py` |

### Sesión

El polling no cuenta como actividad: no actualiza `last_activity` (`PASSIVE_POLL_PATHS`), no se audita
y, para las rutas `/core/api/`, `core.middleware.PassiveSessionMiddleware` evita que
`SESSION_SAVE_EVERY_REQUEST` renueve la sesión. Así una pestaña abierta no impide que la sesión de 8 h venza.

## Criterios cumplidos

Ver los de [REQ-065](../requerimientos/REQ-065-tiempo-real-polling.md).

## Limitaciones

- **Cliente y las tablas de `pricing`** (perfiles, vidrios, etc., legacy) no tienen fecha de modificación: solo se detectan altas y bajas (por `count`), no ediciones.
- **Backup** cuenta solo los backups terminados.
- **Sin índices en `updated_at`** de las tablas grandes; si el `Max`/`Count` se vuelve lento hay que agregarlos (backlog).
- La latencia es de hasta 20 s; no es tiempo real estricto.

## Archivos

`core/live.py`, `core/live_api.py`, `core/avisos.py`, `core/models.py` (`Aviso`, `EdicionActiva`), `core/urls.py`,
`core/middleware.py` (`PassiveSessionMiddleware`), `static/js/live.js`, `<app>/live.py`, `security/middleware.py`
(`PASSIVE_POLL_PATHS`), tests en `core/tests.py`.
