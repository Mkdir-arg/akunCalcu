# REQ-012 — Reporte de cobranzas por cobro individual

> **Estado:** En desarrollo
> **Fecha:** 2026-04-22
> **Complejidad:** Mediano

## User Story

Como usuario del módulo comercial, quiero un reporte separado de cobranzas que muestre cada ingreso registrado como un movimiento individual,
para controlar todos los cobros realizados aunque una misma venta tenga varios pagos parciales.

## Criterios de Aceptación

- [ ] Existe un reporte nuevo llamado "Cobranzas" separado del reporte de ventas
- [ ] El reporte muestra cobros individuales y no ventas consolidadas
- [ ] Si una venta tiene múltiples pagos, cada pago aparece como una fila separada
- [ ] El reporte puede incluir la seña inicial como movimiento separado cuando corresponda
- [ ] Cada fila muestra como mínimo: fecha, pedido, cliente, razón social, forma de pago, monto y tipo de comprobante
- [ ] El reporte permite filtrar por fecha, cliente, razón social, estado de la venta y tipo de factura
- [ ] El total del reporte suma movimientos de cobranza, no totales de ventas
- [ ] El reporte deja claro que una misma venta puede aparecer varias veces si tuvo múltiples cobros

## Alcance técnico

Este reporte reutiliza la información de `Venta` y `PagoVenta`, pero se presenta como vista independiente del reporte de ventas. Debe diferenciar claramente entre "venta" y "cobranza" para evitar confusión funcional y contable.