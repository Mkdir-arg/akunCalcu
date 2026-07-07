# FEAT-020 — Eliminación del módulo de despiece y transformación de Pedidos de Fábrica

**Estado:** Implementado
**Fecha:** 2026-07-07
**Requerimiento:** [REQ-036](../requerimientos/REQ-036-eliminar-modulo-despiece.md)

## Descripción funcional

Se eliminó por completo el módulo obsoleto de **despiece** de la app `plantillas` (Calcular, Configurar Plantillas, Historial y los ítems de despiece dentro de los pedidos), dejando **Pedidos de Fábrica** como único módulo visible, transformado en el contenedor donde vivirán las Órdenes de Fabricación (REQ-035).

Cambios visibles para el usuario:
- El menú ya no muestra "Calcular", "Configurar Plantillas" ni "Historial"; queda la entrada única **Pedidos de Fábrica**.
- `/plantillas/` redirige al listado de pedidos.
- El detalle del pedido es una pantalla limpia: datos de cabecera, estado, y links al **presupuesto de origen** y a la **venta asociada** (FEAT-019).
- El listado de pedidos muestra la columna "Presupuesto" (origen del pedido, o "Manual").
- Los **Opcionales de Fábrica** y todos los ABMs del grupo Fábrica quedaron intactos (los usa el cotizador de presupuestos).

## Criterios de aceptación cumplidos

- [x] Menú sin Calcular / Configurar Plantillas / Historial; Pedidos de Fábrica visible y funcional.
- [x] `/plantillas/` redirige al listado de pedidos.
- [x] Detalle del pedido sin rastros de despiece, con link al presupuesto de origen.
- [x] Grupo Fábrica completo funcionando (opcionales, ABMs, cotizador, presupuestos — validado por tests).
- [x] Confirmar un presupuesto (FEAT-019) sigue creando venta + pedido.
- [x] Migración de borrado creada; `manage.py check` y tests sin referencias rotas.
- [x] Roles con permisos `despiece.*` huérfanos no rompen nada.

## Qué se eliminó

- **Modelos** (+ tablas con sus datos): `ProductoPlantilla`, `CampoPlantilla`, `CalculoEjecucion`, `PedidoFabricaItem`, `PedidoFabricaFila` — migración `0014_eliminar_modelos_despiece`.
- **16 views** y sus URLs (ABM plantillas, campos, probar, calcular ×3, historial, ítems/filas de pedidos ×6). `views.py` pasó de 491 a 55 líneas.
- **8 templates** del despiece + `templatetags/plantillas_tags` + `services/formula_engine.py` (motor Shunting Yard) + comando `seed_plantillas` + forms del despiece + registros del admin.
- **Permisos** `despiece.calcular`, `despiece.plantillas`, `despiece.historial` del registro central (el menú se limpia solo). El code `despiece.pedidos` se conservó para no invalidar roles guardados.

## Archivos modificados

- `akuna_calc/plantillas/models.py`, `views.py`, `urls.py`, `forms.py`, `admin.py`, `tests.py`
- `akuna_calc/plantillas/migrations/0014_eliminar_modelos_despiece.py` (nueva)
- `akuna_calc/plantillas/templates/plantillas/pedido_detail.html` (reescrito), `pedido_list.html` (columna Presupuesto), `base_plantillas.html` (título)
- `akuna_calc/usuarios/access_control.py` (menú/permisos)
- Eliminados: `services/`, `management/`, `templatetags/`, 8 templates del despiece

## Decisiones técnicas

- La app conserva el nombre `plantillas` (renombrarla implicaba migraciones invasivas sin beneficio funcional). Ver ADR-013.
- La raíz de la app quedó como view `index` con redirect (registrada bajo `despiece.pedidos`).
- El listado de pedidos usa `select_related('presupuesto')`.

## Validación

- `manage.py check`: sin problemas.
- Suites `plantillas` + `presupuestos`: **104 tests OK** (6 nuevos de Pedidos de Fábrica; los de Opcionales intactos).
- Suite `pricing`: solo el baseline preexistente de SQLite (verificado contra el código original vía `git stash` — cero regresiones).
- Barrido global: ninguna referencia viva a los modelos/views eliminados fuera de las migraciones históricas.

## Pendiente de deploy

- Migración `plantillas/0014` pendiente de aplicar en Docker/Railway. ⚠️ **Al aplicarla se borran definitivamente** las plantillas de despiece, el historial de cálculos y los ítems/filas de pedidos existentes (confirmado por el usuario el 2026-07-07).
