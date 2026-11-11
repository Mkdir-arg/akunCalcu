# REQ-073 — Checks «Flete expreso CABA» y «No incluye izaje» en el presupuesto
**Estado**: Implementado — [FEAT-056](../features/FEAT-056-checks-flete-expreso-izaje.md)
**Fecha**: 2026-11-11
**Solicitante**: Comercial
**Complejidad**: Pequeño

## User Story
Como vendedor quiero tildar «Flete expreso CABA» y «No incluye izaje» en la configuración del
presupuesto para que el cliente vea esas condiciones en las Observaciones del PDF.

## Criterios de aceptación
- [x] En el detalle del presupuesto, debajo de «Incluye colocación», aparecen dos checks nuevos:
      «Flete expreso CABA» y «No incluye izaje». Los dos arrancan sin tildar.
- [x] Los dos son independientes de «Incluye flete» e «Incluye colocación».
- [x] Se guardan con el botón «Guardar configuración».
- [x] Con el presupuesto bloqueado (confirmado o cancelado), la vista de solo lectura muestra
      «Flete expreso CABA: Sí/No» e «Izaje: No incluido» cuando corresponde.
- [x] La línea de Observaciones del PDF suma los checks en una sola frase. Ejemplo con todo tildado:
      «El presente presupuesto incluye flete y colocación, flete expreso CABA. No incluye izaje.»
- [x] Sin los checks nuevos tildados, el PDF queda igual que hoy.
- [x] Los presupuestos existentes quedan con los dos checks sin tildar.

## Ejemplos del texto en el PDF
| Flete | Colocación | Expreso CABA | No izaje | Observaciones |
|---|---|---|---|---|
| Sí | Sí | Sí | Sí | El presente presupuesto incluye flete y colocación, flete expreso CABA. No incluye izaje. |
| Sí | No | Sí | No | El presente presupuesto incluye flete, flete expreso CABA. |
| No | No | No | Sí | El presente presupuesto no incluye flete ni colocación. No incluye izaje. |
| No | No | Sí | No | El presente presupuesto no incluye flete ni colocación, flete expreso CABA. |

## Notas
- La última fila se lee contradictoria, pero el usuario pidió que «Flete expreso CABA» sea
  independiente de «Incluye flete».
