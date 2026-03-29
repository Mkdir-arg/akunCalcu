# REQ-007 — Pagos Parciales en Compras

> **Estado**: Implementado
> **Fecha**: 2026-03-28
> **Derivó en**: FEAT-006

## Descripción

Replicar la lógica de seña + pagos parciales + saldo dinámico que existe en Ventas, aplicándola al módulo de Compras. Incluye vista de detalle con diseño similar al de ventas.

## User Story

Como administrador, quiero registrar compras con monto total, seña y pagos parciales, y ver el detalle de cada compra con el saldo pendiente, para llevar el mismo control de deuda que tengo en ventas pero del lado de proveedores.

## Criterios de Aceptación

- [x] El modelo Compra tiene campos `valor_total`, `sena` y `saldo` (calculado automáticamente)
- [x] Existe un modelo `PagoCompra` para registrar pagos parciales
- [x] El saldo se recalcula automáticamente: `saldo = valor_total - seña - suma(pagos)`
- [x] No se puede registrar un pago mayor al saldo pendiente
- [x] El formulario de compra permite ingresar valor total y seña
- [x] Existe vista de detalle con KPIs, barra de progreso, registrar pago, historial, notas internas
- [x] Desde el listado se accede al detalle con botón "Ver"
- [x] El campo `importe_abonado` se migró a `valor_total` sin perder datos
- [x] Las compras existentes mantienen sus datos

## Complejidad

Grande

## Link

[FEAT-006](../features/FEAT-006-pagos-parciales-compras.md)
