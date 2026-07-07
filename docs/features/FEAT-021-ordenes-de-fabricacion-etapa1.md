# FEAT-021 — Órdenes de Fabricación dentro del pedido (Etapa 1)

**Estado:** Implementado
**Fecha:** 2026-07-07
**Requerimiento:** [REQ-035](../requerimientos/REQ-035-ordenes-de-fabricacion-en-pedidos.md) — **Etapa 1 de 2** (modelo + generación + edición). La Etapa 2 (PDF A4 corporativo + datos de contacto en Configuración) queda pendiente.

## Descripción funcional

Cada pedido de fábrica ahora contiene **órdenes de fabricación** (la planilla de fábrica digitalizada), una por cada ítem del presupuesto confirmado, editables desde el sistema.

- **Generación automática:** al confirmar un presupuesto (flujo FEAT-019), dentro de la misma transacción se crea una `OrdenFabricacion` por cada ítem, precargada con: datos del cliente, tipo de abertura / línea / color / tipo de vidrio (del snapshot del cotizador), fecha comprometida (desde `plazo_entrega_dias`) y una fila de medidas (cantidad + "ancho x alto").
- **Alta manual:** botón "Agregar orden" dentro de cualquier pedido (incluye pedidos sin presupuesto). Crea una orden con N° correlativo y redirige a su edición.
- **Edición:** pantalla con todos los campos de la planilla (datos iniciales, cliente, detalle de la abertura, sección Detalle completa, **Estructura** nuevo, Nota) + tabla de "Detalle de medidas" con filas dinámicas (agregar/quitar).
- **Listado:** el detalle del pedido muestra la tabla de órdenes (N° / abertura / medidas) con editar y eliminar (SweetAlert2).

## Criterios de aceptación cubiertos en esta etapa

- [x] Al confirmar un presupuesto se crea una orden por ítem, precargada.
- [x] El detalle del pedido lista las órdenes con acciones.
- [x] Alta manual de órdenes dentro de cualquier pedido.
- [x] N° correlativo global (formato `0001`), fecha y fecha comprometida.
- [x] Edición de todos los campos de la planilla + campo nuevo **Estructura**.
- [x] Panel de Nota multilínea.
- [x] Tabla de medidas editable con filas dinámicas.

Pendiente (Etapa 2): PDF A4 con diseño corporativo, croquis, y datos de contacto del pie desde `ConfiguracionGeneral`.

## Archivos modificados

- `akuna_calc/plantillas/models.py` — modelos `OrdenFabricacion` y `MedidaOrdenFabricacion`
- `akuna_calc/plantillas/migrations/0015_ordenes_de_fabricacion.py` (nueva)
- `akuna_calc/plantillas/forms.py` — `OrdenFabricacionForm`
- `akuna_calc/plantillas/views.py` — `orden_create`, `orden_edit`, `orden_delete`, `_guardar_medidas`; `pedido_detail` con órdenes
- `akuna_calc/plantillas/urls.py`, `admin.py`, `tests.py`
- `akuna_calc/plantillas/templates/plantillas/orden_form.html` (nuevo), `pedido_detail.html` (tabla de órdenes)
- `akuna_calc/presupuestos/views.py` — `_crear_orden_desde_item` y su llamada en `_procesar_confirmacion`
- `akuna_calc/presupuestos/tests.py`
- `akuna_calc/usuarios/access_control.py` — rutas nuevas bajo `despiece.pedidos`

## Decisiones técnicas

- Los campos SI/NO de la planilla se modelan como texto libre corto (la planilla papel mezcla "SI/NO" con "indicar modelo"). Fidelidad sobre rigidez.
- N° de orden correlativo global (`generar_numero()` = max+1), formateado `0001` en presentación.
- La generación vive en `presupuestos/views.py` (que ya conoce el snapshot del ítem e importa de `plantillas`); `plantillas` no importa `presupuestos` (FK por string) para evitar import circular.
- Las filas de medidas se reemplazan en cada guardado (borrar + recrear desde los arrays del POST); se descartan filas sin ningún texto.
- Sin librerías nuevas; el alta dinámica de filas es JS vanilla.

## Validación

- `python manage.py test plantillas presupuestos --settings=akuna_calc.settings_test_sqlite`
- Resultado: **114 tests OK** (10 nuevos: generación automática con precarga + CRUD de órdenes), sin regresiones.

## Pendiente de deploy

- Migración `plantillas/0015` pendiente de aplicar en Docker/Railway (solo agrega 2 tablas; sin riesgo sobre datos existentes).
