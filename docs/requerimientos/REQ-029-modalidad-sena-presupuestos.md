# REQ-029 — Modalidad de seña en presupuestos

**Estado:** Implementado  
**Fecha:** 2026-05-26  
**Origen:** RF-002 (Prioridad alta, módulo Presupuestos).

## User Story

Como vendedor, quiero seleccionar una modalidad de seña al generar un presupuesto para definir claramente el porcentaje de adelanto y saldo a cobrar.

## Criterios de Aceptación

- [ ] En la pantalla de detalle/edición del presupuesto se muestra un menú desplegable para modalidad de seña.
- [ ] El selector se ubica debajo del bloque de "Configuración de obra" (debajo de "Tipo / Sin definir") en el panel lateral.
- [ ] El selector mantiene el mismo diseño visual que los demás campos del panel (tipografía, bordes, espaciados y estados).
- [ ] El selector ofrece exactamente estas opciones predefinidas:
  - [ ] 50% adelanto / 50% saldo.
  - [ ] 70% adelanto / 30% saldo.
- [ ] La modalidad seleccionada se guarda en el presupuesto.
- [ ] Al volver a abrir un presupuesto, el selector muestra la modalidad previamente guardada.
- [ ] Si no se seleccionó una modalidad antes, el sistema muestra un valor por defecto definido en implementación.

## URL de referencia

- https://akun.pythonanywhere.com/presupuestos/26/?_return_to=%2Fpresupuestos%2F

## Fuera de alcance

- Cálculo automático de cuotas adicionales.
- Nuevas modalidades editables por usuario desde configuración.

## Estimación

Pequeño.

## Riesgos identificados

- Si la modalidad impacta textos de impresión/PDF y no se actualizan, puede haber inconsistencias entre UI y documento final.
- Si se agrega como campo obligatorio sin migración adecuada, puede romper registros históricos de presupuestos.

## Derivó en

[FEAT-013](../features/FEAT-013-modalidad-sena-presupuestos.md)