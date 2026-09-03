# REQ-048 — Elevación técnica con cotas en cotizador, PDF y presupuesto

- **Estado:** Implementado
- **Fecha:** 2026-08-26 (creado retroactivamente el 2026-09-03; el trabajo se hizo sin REQ)
- **Feature:** [FEAT-038](../features/FEAT-038-elevacion-tecnica-cotas.md)
- **Apps afectadas:** `presupuestos`, `static/js`

## User Story

Como **vendedor** quiero **ver el plano técnico de cada abertura con sus medidas** en el cotizador
para **verificar lo que estoy cotizando**, y como **cliente** quiero **recibir ese plano en el
presupuesto** para **entender sin ambigüedad qué se me está vendiendo**.

## Contexto

El cotizador tenía un visor 3D sin medidas. La fábrica usa planos 2D vista de frente con cotas
(alto a la izquierda, anchos por paño y total abajo, composición del vidrio dentro del paño,
mosquitero rayado). El PDF del presupuesto no tenía ningún dibujo.

## Criterios de Aceptación

- [x] Las cotas de paño parten el ancho total y su suma siempre cierra contra él
- [x] Los tres planos de referencia (1790×1050 2 hojas, 3630×1050 2 hojas, 950×1050 paño fijo) dan los valores exactos
- [x] En el cotizador hay pestañas 3D / Plano en el mismo alto, y un toggle de cotas sobre el 3D
- [x] En el PDF el plano de cada ítem va en un anexo, con la tabla de precios intacta y los ítems numerados
- [x] En la página del presupuesto cada ítem muestra una miniatura
- [x] Los ítems terciarizados, PVC simple y "No dibujar" no tienen plano
- [x] Los ítems anteriores siguen imprimiendo sin cambios

## Fuera de alcance (resuelto después en REQ-047)

- Símbolos de apertura y color del perfil: dependían de datos que no existían.
