# REQ-010 — Cuenta corriente por proveedor + forma de pago en gastos

> **Estado:** En desarrollo
> **Fecha:** 2026-04-21
> **Complejidad:** Mediano

## User Story

Como usuario de compras, quiero ver la cuenta corriente de cada proveedor y registrar la forma de pago de la seña o pago inicial de un gasto,
para controlar saldos pendientes, saldos a favor y los medios de pago usados.

## Criterios de Aceptación

### Parte A — Cuenta corriente por proveedor
- [ ] En el menú Reportes existe la opción "Reportes Proveedores"
- [ ] El reporte muestra saldos por proveedor y permite abrir el detalle de cuenta corriente
- [ ] La cuenta corriente muestra compras, señas, pagos y saldo acumulado
- [ ] Si un proveedor queda con saldo a favor, el reporte lo muestra correctamente

### Parte B — Forma de pago en gastos
- [ ] Al cargar un gasto con seña, se puede registrar la forma de pago del anticipo
- [ ] La forma de pago inicial se visualiza en el detalle de la compra
- [ ] En pagos adicionales de compras se sigue pudiendo elegir forma de pago

## Alcance técnico

La cuenta corriente se construye sobre cuentas de tipo `proveedores`, compras, señas y pagos ya existentes en el módulo comercial.