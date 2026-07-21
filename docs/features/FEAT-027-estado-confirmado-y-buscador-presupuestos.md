# FEAT-027 — Cambiar estado desde Confirmado + buscador único en presupuestos

**Estado:** Implementado
**Fecha:** 2026-07-21
**Módulo:** `presupuestos`

Agrupa dos mejoras de UX del módulo de presupuestos pedidas en la misma sesión.

## A) Cambiar el estado de un presupuesto Confirmado

### Descripción funcional
Antes, un presupuesto en estado **Confirmado** quedaba bloqueado y no se podía cambiar de estado (había que tocar la base a mano para deshacer). Ahora **sí se puede cambiar** el estado de un confirmado.

- Al salir de "confirmado" **solo cambia la etiqueta de estado**: la **Venta** y el **Pedido de fábrica** generados al confirmar **siguen existiendo** (decisión del usuario). Se muestra una confirmación SweetAlert2 avisando esto.
- **"Cancelado" sigue bloqueado** (no se pidió tocarlo).
- **Re-confirmar** un presupuesto que ya tiene venta solo re-marca el estado: **no duplica** la venta ni el pedido.

### Criterios cumplidos
- [x] Un confirmado puede pasar a cualquier otro estado.
- [x] La venta y el pedido no se borran al des-confirmar (se avisa).
- [x] Cancelado sigue bloqueado; re-confirmar no duplica.

## B) Buscador único del listado

### Descripción funcional
El cuadro "Buscar cliente" del listado (`/presupuestos/`) pasó a ser un **buscador único** que matchea cualquier dato de la tabla: **número**, **cliente** (nombre/apellido/razón social), **estado**, **usuario creador** (solo si el rol tiene permiso de ver esa columna) y **total** (si el término es un número). Los filtros de dropdown (Estado / Creado por) siguen funcionando y se combinan.

### Criterios cumplidos
- [x] Busca por número, cliente, estado, usuario y total.
- [x] La búsqueda por creador respeta el permiso.
- [x] No rompe con entradas raras (inf/nan/números gigantes → se ignoran, ver nota técnica).

## Archivos modificados

- `akuna_calc/presupuestos/views.py` — `cambiar_estado` (permite salir de confirmado, cancelado bloqueado, re-confirmar sin duplicar); `lista` (buscador único `q`); helper `_termino_a_decimal`.
- `akuna_calc/presupuestos/templates/presupuestos/detalle.html` — panel "Cambiar estado" visible en confirmado + confirmación al des-confirmar.
- `akuna_calc/presupuestos/templates/presupuestos/lista.html` — input único `q`.
- `akuna_calc/presupuestos/tests.py` — tests de ambos.

## Decisiones técnicas

- **Sin migración.**
- Se decidió (con el usuario) que des-confirmar **no** deshace la Venta/Pedido; solo cambia la etiqueta. Queda a cargo del usuario dar de baja esos objetos si ya no corresponden.
- `_termino_a_decimal` sanitiza el término antes de buscar por `total`: descarta `inf`/`nan` y montos ≥ 1e12 (fuera del rango de `total`, `max_digits=14`) para no romper el lookup en MySQL de producción (en SQLite no se notaba — ver [[tests-locales-sqlite]]).
- La búsqueda por `created_by` solo se aplica si el usuario tiene permiso de ver la columna Usuario (`_puede_ver_creador`).
