# REQ-074 — «Agregar adicional»: conceptos libres con etiqueta y precio en el ítem
**Estado**: Implementado — [FEAT-057](../features/FEAT-057-adicionales-libres-item.md)
**Fecha**: 2026-11-11
**Solicitante**: Comercial
**Complejidad**: Mediano

## User Story
Como vendedor quiero agregarle a un ítem del presupuesto conceptos libres con etiqueta y precio
(por ejemplo «Albañilería $5») para cobrar trabajos que no están en el catálogo de opcionales, sin
que les afecten el margen ni el IVA.

## Funcionamiento
1. En «Agregar ítem», al lado de «Agregar Opcional», hay un botón **«Agregar adicional»**.
2. Cada vez que se toca, aparece una fila con **Etiqueta** y **Precio**. Un ítem puede tener
   varios adicionales y cada uno se puede quitar.
3. Al escribir la etiqueta se sugieren las etiquetas ya usadas en **cualquier presupuesto**
   (por ejemplo «Albañilería»), para no volver a tipearlas.
4. Si el ítem tiene cantidad mayor a 1, al guardar se pregunta por cada adicional:
   **«¿Va por cada unidad o es un total?»**
   - Por cada unidad: $5 en un ítem de 3 unidades suma $15.
   - Total: suma $5 una sola vez.
5. El adicional se suma al precio del ítem **sin margen y sin IVA**: el IVA del presupuesto se
   calcula sobre el subtotal sin los adicionales.
6. En PVC el precio del adicional se carga en dólares, igual que el resto del ítem, y se convierte
   con la cotización del presupuesto.

## Criterios de aceptación
- [x] El botón «Agregar adicional» está en el alta y la edición de ítems de aluminio y de PVC.
- [x] Se pueden cargar varios adicionales por ítem, cada uno con etiqueta y precio mayor a 0.
- [x] La etiqueta sugiere las ya usadas en otros presupuestos.
- [x] Con cantidad mayor a 1 se elige «por cada unidad» o «total», y el importe se calcula según eso.
- [x] El margen no se aplica al adicional.
- [x] El IVA del presupuesto no incluye los adicionales.
- [x] El detalle del ítem muestra cada adicional: etiqueta, precio, modo y subtotal
      (ej.: «Albañilería $5 × 3 = $15»).
- [x] En el PDF del cliente, el precio del ítem incluye los adicionales y debajo se lee
      «Incluye: Albañilería».
- [x] Al editar el ítem, los adicionales cargados aparecen y se pueden cambiar o quitar.
- [x] Los ítems existentes no cambian de precio.

## Fuera de alcance
- Estructuras (REQ-062) y productos terciarizados: no llevan el botón en esta etapa.
- Un ABM de etiquetas: las sugerencias salen de lo ya cargado.
