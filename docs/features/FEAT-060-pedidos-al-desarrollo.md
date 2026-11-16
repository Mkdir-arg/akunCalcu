# FEAT-060 — Pedidos al desarrollo (tickets) en Novedades

**Estado:** Implementado
**Fecha:** 2026-11-16
**Requerimiento:** [REQ-077](../requerimientos/REQ-077-pedidos-al-desarrollo.md) (extiende [FEAT-053](./FEAT-053-novedades-del-sistema.md))

## Qué hace

Cualquier usuario puede levantar un **pedido al desarrollo** (un error, una mejora, una idea o una
consulta) y seguirlo como un ticket. El administrador lo recibe, comenta y cambia el estado.

- **Dónde:** ítem **Pedidos al desarrollo** en el menú (bloque *Sistema AKUN*, visible para todos) y
  botones **«Nuevo pedido»** / **«Mis pedidos»** en `/novedades/`.
- **Alta:** título, etiqueta (Error / Mejora / Nueva funcionalidad / Consulta) y comentario. Queda
  en estado **Nuevo**, con quién lo pidió y cuándo.
- **Listado:** el usuario ve solo sus pedidos («Mis pedidos»); el administrador ve todos («Pedidos al
  desarrollo»), con pestañas por estado con contador y filtro por etiqueta. Paginado de a 20.
- **Detalle:** el pedido original y un **hilo de comentarios** donde escriben quien lo pidió y el
  administrador. El administrador tiene además el panel **Estado del pedido** (Nuevo → En análisis →
  En desarrollo → Resuelto / Descartado) con una nota opcional; cada cambio queda en el hilo como
  «Cambió el estado de X a Y».

«Administrador» es lo mismo que en la Bandeja de novedades: `novedades.services.puede_gestionar`
(acceso total), no `is_staff`.

## Criterios de aceptación

| Criterio | Estado |
|---|---|
| Botón «Nuevo pedido» y sección «Mis pedidos» en `/novedades/` | ✅ |
| Formulario con título y comentario obligatorios y etiqueta cerrada | ✅ |
| Se crea en estado Nuevo, con usuario y fecha | ✅ |
| El usuario ve solo sus pedidos; uno ajeno da 404 (también al comentar) | ✅ |
| El administrador ve todos, filtra por estado y etiqueta, con paginación | ✅ |
| El administrador comenta y cambia el estado | ✅ |
| Cada cambio de estado queda en el hilo (quién, cuándo, de qué a cuál) | ✅ |
| Quien levantó el pedido ve estado y comentarios y puede responder | ✅ |
| Solo el administrador cambia el estado (403 para el resto, solo POST) | ✅ |
| Tests de modelos y vistas | ✅ (13 tests nuevos) |

## Archivos

| Archivo | Cambio |
|---|---|
| `novedades/models.py` | `PedidoDesarrollo` (título, etiqueta, comentario, estado, creado_por, fechas) y `ComentarioPedido` (pedido, autor, texto, `estado_anterior`/`estado_nuevo`) |
| `novedades/migrations/0002_pedidodesarrollo_comentariopedido.py` | Crea las dos tablas (sin tocar las existentes) |
| `novedades/forms.py` | `PedidoDesarrolloForm`, `ComentarioPedidoForm`, `CambioEstadoForm` |
| `novedades/views.py` | `pedidos`, `pedido_crear`, `pedido_detalle`, `pedido_estado` |
| `novedades/urls.py` | `novedades:pedidos`, `pedido_crear`, `pedido_detalle`, `pedido_estado` |
| `novedades/admin.py` | Admin de pedidos con los comentarios inline |
| `novedades/templates/novedades/pedidos_lista.html`, `pedido_form.html`, `pedido_detalle.html` | Pantallas nuevas (Taller) |
| `novedades/templates/novedades/lista.html` | Botones «Mis pedidos» y «Nuevo pedido» |
| `core/templates/core/base.html` | Ítem «Pedidos al desarrollo» en el menú |
| `novedades/tests.py` | 13 tests |

## Decisiones técnicas

- **El cambio de estado es un comentario más** (`ComentarioPedido` con `estado_anterior`/`estado_nuevo`),
  así el hilo cuenta toda la historia en orden sin una tabla de auditoría aparte.
- **Visibilidad por queryset:** `_pedidos_visibles(user)` filtra por `creado_por` antes del
  `get_object_or_404`, así un pedido ajeno da 404 y no revela que existe.
- **FK a usuario con `PROTECT`:** no se pierde el historial si se intenta borrar un usuario (en el
  sistema los usuarios se desactivan, no se borran).
- Las rutas no se registran en `ROUTE_ACCESS_MAP`: las ve cualquier usuario logueado, como
  `novedades:lista`; el control fino lo hace cada view.
- Sin avisos por WhatsApp/email, adjuntos ni prioridades (fuera de alcance de REQ-077).
