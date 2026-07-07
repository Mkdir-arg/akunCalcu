# REQ-034 — Confirmación de presupuesto genera venta y pedido de fábrica

**Estado:** Implementado
**Fecha:** 2026-07-07
**Origen:** Pedido directo del usuario (análisis del proceso presupuestos → ventas → pedidos de fábrica).

## User Story

Como vendedor, quiero que al confirmar un presupuesto el sistema me pida la seña cobrada y genere automáticamente la venta en Comercial y el pedido de fábrica en Plantillas, para no cargar los mismos datos tres veces y que todo quede vinculado desde el origen.

## Criterios de Aceptación

- [ ] En el detalle del presupuesto, al elegir estado "Confirmado" y presionar "Actualizar estado", se abre un popup (SweetAlert2) que pide el monto de la seña antes de ejecutar el cambio.
- [ ] Los demás cambios de estado (Enviado, Vencido, Cancelado) siguen funcionando como hoy, sin popup.
- [ ] El popup muestra el total del presupuesto como referencia y precarga el monto sugerido según la modalidad de seña guardada (50% o 70% del total), editable.
- [ ] Moneda de la seña según material: PVC → USD (con la cotización del presupuesto); Aluminio → pesos.
- [ ] La seña es obligatoria: monto mayor a 0 para poder confirmar.
- [ ] Al aceptar, en una única operación atómica:
  - [ ] El presupuesto pasa a "Confirmado".
  - [ ] Se crea una Venta en comercial con: cliente del presupuesto, número de pedido = número del presupuesto, valor total = total del presupuesto (con datos USD si es PVC), seña = monto ingresado, estado "Pendiente". El saldo se calcula automáticamente.
  - [ ] Se crea un Pedido de fábrica en plantillas con: número correlativo PF-XXXX, cliente = nombre del cliente del presupuesto, observaciones con referencia al presupuesto de origen, estado "Borrador", sin ítems (fábrica carga el despiece después).
- [ ] El presupuesto queda vinculado a la venta creada (FK `venta` existente) y desde el detalle se puede navegar a la venta y al pedido generados.
- [ ] Si se cancela el popup, no cambia el estado ni se crea ningún registro.
- [ ] No puede generarse doble venta/pedido para el mismo presupuesto.

## Decisiones de negocio (definidas con el usuario, 2026-07-07)

| Punto | Decisión |
|---|---|
| Moneda de la seña | Según material: PVC en USD, aluminio en pesos |
| Obligatoriedad | Seña obligatoria (> 0) para confirmar |
| Monto sugerido | Precargado según `modalidad_sena` (50% o 70% del total), editable |

## Fuera de alcance

- Traducir los ítems del presupuesto a ítems de despiece del pedido de fábrica (las plantillas de despiece no se corresponden con los ítems del cotizador; el despiece lo carga fábrica).
- Revertir una confirmación (des-confirmar y borrar venta/pedido generados).
- Registrar la seña como cobro con recibo (`PagoVenta`); la seña usa el campo `sena` de la Venta, igual que el alta manual actual.

## Estimación

Mediano.

## Riesgos identificados

- La confirmación es irreversible por UI: si se confirma por error, la venta y el pedido quedan creados y deben borrarse manualmente en cada módulo.
- El cliente en el pedido de fábrica es texto libre: si luego se corrige el nombre del cliente, el pedido no se actualiza.
- La creación debe ser transaccional (todo o nada) para no dejar registros huérfanos.

## Derivó en

[FEAT-019](../features/FEAT-019-confirmacion-presupuesto-genera-venta-y-pedido.md)
