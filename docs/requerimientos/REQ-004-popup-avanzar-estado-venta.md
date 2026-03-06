# REQ-004 — Popup para avanzar estado al completar pago

**Estado:** Implementado
**Complejidad:** Pequeño
**Fecha:** 2026-03-06
**Feature relacionada:** [FEAT-004](../features/FEAT-004-popup-avanzar-estado-venta.md)

## User Story

Como vendedor, quiero que al registrar el último pago de una venta (saldo pendiente = $0) me aparezca un popup preguntando si deseo avanzar al siguiente estado, para agilizar el seguimiento de la venta sin pasos manuales extra.

## Criterios de Aceptación

- [x] Al registrar un pago que deja el saldo en $0, se muestra automáticamente un popup (SweetAlert2)
- [x] El popup dice: "¿Deseas cambiar el estado a 'Colocado'?"
- [x] Si el usuario confirma → el estado cambia de `pendiente` a `colocado` automáticamente
- [x] Si el usuario cancela → no se hace ningún cambio de estado
- [x] El cambio de estado queda registrado en la venta (visible en el detalle)
- [x] El comportamiento aplica en la vista `/comercial/ventas/<id>/`
