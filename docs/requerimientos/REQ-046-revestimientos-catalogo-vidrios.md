# REQ-046 — Revestimientos en el catálogo de vidrios

- **Estado:** Implementado
- **Fecha:** 2026-08-18
- **Feature:** [FEAT-036](../features/FEAT-036-revestimientos-catalogo-vidrios.md)
- **Apps afectadas:** `pricing`, `presupuestos`

## User Story

Como **vendedor que cotiza aberturas con travesaños divisores** quiero que **al elegir si una
sección es de vidrio o ciega el selector me ofrezca solo los materiales de ese tipo** para
**cargar el relleno de cada sección desde un único catálogo, sin mantener dos ABMs distintos**.

## Contexto

El editor de secciones ya tenía dos botones (Vidrio / Ciego) y ya conmutaba el selector, pero cada
uno leía de un catálogo distinto: los vidrios de la tabla legacy `vidrios` (por `codigo`) y los
ciegos del modelo `MaterialCiego` (por `id`).

`MaterialCiego` nació con REQ-041/ADR-016 pero **nunca se puso en servicio**: su pantalla de ABM no
tenía link desde ningún menú, el catálogo nunca se cargó y por lo tanto el botón "Ciego
(chapa/panel)" mostraba una lista vacía en producción.

## Criterios de Aceptación

- [x] El catálogo de vidrios tiene un campo **Tipo** con valores *Vidrio* y *Revestimiento*
- [x] Todos los registros existentes quedan clasificados como **Vidrio**
- [x] Al elegir "Vidrio" en una sección, el selector ofrece solo los `tipo='vidrio'`
- [x] Al elegir "Ciego (chapa/panel)", ofrece solo los `tipo='revestimiento'`
- [x] El selector de vidrio principal de la abertura no ofrece revestimientos
- [x] Los presupuestos ya guardados con secciones ciegas siguen cotizando e imprimiendo
- [x] El PDF sigue diciendo "VIDRIO Y REVESTIMIENTO" donde corresponde (no se rompe FIX-023)

## Decisión de arquitectura

Ver [ADR-018](../team/decisions.md) — se reemplaza `MaterialCiego` en lugar de hacerlos convivir.
