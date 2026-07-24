# REQ-039 — Imagen 3D por ítem en la lista y en el PDF del presupuesto (Fase 2 del graficador 3D)

- **Estado:** En desarrollo
- **Fecha:** 2026-07-24
- **Derivó en:** —
- **Continúa:** [REQ-038](./REQ-038-graficador-3d-aberturas-en-cotizador.md) / FEAT-030

## Contexto

FEAT-030 agregó un visor 3D **en vivo** dentro del modal de ítem (al calcular). Fase 2 lleva ese diseño a donde el cliente y el vendedor lo consultan después: la **lista de ítems** del presupuesto y el **PDF**.

Como el PDF se arma en el servidor y el 3D se renderiza en el navegador (WebGL), la imagen se **captura en el cliente** al guardar el ítem y se **persiste** en el `ItemPresupuesto`. Se reutiliza el `snapshot_item` (que ya guarda todos los parámetros).

## User Story

```
Como vendedor
quiero que el diseño 3D de cada ítem quede guardado como imagen y se vea en la
lista de ítems y en el PDF del presupuesto
para que el cliente reciba una representación visual de cada abertura cotizada.
```

## Criterios de aceptación

- [ ] Al **guardar** (agregar/editar) un ítem de aluminio con precio calculado, se **captura una imagen del 3D** y se persiste en el ítem.
- [ ] En la **lista de ítems** del presupuesto (`detalle.html`), cada ítem muestra su **miniatura 3D**.
- [ ] En el **PDF** del presupuesto, cada ítem incluye su **imagen 3D**.
- [ ] El `snapshot_item` guarda `tipo_abertura` + `cantidad_hojas` (para contexto y futura regeneración).
- [ ] Ítems **sin imagen** (PVC, terciarizados, ítems viejos previos a esta feature) **no rompen** la lista ni el PDF: simplemente se muestran sin imagen.
- [ ] No se rompe agregar / editar / eliminar ítems, el cálculo, ni la generación actual del PDF.

## Alcance

**Incluye:** captura de PNG en el navegador (nuevo método en `viewer3d.js`), persistencia por ítem, render de la miniatura en la lista y en el PDF, y `tipo_abertura` + `cantidad_hojas` en el snapshot.

**Fuera de alcance:** color de perfil y mano de apertura como dato de entrada nuevo; afinado del clasificador con datos de producción; regeneración masiva de imágenes para ítems históricos.

## Complejidad estimada

**Grande** — captura cliente → persistencia (con decisión de almacenamiento) → render en lista y PDF, tocando viewer, modal, model/almacenamiento, views y dos templates.

## Relación con el backlog

Nueva **US-039**, continuación de US-038 (FEAT-030).
