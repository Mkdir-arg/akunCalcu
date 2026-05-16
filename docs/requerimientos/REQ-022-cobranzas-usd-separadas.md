# REQ-022 — Visualización separada de cobranzas en USD

> **Estado:** En desarrollo
> **Fecha:** 2026-05-16
> **Complejidad:** Mediano

## User Story

Como usuario del módulo comercial, quiero visualizar las cobranzas en USD dentro del reporte de cobranzas
para distinguir claramente los cobros en dólares sin mezclarlos con los totales expresados en pesos.

## Criterios de Aceptación

- [ ] El reporte de cobranzas muestra una columna específica `Cobranzas USD`
- [ ] La columna `Cobranzas USD` solo informa los importes cobrados en dólares
- [ ] Los importes de la columna `Cobranzas USD` no se suman al total general en pesos del reporte
- [ ] El reporte mantiene separada la visualización de cobranzas en pesos y cobranzas en USD
- [ ] Existen filtros para identificar fácilmente cobranzas registradas en USD
- [ ] El usuario puede combinar el filtro de USD con los filtros existentes del reporte
- [ ] La incorporación de `Cobranzas USD` no altera el cálculo actual de totales en pesos
- [ ] La vista deja claro a nivel visual que los importes en USD son informativos y separados del total en pesos

## Contexto

Este requerimiento extiende el trabajo de [REQ-009](./REQ-009-dolares-cobro-estado-colocado.md) y [REQ-012](./REQ-012-reporte-cobranzas.md).
El objetivo no es convertir ni consolidar monedas, sino exponer de forma separada la cobranza en USD dentro del reporte existente de cobranzas.