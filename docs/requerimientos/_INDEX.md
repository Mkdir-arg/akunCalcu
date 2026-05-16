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
| [REQ-011](./REQ-011-navegacion-contexto-y-reporte-ventas-facturado.md) | Navegación con retorno contextual + reporte de ventas por importe facturado | En desarrollo | 2026-04-21 | — |
| [REQ-012](./REQ-012-reporte-cobranzas.md) | Reporte de cobranzas por cobro individual | En desarrollo | 2026-04-22 | — |
| [REQ-013](./REQ-013-reporte-ventas-todos.md) | Reporte de ventas muestra Blanco y Negro | En desarrollo | 2026-04-23 | — |
| [REQ-014](./REQ-014-premarco-en-opcionales-y-formulas-marcos.md) | Tipo Premarco en opcionales + relaciones con Líneas y Perfiles | En desarrollo | 2026-05-02 | — |
| [REQ-015](./REQ-015-vista-previa-pdf-ventas.md) | Vista previa de PDF desde ventas | En desarrollo | 2026-05-03 | — |
| [REQ-016](./REQ-016-rediseno-pdf-presupuestos-descripcion-narrativa.md) | Rediseño del PDF de presupuestos con descripción narrativa por ítem | Implementado | 2026-05-04 | FEAT-008 |
| [REQ-017](./REQ-017-compras-y-pagos-de-compra-en-dolares.md) | Compras y pagos de compra en dólares | En desarrollo | 2026-05-04 | — |
| [REQ-018](./REQ-018-recargos-obra-nueva-renovacion-y-fix-desglose-presupuesto.md) | Recargos por obra nueva o renovación + fix de desglose en presupuestos | En desarrollo | 2026-05-07 | — |
| [REQ-019](./REQ-019-roles-permisos-por-modulo-y-opcion.md) | Roles y permisos por módulo y opción | Implementado | 2026-05-09 | FEAT-009 |
| [REQ-020](./REQ-020-auditoria-actividad-usuarios.md) | Auditoría de actividad de usuarios | En desarrollo | 2026-05-10 | — |
| [REQ-021](./REQ-021-confirmacion-reemplazo-accesorios-vidrios.md) | Confirmación al reemplazar accesorios o vidrios en configurador de hojas | En desarrollo | 2026-05-15 | — |
| [REQ-022](./REQ-022-cobranzas-usd-separadas.md) | Visualización separada de cobranzas en USD | En desarrollo | 2026-05-16 | — |
| [REQ-023](./REQ-023-edicion-masiva-precios-perfiles.md) | Edición masiva de precios en perfiles | En desarrollo | 2026-05-16 | — |
