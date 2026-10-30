# FEAT-048 — Circuito de pedidos de fábrica (Etapa 1)

- **Estado:** Implementado, Etapa 1 (rama `feat/req-063-pedidos-fabrica`, sin desplegar a `main`)
- **Fecha:** 2026-10-30
- **Requerimiento:** [REQ-063](../requerimientos/REQ-063-circuito-pedidos-fabrica.md)
- **Decisión:** [ADR-025](../team/decisions.md)
- **Apps:** `plantillas` (núcleo), `presupuestos`, `usuarios` (permisos)
- **Migración:** sí, `plantillas/0017_circuito_pedidos` (schema + migración de datos reversible); se aplica sola en el deploy

## Qué hace

### Estados del pedido

`Recibido → En fábrica → En producción → Terminado → Entregado`, y `Cancelado` en cualquier momento antes de entregar.
Al confirmar el presupuesto el pedido nace en **Recibido** y sus órdenes en **Por fabricar**. «En producción» y
«Terminado» **no se eligen**: se calculan a partir de las etapas de las órdenes (`recalcular_estado()`).

### Etapas de cada orden

`Por fabricar → Corte → Armado → Vidriado → Lista` (más `Anulada`). Se cambian desde el detalle del pedido; retroceder
exige nota. Cada cambio queda en `HistorialPedidoFabrica` con usuario y fecha. Una orden «Lista» que retrocede saca
al pedido de «Terminado».

### Liberar, cancelar, entregar

- **Liberar a fábrica:** el detalle muestra el checklist de faltantes por orden (medida, cantidad, línea, color, vidrio,
  hojas y lado, fecha comprometida). El botón solo se habilita con el checklist vacío. Si la venta no tiene seña, se advierte y
  «Liberar igual» pide confirmación y motivo (máx. 500 caracteres), que va al historial. Al liberar, las órdenes quedan en Rev. 1.
- **Cancelar:** motivo obligatorio; las órdenes pasan a «Anulada». Si el presupuesto confirmado pasa a cancelado, el pedido
  se cancela solo (y el mensaje advierte si ya estaba en producción). Si el pedido ya se había cerrado en paralelo, se tolera.
- **Entregar / colocar:** desde «Terminado»; copia `entregado` o `colocado` a `Venta.estado`.
- **Listado:** filtro por estado con contadores y marca de atrasados.

### Orden liberada: revisiones

Editar una orden de un pedido liberado exige `fabrica.pedidos_gestion` y un motivo. Sube `revision` (Rev. 2, 3…), prende
`reimpresion_pendiente` y avisa a los responsables de fábrica. El aviso se apaga **solo** con el botón «Ya la reimprimí»
(POST a `orden_reimpresa`), y únicamente si la revisión posteada coincide con la vigente. Abrir el PDF no lo apaga.
`orden_edit` es atómica (`select_for_update`, `update_fields`): no pisa la etapa si el taller avanzó mientras se editaba.

### PDF

- **Orden:** misma identidad (azul `#145ea7`, A4). Suma el bloque Detalle precargado del cotizador, casillas SÍ / NO donde el
  dato falta (celdas con borde, no el carácter ☐), línea de contexto `Pedido PF-… · Presup. … · Orden N de M · Rev. R` y control
  de etapas al pie (Corte · Armado · Vidriado · Control).
- **Pedido completo:** `pedido_pdf` — carátula (cliente, cantidad de órdenes, fecha comprometida, estado) y una hoja A4 por orden.
- La hoja se partió en `_orden_hoja.html` + `_orden_pdf_estilos.html`; `orden_pdf.html` y `pedido_pdf.html` la incluyen.
- Filtro `si_no` en `templatetags/orden_pdf.py`.

### Precarga desde el presupuesto

`services/precarga.py::detalle_desde_snapshot()` completa mosquitero y modelo, premarco, tipo de marco, modelo de hoja,
cantidad de hojas, lado, travesaño y «Atendido por» (creador del presupuesto). Si el snapshot no trae el dato (PVC,
terciarizado, snapshots viejos), el campo queda vacío y el PDF muestra la casilla.

### Numeración

