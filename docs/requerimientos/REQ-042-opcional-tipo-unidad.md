# REQ-042 — Opcional de tipo "unidad" (cantidad × precio en el cotizador)

- **Estado:** Implementado
- **Fecha:** 2026-07-27
- **Derivó en:** [FEAT-032](../features/FEAT-032-opcional-tipo-unidad.md)

## Contexto

Los opcionales de fábrica (`plantillas.OpcionalFabrica`) hoy tienen tres tipos: **mosquitero** (cobra `precio_m2 × área` por fórmulas), **premarco** y **otro** (cobran por perfiles + accesorios del despiece). El motor `pricing/services/calculator.py::_calcular_opcionales` ramifica por `tipo`. En el cotizador de presupuestos, `OpcionalesModal` agrega el opcional y el POST manda solo `{id}` por cada uno.

Falta un tipo simple para cobrar cosas que se cuentan **por unidad** (con un costo unitario fijo), donde al cotizar se ingresa la **cantidad** y se suma `cantidad × costo` al total.

**Decisiones de alcance confirmadas (discovery):**
1. **Campo nuevo `precio_unidad`** en `OpcionalFabrica` (no reusar `precio_m2`) → requiere migración.
2. El opcional de tipo unidad se ofrece **para todos los productos** (como el tipo `otro`), sin filtrar por línea ni producto.

## User Story

```
Como vendedor
quiero crear un opcional de tipo "unidad" con un costo unitario
y que al cotizar el sistema me pida la cantidad y sume cantidad × costo al presupuesto
para cobrar ítems que se cuentan por unidad (no por m² ni por despiece).
```

## Criterios de aceptación

- [ ] En `/opcionales/crear/` (y editar) el `tipo` incluye **"Unidad"**, y al elegirlo se carga su **costo unitario** (`precio_unidad`).
- [ ] El opcional de tipo unidad **no** requiere fórmulas, perfiles ni accesorios (secciones ocultas/irrelevantes para ese tipo).
- [ ] En el cotizador, al agregar un opcional de tipo unidad, aparece un campo **cantidad** (default 1, entero ≥ 1).
- [ ] El precio del opcional = `cantidad × precio_unidad`; se suma al total del ítem y aparece en el **desglose** (pantalla y modal de ítems guardados).
- [ ] El opcional de tipo unidad aparece en el selector del cotizador para cualquier producto.
- [ ] Los tipos existentes (mosquitero / premarco / otro) siguen funcionando igual (no-regresión).
- [ ] La cantidad se **persiste** en el ítem (`resultado_json`) para reconstruir al editar.
- [ ] Tests: cálculo por unidad (cantidad × precio), ABM del tipo unidad y no-regresión de los otros tipos.

## Alcance

**Incluye:** campo `precio_unidad` + migración; tipo `unidad` en el modelo y el form/ABM; rama de cálculo en `_calcular_opcionales`; input de cantidad por opcional en el cotizador (frontend React) + persistencia; desglose.

**Fuera de alcance:** filtrado por producto/línea del opcional unidad; unidad en presupuestos PVC (PVC usa precio manual, no pasa por el cotizador de opcionales).

## Análisis de impacto — ¿qué podría romperse?

- [ ] **Payload de opcionales:** hoy el cotizador manda `{id}`; hay que agregar `cantidad` por opcional sin romper el mapeo actual (mosquitero/premarco/otro no usan cantidad).
- [ ] **`_calcular_opcionales`:** agregar rama `tipo == 'unidad'` antes del `else` (que hoy asume perfiles/accesorios) para que unidad no caiga en esa lógica.
- [ ] **`OpcionalesListView`:** el tipo unidad debe entrar en el filtro que devuelve opcionales (hoy `otro` se muestra siempre; unidad igual).
- [ ] **ABM `opcional_form`:** el JS que muestra/oculta secciones por tipo debe contemplar `unidad` (mostrar solo el costo).
- [ ] **Migración:** `precio_unidad` es aditivo con default 0 → los opcionales existentes no se afectan.

## Complejidad estimada

**Mediano** — choice nuevo + campo/migración + rama en el motor + input de cantidad en el frontend con persistencia. Sin modelo nuevo.

## Relación con el backlog

Nueva user story **US-042**. Se apoya sobre los opcionales de fábrica (`plantillas`) y el cotizador de presupuestos (REQ-006 / FEAT-005 / FEAT-007). No reemplaza ningún ítem del backlog.
