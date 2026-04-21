# REQ-009 — Registro de dólares en cobros + Estado obligatorio a Colocado

> **Estado:** En desarrollo
> **Fecha:** 2026-04-01
> **Complejidad:** Mediano

## User Story

Como vendedor, quiero poder registrar si un cobro fue en dólares (monto USD + cotización usada)
y que cuando el saldo llegue a 0 se me obligue a cambiar el estado a "Colocado",
para tener reportes de dólares ingresados y asegurar que las ventas cobradas avancen de estado.

## Criterios de Aceptación

### Parte A — Registro de cobro en dólares
- [ ] Al registrar un cobro, puedo marcar opcionalmente "Pagó en dólares"
- [ ] Si marco esa opción, aparecen campos: monto en USD y cotización utilizada
- [ ] El monto en pesos sigue siendo lo que cuenta para el saldo (la contabilidad no cambia)
- [ ] En el historial de pagos se ve si un pago fue en USD, con el monto USD y cotización registrada
- [ ] Se puede obtener un reporte/consulta de cuántos dólares entraron

### Parte B — Obligar cambio de estado a "Colocado" cuando saldo = 0
- [ ] Cuando el saldo llega a 0, aparece un popup SweetAlert2 obligatorio que pida cambiar el estado a "Colocado"
- [ ] El popup no se puede cerrar sin confirmar el cambio
- [ ] Aplica sin importar el estado actual de la venta
- [ ] El banner actual opcional de "Entregado" se reemplaza por este flujo obligatorio

## Contexto

Evoluciona la US-004 (popup sugerido → obligatorio, estado target: Colocado en vez de Entregado).
Los dólares registrados son informativos; la contabilidad sigue operando en pesos.
