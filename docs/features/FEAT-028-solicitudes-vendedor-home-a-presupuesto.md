# FEAT-028 — Bandeja del vendedor en el home + crear presupuesto desde la solicitud

- **Estado:** Implementado
- **Fecha:** 2026-07-23
- **Apps:** `core` (home), `presupuestos`, `comercial`, `solicitudes`
- **Relacionada:** extiende [FEAT-025](./FEAT-025-reparto-automatico-solicitudes-presupuesto.md)

## Qué hace

Cierra el circuito entre una **solicitud** (lead que llega por email, FEAT-025) y un
**presupuesto**:

1. El vendedor entra a **`/home/`** y ve una tabla **"Mis solicitudes pendientes"** (solo las
   asignadas a él y sin atender).
2. Por fila puede **"Crear presupuesto"** (abre el alta de presupuesto precargada con los datos
   del pedido) o **"Marcar contestada"** (si el cliente desistió).
3. Al **crear el presupuesto**, queda **vinculado a la solicitud** (OneToOne) y la solicitud pasa
   automáticamente a **contestada** → sale del home y del recordatorio diario. Una sola acción.

Para no duplicar el cliente: el alta de presupuesto muestra los datos del pedido y permite
**elegir un Cliente existente** o **crear uno nuevo prellenado** con esos datos.

## Flujo

```
Solicitud (asignada)  →  /home/ "Mis solicitudes"  →  "Crear presupuesto"
   →  /presupuestos/crear?solicitud=<id>  (datos del pedido a la vista + selector de Cliente
        · "Crear cliente con estos datos" → comercial/cliente_create prellenado → vuelve con el cliente elegido)
   →  al guardar: Presupuesto.solicitud = solicitud  +  solicitud → contestada
   →  (sigue el flujo normal: presupuesto confirmado → Venta + Pedido)
```

## Archivos

- `presupuestos/models.py` — FK `Presupuesto.solicitud` (OneToOne, nullable, SET_NULL) + migración
  `0012_presupuesto_solicitud`.
- `presupuestos/views.py` — `crear` acepta `?solicitud`/`?cliente`, vincula y cierra la solicitud
  al guardar, y arma la URL de "crear cliente prellenado" (`_get_solicitud_param`).
- `presupuestos/templates/presupuestos/form.html` — box con los datos del pedido + link "crear
  cliente con estos datos" + hidden `solicitud_id`.
- `comercial/views.py` — `cliente_create` acepta prefill por query params (nombre/apellido/tel/email)
  y `next` (URL interna) para volver con `?cliente=<id>`.
- `core/views.py` + `core/templates/core/home.html` — tabla "Mis solicitudes pendientes" (solo rol
  vendedor) con acciones + JS de "marcar contestada" (SweetAlert2).
- `solicitudes/views.py` — `solicitud_marcar_contestada` honra `next` y valida propiedad (el vendedor
  solo marca las suyas; admin cualquiera).
- `usuarios/access_control.py` — `solicitudes:marcar_contestada` también accesible con `dashboard.view`
  (para la bandeja del vendedor).

## Decisiones técnicas

- **1:1 solicitud ↔ presupuesto** (OneToOne). Si el presupuesto se cancela y hay que rehacerlo, se
  reabre a mano (caso borde).
- **"Atendida" = tiene presupuesto** → se reusa el estado `contestada` (sin estado nuevo). Por eso se
  **dio de baja la detección de "contestada por respuesta de email"** (WF3 que nunca se construyó):
  quedaba redundante.
- El **cliente no se duplica**: prefill + el vendedor matchea/crea. No se crea Cliente automático.
- Permisos: el rol **Vendedor** necesita `dashboard.view` (home) y `presupuestos.view` (crear) — los
  asigna el admin en Configuración.

## Pendiente de despliegue

- Migración `presupuestos/0012_presupuesto_solicitud` (aditiva, FK nullable).
- Deploy del código (se junta con el ajuste del recordatorio diario).
- Asignar al rol Vendedor los accesos Dashboard + Presupuestos.

## Tests

- `presupuestos`: crear desde solicitud vincula + cierra; sin solicitud no rompe.
- `core`: el home muestra "Mis solicitudes" al vendedor; las contestadas no aparecen; el admin no ve la tabla.
- `solicitudes`: guard de propiedad al marcar contestada (propia OK / ajena 403).
- `comercial`: `cliente_create` prellena desde query params.
- Suite afectada: 157 OK (solicitudes + presupuestos + core + comercial nuevo), sin regresiones.
