# FEAT-007 — Mejora de Presupuestos: Paridad con Cotizador + UI

> **Requerimiento**: [REQ-008](../requerimientos/REQ-008-mejora-presupuestos-cotizador.md)
> **Fecha**: 2026-03-30
> **Apps afectadas**: `presupuestos`

## Descripción funcional

Se mejoró el módulo de presupuestos para que el cotizador embebido tenga paridad completa con el cotizador principal de pricing:

- **Opcionales**: se pueden agregar mosquiteros y otros opcionales al cotizar un ítem. Se envían al backend y se guardan en `resultado_json`.
- **Desglose completo**: el resultado muestra perfiles, accesorios, vidrio, tratamiento, mano de obra y opcionales en secciones expandibles.
- **Modal de desglose**: cada ítem guardado tiene un botón "Ver desglose" que abre un modal con el detalle completo del cálculo.
- **KPIs en lista**: la vista de lista muestra tarjetas de resumen (total, borradores, enviados, confirmados con monto).
- **Código unificado**: se eliminó `item_form.html` y se unificó todo el cotizador dentro del modal en `detalle.html`.
- **Filtro corregido**: se corrigió el filtro de búsqueda por cliente usando `Q()` objects en vez de encadenar querysets con `|`.

## Criterios de aceptación cumplidos

- [x] Se pueden agregar opcionales al cotizar un ítem del presupuesto
- [x] Los opcionales se envían al backend y se guardan en resultado_json
- [x] El resultado muestra mano de obra cuando aplica
- [x] El resultado muestra desglose expandible completo
- [x] El botón "Ver desglose" de cada ítem guardado funciona con modal
- [x] Lista de presupuestos mejorada con KPIs de resumen
- [x] Cotizador en modal con paridad visual respecto al cotizador principal
- [x] Código del cotizador unificado (sin duplicación)

## Archivos modificados

- `presupuestos/views.py` — KPIs con aggregate, filtro Q(), soporte opcionales_json
- `presupuestos/templates/presupuestos/lista.html` — tarjetas KPI, UI mejorada
- `presupuestos/templates/presupuestos/detalle.html` — cotizador React con opcionales + desglose completo + modal desglose items guardados

## Archivos eliminados

- `presupuestos/templates/presupuestos/item_form.html` — unificado en detalle.html

## Decisiones técnicas

- Se unificó el cotizador en `detalle.html` para evitar duplicación de código entre `item_form.html` y `detalle.html`. Ahora `agregar_item` siempre redirige a detalle.
- No se requirieron cambios de modelo ni migraciones.
