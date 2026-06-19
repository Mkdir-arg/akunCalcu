# REQ-032 — Presupuestos PVC siempre en dólares

**Estado:** Implementado
**Fecha:** 2026-06-19
**Origen:** Pedido directo del usuario sobre el módulo de Presupuestos en producción (Railway).

## User Story

Como vendedor, quiero que un presupuesto de PVC se cotice y se muestre siempre en dólares (con su propia cotización), para que el cliente vea el presupuesto en la moneda real en la que se vende el PVC, igual que ya ocurre con las ventas en dólares en `comercial/ventas`.

## Contexto

Hoy el tipo de material PVC permite, ítem por ítem, marcar un checkbox opcional "valor en dólares" + cotización, pero ese dato solo se usa internamente para calcular el precio en pesos: nunca se muestra en el PDF ni en el listado. Todo presupuesto (PVC o Aluminio) se ve y se imprime en pesos.

## Criterios de Aceptación

- [ ] Si `tipo_material = PVC`, el presupuesto es en dólares por definición — se elimina el checkbox "valor en dólares" por ítem.
- [ ] El presupuesto PVC tiene una única cotización USD a nivel de cabecera (no por ítem), que se carga al crear/editar el presupuesto.
- [ ] Los ítems PVC se ingresan en dólares (valor base en USD) y el sistema sigue calculando y guardando el total en pesos como base común para reportes/KPIs existentes.
- [ ] El PDF de un presupuesto PVC muestra los montos (precio unitario, totales, IVA, total final) en USD, usando la cotización de cabecera.
- [ ] El PDF de un presupuesto PVC muestra la cotización USD utilizada.
- [ ] El detalle del presupuesto (`detalle.html`) muestra los montos en USD cuando el presupuesto es PVC.
- [ ] El listado de presupuestos (`lista.html`) muestra, para presupuestos PVC, un badge "USD" igual al patrón visual de `comercial/ventas/list.html` (badge "Venta USD").
- [ ] Los presupuestos de Aluminio no cambian: siguen mostrándose y calculándose en pesos.
- [ ] No es necesario migrar ni dar soporte a presupuestos PVC ya existentes sin cotización cargada (no hay datos así en producción).

## Fuera de alcance

- Cambios en el módulo `comercial/ventas` (ya soporta USD).
- Conversión automática de tipo de cambio en vivo (la cotización se sigue ingresando manualmente).
- Cambios en presupuestos de Aluminio.

## Estimación

Mediano (cambio de modelo + migración, vistas, forms, templates de detalle/lista/PDF).

## Riesgos identificados

- Si se borra el campo `cotizacion_usd` por ítem sin migrar los datos `resultado_json` existentes, los presupuestos PVC ya guardados podrían mostrar inconsistencias al recalcular. (Sin impacto real: no hay datos en producción a preservar, según confirmación del usuario.)
- El total en pesos sigue siendo la "base común" usada por KPIs del listado (`total_monto`, `monto_confirmado`); hay que verificar que esos KPIs no mezclen sin aclarar la moneda cuando hay presupuestos PVC y Aluminio combinados.

## Derivó en

[FEAT-015](../features/FEAT-015-presupuestos-pvc-en-dolares.md)
