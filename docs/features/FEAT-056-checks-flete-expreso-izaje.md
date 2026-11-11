# FEAT-056 — Checks «Flete expreso CABA» y «No incluye izaje» en el presupuesto

**Estado:** Implementado (en `development`, sin commitear)
**Fecha:** 2026-11-11
**Requerimiento:** [REQ-073](../requerimientos/REQ-073-checks-flete-expreso-izaje.md)

## Qué hace

En la configuración del presupuesto, debajo de «Incluye colocación», hay dos checks nuevos:
«Flete expreso CABA» y «No incluye izaje». Son independientes de flete y colocación y se guardan
con «Guardar configuración».

En el PDF se suman a la línea de Observaciones, en una sola frase:

| Flete | Colocación | Expreso CABA | No izaje | Observaciones |
|---|---|---|---|---|
| Sí | Sí | Sí | Sí | El presente presupuesto incluye flete y colocación, flete expreso CABA. No incluye izaje. |
| Sí | No | Sí | No | El presente presupuesto incluye flete, flete expreso CABA. |
| No | No | No | Sí | El presente presupuesto no incluye flete ni colocación. No incluye izaje. |
| No | No | Sí | No | El presente presupuesto no incluye flete ni colocación, flete expreso CABA. |

Con el presupuesto confirmado o cancelado, el resumen de solo lectura muestra «Flete expreso CABA:
Sí/No» y, si está tildado, «Izaje: No incluido».

## Criterios de aceptación

| Criterio | Estado |
|---|---|
| Dos checks debajo de «Incluye colocación», sin tildar por defecto | ✅ |
| Independientes de flete y colocación | ✅ |
| Se guardan con «Guardar configuración» | ✅ |
| Se ven en la vista de solo lectura | ✅ |
| Observaciones del PDF en una sola frase | ✅ |
| Sin los checks nuevos, el PDF queda igual | ✅ |
| Presupuestos existentes quedan sin tildar | ✅ |

## Archivos modificados

- `akuna_calc/presupuestos/models.py` — campos `flete_expreso_caba` y `no_incluye_izaje`;
  `get_observaciones_pdf()` los suma a la frase.
- `akuna_calc/presupuestos/migrations/0013_presupuesto_flete_expreso_izaje.py` — migración nueva.
- `akuna_calc/presupuestos/forms.py` — los dos campos en `PresupuestoConfiguracionObraForm`.
- `akuna_calc/presupuestos/templates/presupuestos/detalle.html` — checks y renglones de solo lectura.
- `akuna_calc/presupuestos/tests.py` — 7 tests nuevos.

## Decisiones técnicas

- No se tocó el resumen del listado de presupuestos (`get_resumen_flete_colocacion`): no se pidió.
- Sin ADR: no hay decisión de arquitectura.

## Pendiente

- Probar en el navegador y generar un PDF real.