`PedidoFabrica.generar_numero()` reemplaza `count()+1` (toma el mayor `PF-NNNN` + 1). El `unique` de `numero` sigue de red de
seguridad y la confirmación del presupuesto y `orden_create` reintentan ante `IntegrityError`. `pedido_create` usa
`PedidoFabricaForm`.

### Permisos

| Código | Puede |
|---|---|
| `despiece.pedidos` (existente) | Ver, editar órdenes con el pedido en Recibido, imprimir |
| `fabrica.pedidos_gestion` (nuevo) | Liberar, cancelar, entregar, modificar orden liberada, cambiar etapa, «Ya la reimprimí» |
| `fabrica.tablero` (nuevo) | Cambiar etapa de las órdenes y marcar reimpresión (el tablero en sí es Etapa 2) |

Los usuarios actuales no pueden liberar ni entregar hasta que un admin les asigne `fabrica.pedidos_gestion`. Los admin tienen todo.

### Tiempo real

`plantillas/live.py` registra `pedidos_fabrica` y `ordenes_fabrica` (permisos `despiece.pedidos`, `fabrica.pedidos_gestion`,
`fabrica.tablero`). Las escrituras con `QuerySet.update()` pasan `updated_at` a mano porque `update()` no dispara `auto_now`.

## Criterios cumplidos

Los de Etapa 1 de [REQ-063 § 9](../requerimientos/REQ-063-circuito-pedidos-fabrica.md). Sobre el 403: el
`RouteAccessMiddleware` redirige con 302 + mensaje (patrón del sistema); las vistas además lanzan `PermissionDenied` (403)
si se las llama sin pasar por el middleware.

## Archivos

**Nuevos** (`akuna_calc/plantillas/`): `services/circuito.py`, `services/precarga.py`, `migrations/0017_circuito_pedidos.py`,
`templatetags/orden_pdf.py`, `tests_circuito.py`, `templates/plantillas/_orden_hoja.html`, `_orden_pdf_estilos.html`, `pedido_pdf.html`.

**Modificados:** `plantillas/{models,forms,views,urls,live}.py`, templates `_pedido_tabla.html`, `orden_form.html`,
`orden_pdf.html`, `pedido_detail.html`, `pedido_form.html`; `presupuestos/views.py` (precarga, reintento de número, cancelación en
cascada), `presupuestos/tests.py`, `usuarios/access_control.py` (2 códigos y rutas nuevas).

Rutas nuevas (`plantillas:`): `pedido_liberar`, `pedido_cancelar`, `pedido_entregar`, `pedido_pdf`, `orden_etapa`, `orden_reimpresa`.

## Decisiones técnicas

- Toda la lógica de transiciones vive en `services/circuito.py` (`transaction.atomic()` + `select_for_update()` + fila de historial). Ver ADR-025.
- Hallazgos del Reviewer (9), todos corregidos: `orden_edit` atómica sin pisar la etapa; `updated_at` en `update()`; live con los 3
  permisos; reimpresión solo por POST con revisión; reintento ante `IntegrityError`; `PermissionDenied` en las vistas; aviso a
  responsables al revisar; `_cancelar_pedidos_fabrica` tolera `ValidationError`; `revisar_orden` relee la orden bloqueada; liberar valida el largo del motivo.

## Tests

`plantillas` + `presupuestos`: 298 OK (47 nuevos, en `plantillas/tests_circuito.py` y `presupuestos/tests.py`). Suite completa:
805 tests con 25 failures + 9 errors, igual a la línea base previa (`comercial` y `pricing`, ajenos).

## Pendientes

- **Etapa 2 del REQ** sin hacer: tablero de fábrica, semáforo, usable en celular y QR en el PDF (M6).
- **Etapa 3:** planos en la orden (M3, M7).
- Verificación visual en navegador (Playwright) no hecha.
- Si la orden no tiene datos del cliente, las columnas del PDF se achican (detalle previo; se ofrece como mejora).
- Migración a aplicar en prod: `plantillas/0017`. Los pedidos viejos en `BORRADOR` quedan en Recibido y hay que liberarlos.
- Asignar `fabrica.pedidos_gestion` y `fabrica.tablero` a los usuarios desde el ABM.
