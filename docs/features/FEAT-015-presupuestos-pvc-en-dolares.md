# FEAT-015 — Presupuestos PVC siempre en dólares

**Estado:** Implementado
**Fecha:** 2026-06-19
**Requerimiento:** [REQ-032](../requerimientos/REQ-032-presupuestos-pvc-en-dolares.md)

## Descripción funcional

Los presupuestos en PVC se cotizan y se muestran siempre en dólares. Se reemplazó el checkbox "valor en dólares" que existía por ítem por una única **cotización USD a nivel de cabecera del presupuesto** (`Presupuesto.cotizacion_usd`), obligatoria cuando `tipo_material = pvc`.

El sistema sigue calculando y guardando todo en pesos como base común (igual que antes — recargos de obra nueva/renovación, IVA y KPIs no cambian su lógica interna). Lo nuevo es la capa de visualización: cuando el presupuesto es PVC, el detalle, el PDF y el listado muestran los montos convertidos a USD usando la cotización de cabecera.

Los presupuestos en Aluminio no cambian: siguen mostrándose y calculándose en pesos.

## Criterios de aceptación cumplidos

- [x] `tipo_material = PVC` implica presupuesto en dólares por definición, sin toggle por ítem.
- [x] Cotización USD única por presupuesto (cabecera), obligatoria para PVC vía validación de formulario.
- [x] Los ítems PVC se ingresan en USD; el sistema sigue calculando y guardando el total en pesos.
- [x] El PDF de un presupuesto PVC muestra precio unitario, totales, IVA y total final en USD, más la cotización utilizada.
- [x] El detalle del presupuesto muestra los montos en USD cuando es PVC (incluyendo recargos de obra nueva/renovación).
- [x] El listado de presupuestos muestra badge "Presupuesto USD" para presupuestos PVC, con el mismo patrón visual que `comercial/ventas/list.html`.
- [x] Los presupuestos de Aluminio no cambian.
- [x] Tests automatizados cubren modelo, formulario y vistas (46 tests en `presupuestos`, todos en verde).

## Archivos modificados

- `akuna_calc/presupuestos/models.py` — campo `cotizacion_usd`; métodos `es_pvc()`, `tiene_cotizacion_usd()`, y getters `_usd` para subtotal/IVA/total/recargos/ítems.
- `akuna_calc/presupuestos/forms.py` — `PresupuestoForm` exige `cotizacion_usd` cuando `tipo_material == 'pvc'`.
- `akuna_calc/presupuestos/views.py` — `agregar_item()`: rama PVC recibe `valor_usd`, exige cotización configurada, convierte a pesos con la cotización del presupuesto.
- `akuna_calc/presupuestos/templates/presupuestos/form.html` — campo cotización USD, visible solo para PVC.
- `akuna_calc/presupuestos/templates/presupuestos/detalle.html` — formulario PVC simplificado (sin checkbox); totales y recargos en USD cuando corresponde.
- `akuna_calc/presupuestos/templates/presupuestos/pdf.html` — ítems y totales en USD + línea de cotización utilizada.
- `akuna_calc/presupuestos/templates/presupuestos/lista.html` — badge "Presupuesto USD" y columna Total en USD para PVC.
- `akuna_calc/presupuestos/tests.py` — tests de modelo, formulario y vistas para el flujo USD.
- `akuna_calc/presupuestos/migrations/0007_presupuesto_cotizacion_usd_presupuesto_tipo_material.py`.

## Decisiones técnicas

- Cotización a nivel de cabecera (no por ítem) para evitar inconsistencias entre ítems de un mismo presupuesto y simplificar la UI — ver [ADR-010](../team/decisions.md#adr-010-cotización-usd-de-presupuestos-pvc-a-nivel-de-cabecera).
- El cálculo interno sigue en pesos como base común; el USD es siempre derivado (`monto_ars / cotizacion_usd`) para visualización, nunca se persiste un monto en USD por ítem. Si se cambia la cotización del presupuesto después de cargar ítems, el USD mostrado de todos los ítems se recalcula automáticamente.
- Se bloquea el alta de ítems PVC si el presupuesto no tiene cotización configurada, para evitar ítems a $0.

## Incidencia de despliegue (no atribuible a esta feature)

Al generar la migración de este cambio se detectó que el campo `tipo_material` (agregado al modelo en un commit previo) nunca tuvo migración asociada. La migración 0007 de esta feature corrigió ambos huecos a la vez. En producción (Railway) ambas columnas ya existían físicamente sin estar registradas en `django_migrations`, por lo que se aplicó `migrate presupuestos 0007 --fake`. Se encontró un problema análogo en la app `productos` (migración `0007_remove_cotizacionitem_cotizacion_and_more` con tablas ya inexistentes) y se resolvió de la misma forma (`migrate productos 0007 --fake`), no relacionado con esta feature.

## Validación

- `docker compose exec web python manage.py test presupuestos` → 46 tests, OK.
- Verificado en producción (Railway): `python manage.py migrate` sin migraciones pendientes en ninguna app tras los fakes.
