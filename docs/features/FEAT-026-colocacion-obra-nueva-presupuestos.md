# FEAT-026 — Colocación en presupuestos de obra nueva

**Estado:** Implementado
**Fecha:** 2026-07-21
**Módulo:** `presupuestos`
**Pedido por:** Romina

## Descripción funcional

En los presupuestos de **obra nueva**, el valor que hoy se cargaba como "Recargo obra nueva" es en realidad la **Colocación** (el monto de instalación que cargan las chicas). Este cambio lo refleja en toda la salida del presupuesto y agrega una validación al confirmar.

1. **Renglón "Colocación" en el presupuesto.** En el PDF y en el detalle web, debajo del **Subtotal** aparece un renglón **"Colocación"** con el monto (solo en obra nueva). El **IVA** se calcula sobre **Subtotal + Colocación** y ese es el total final.
2. **Renombre de etiqueta.** Donde decía "Recargo obra nueva" ahora dice **"Colocación"** (desglose de totales, tarjetas de configuración y el input del formulario de configuración de obra).
3. **Validación al confirmar.** Cuando el checkbox **"Incluye colocación"** está tildado:
   - Si el monto de colocación aplicable es **$0**, **no deja confirmar** (bloqueo con mensaje claro, server-side y client-side).
   - Si el monto es **menor a $100.000**, muestra una **alerta** ("¿confirmar igual?") antes de confirmar (se puede seguir).
4. **Renovación queda igual** (no se tocó).

## Criterios de aceptación cumplidos

- [x] El PDF muestra "Colocación" bajo el Subtotal en obra nueva; el IVA es 21% de (Subtotal + Colocación).
- [x] El detalle web y el label del formulario dicen "Colocación".
- [x] Con "Incluye colocación" tildado y monto 0 → confirmación bloqueada.
- [x] Con monto < $100.000 → alerta antes de confirmar.
- [x] Renovación sin cambios.
- [x] Tests (118 OK en presupuestos).

## Archivos modificados

- `akuna_calc/presupuestos/models.py` — método `get_monto_colocacion()` (devuelve el monto según `tipo_obra`).
- `akuna_calc/presupuestos/views.py` — `pdf` (renglón colocación + `pdf_iva = get_iva_desglosado()`); `_procesar_confirmacion` (bloqueo si `incluye_colocacion` y monto ≤ 0).
- `akuna_calc/presupuestos/forms.py` — label de `recargo_obra_nueva` → "Colocación".
- `akuna_calc/presupuestos/templates/presupuestos/pdf.html` — renglón "Colocación" (ARS y USD/PVC).
- `akuna_calc/presupuestos/templates/presupuestos/detalle.html` — labels + data-attributes + JS de bloqueo/alerta al confirmar.
- `akuna_calc/presupuestos/tests.py` — tests de colocación.

## Decisiones técnicas

- **Sin migración**: se reutiliza el campo existente `recargo_obra_nueva` (obra nueva) / `recargo_renovacion_unitario` (renovación); solo cambian etiquetas, desglose y validación.
- El **monto de colocación aplicable** depende del `tipo_obra` (`get_monto_colocacion`).
- El **IVA del PDF** pasó a `get_iva_desglosado()` (21% de subtotal+colocación, mostrado como referencia esté o no incluido en el total) — esto además corrigió un desglose que no cerraba (ver FIX-017).
- El bloqueo por monto 0 vive en el servidor (`_procesar_confirmacion`, no se puede saltar) y se refuerza en el cliente; la alerta por monto bajo (< $100.000) es solo client-side (SweetAlert2).
