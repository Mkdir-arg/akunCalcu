# REQ-017 — Compras y pagos de compra en dólares

> **Estado**: En desarrollo
> **Fecha**: 2026-05-04
> **Complejidad**: Mediano
> **Derivará en**: —

## User Story
Como usuario administrativo quiero registrar compras y pagos de compra en dólares, indicando monto en USD y cotización, para reflejar correctamente operaciones con proveedores en moneda extranjera y mantener coherencia con el flujo que ya existe en ventas.

## Criterios de Aceptación
- [ ] En el flujo de compras el usuario puede indicar que la operación o el pago asociado está expresado en dólares.
- [ ] Cuando la operación está en dólares, el sistema solicita monto en USD y la cotización aplicada.
- [ ] El sistema conserva tanto el importe original en dólares como su equivalente en pesos para cálculos y consultas.
- [ ] La experiencia de uso toma como referencia la lógica ya existente en ventas para `Pagó en dólares`, evitando dos comportamientos distintos para una misma necesidad.
- [ ] En las pantallas relevantes de compras se visualiza claramente cuándo una compra o un pago fue registrado en dólares y con qué cotización.
- [ ] Los totales, saldos y validaciones del flujo de compras siguen siendo correctos cuando intervienen importes en dólares.
- [ ] Si la operación se registra en pesos, el flujo actual no cambia.

## Notas
- Pedido originado a partir de la necesidad de sumar soporte de dólares en compras tomando como referencia la funcionalidad ya presente en ventas.
- Alcance funcional inicial: alta de compra y puntos del flujo de compras donde corresponda cargar o mostrar moneda y cotización.
- Asunción inicial para el análisis técnico: reutilizar el patrón de captura y cálculo ya usado en ventas siempre que sea compatible con el dominio de compras.