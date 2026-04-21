s# Requerimientos — AkunCalcu

> Los requerimientos son ideas que pasaron por el análisis del equipo funcional (/idea) y están listas para entrar al flujo de desarrollo (/feature).
> Este archivo se actualiza al crear o cambiar el estado de un requerimiento.

## Estados posibles

| Estado | Significado |
|--------|-------------|
| Borrador | Idea inicial, sin analizar todavía |
| En análisis | El equipo funcional (PO + Arq) lo está evaluando |
| Aprobado | Listo para entrar a un sprint con /feature |
| En desarrollo | Tiene un FEAT-XXX asignado y está siendo implementado |
| Implementado | Derivó en una feature completada |
| Descartado | Se decidió no hacerlo |

---

## Tabla de requerimientos

| ID | Nombre | Estado | Fecha | Derivó en |
|----|--------|--------|-------|-----------|
| [REQ-001](./REQ-001-documento-v1.md) | Documento V1 del sistema | Implementado | 2026-03-04 | — |
| [REQ-002](./REQ-002-pedidos-telegram.md) | Pedidos por voz via Telegram | Implementado | 2026-03-04 | FEAT-001 |
| [REQ-003](./REQ-003-crud-fabrica-abm.md) | CRUD Fábrica ABM | Implementado | 2026-03-05 | FEAT-002 |
| [REQ-004](./REQ-004-formulas-marcos.md) | Sistema de Fórmulas para Marcos | Implementado | 2026-03-06 | FEAT-003 |
| [REQ-005](./REQ-005-detalle-cliente.md) | Página de detalle de cliente | En desarrollo | 2026-03-06 | FEAT-004 |
| [REQ-006](./REQ-006-modulo-presupuestos.md) | Módulo de Presupuestos | Implementado | 2026-03-11 | FEAT-005 |
| [REQ-007](./REQ-007-pagos-parciales-compras.md) | Pagos Parciales en Compras | Implementado | 2026-03-28 | FEAT-006 |
| [REQ-008](./REQ-008-mejora-presupuestos-cotizador.md) | Mejora Presupuestos: Paridad con Cotizador + UI | Implementado | 2026-03-30 | FEAT-007 |
| [REQ-009](./REQ-009-dolares-cobro-estado-colocado.md) | Registro de dólares en cobros + Estado obligatorio a Colocado | En desarrollo | 2026-04-01 | — |
| [REQ-010](./REQ-010-cuenta-corriente-proveedores.md) | Cuenta corriente por proveedor + forma de pago en gastos | En desarrollo | 2026-04-21 | — |
