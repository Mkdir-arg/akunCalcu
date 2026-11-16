# REQ-077 — Pedidos al desarrollo (tickets) dentro de Novedades
**Estado**: Implementado
**Derivó en**: [FEAT-060](../features/FEAT-060-pedidos-al-desarrollo.md)
**Fecha**: 2026-11-16
**Solicitante**: Dirección / Desarrollo
**Relacionado con**: [REQ-069](./REQ-069-novedades-del-sistema.md)

## Descripción de la idea
Dentro del módulo **Novedades** (`/novedades/`), cualquier usuario puede levantar un **pedido**
al desarrollo (un error, una mejora, una idea) con título, etiqueta y comentario. El pedido le
llega al administrador, que lo ve en una bandeja, deja comentarios y le cambia el estado, como un
ticket de desarrollo. El usuario sigue el estado de sus pedidos y lee las respuestas.

## User Story
> **US-077** — Como usuario de AkunCalcu quiero levantar pedidos al desarrollo (título, etiqueta y
> comentario) desde Novedades para que el administrador los reciba, me responda y yo vea en qué
> estado está cada uno.

## Criterios de aceptación
- [x] En `/novedades/` hay un botón **«Nuevo pedido»** y una sección **«Mis pedidos»**.
- [x] El formulario pide **título** (obligatorio), **etiqueta** (Error / Mejora / Nueva funcionalidad / Consulta) y **comentario** (obligatorio).
- [x] Al crearlo queda en estado **Nuevo**, con el usuario que lo levantó y la fecha.
- [x] El usuario ve solo **sus** pedidos (lista + detalle); no puede abrir los de otros (404).
- [x] El administrador (staff) ve **todos** los pedidos en una bandeja, con filtro por estado y etiqueta, paginada.
- [x] En el detalle, el administrador puede **dejar comentarios** y **cambiar el estado**: Nuevo → En análisis → En desarrollo → Resuelto / Descartado.
- [x] Cada cambio de estado queda registrado en el hilo del pedido (quién, cuándo, de qué estado a cuál).
- [x] El usuario que levantó el pedido ve los comentarios y el estado actual, y **puede responder** en el mismo hilo.
- [x] Solo el administrador cambia el estado.
- [x] Tests: modelos (`__str__`), vistas (status, login requerido, usuario ajeno → 404, no-staff no cambia estado).

## Fuera de alcance (por ahora)
- Notificaciones por WhatsApp/email al crear o responder un pedido.
- Adjuntar archivos o capturas.
- Asignar responsables o prioridades.

## Complejidad
Mediano — 2 modelos nuevos (pedido + comentario), 1 migración, ~4 vistas, 3 templates.
