# REQ-018 — Recargos por obra nueva o renovación + fix de desglose en presupuestos

> **Estado**: En desarrollo
> **Fecha**: 2026-05-07
> **Complejidad**: Mediano
> **Derivará en**: —

## User Story
Como vendedor quiero definir en un presupuesto si el trabajo corresponde a una obra nueva o a una renovación, aplicando el recargo correspondiente y pudiendo revisar el desglose de cada ítem, para cotizar correctamente sin exponer al cliente detalles internos de cálculo.

## Criterios de Aceptación
- [ ] En la pantalla de detalle del presupuesto el usuario puede indicar si el presupuesto corresponde a `Obra nueva` o `Renovación`.
- [ ] El usuario debe seleccionar obligatoriamente una de las dos opciones (`Obra nueva` o `Renovación`) antes de poder agregar ítems al presupuesto.
- [ ] Si el usuario marca `Obra nueva`, el sistema habilita un campo para ingresar un valor adicional que se suma al total del presupuesto.
- [ ] El valor adicional de `Obra nueva` se visualiza dentro del sistema para el usuario interno.
- [ ] El PDF o impresión del presupuesto no muestra al cliente el detalle interno de ese valor adicional de `Obra nueva`.
- [ ] Si el usuario marca `Renovación`, el sistema aplica un valor fijo adicional por cada ítem agregado al presupuesto.
- [ ] El recargo por `Renovación` impacta correctamente en el cálculo total del presupuesto según la cantidad de ítems cargados.
- [ ] El comportamiento actual de presupuestos sin recargo especial no se rompe.
- [ ] En la sección `Items` del presupuesto, la acción `Ver desglose` abre un popup con el desglose del ítem seleccionado.
- [ ] Si no existe desglose disponible para un ítem, el sistema informa la situación sin dejar la acción sin respuesta.

## Notas
- Pedido originado a partir de la necesidad de diferenciar presupuestos de obra nueva y renovación dentro del módulo de presupuestos.
- El detalle de recargos debe quedar visible para uso interno dentro del sistema, pero no trasladarse al documento entregado al cliente como detalle explícito.
- El alcance incluye también la corrección del botón `Ver desglose` en la grilla de ítems del presupuesto.