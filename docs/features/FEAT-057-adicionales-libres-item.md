# FEAT-057 — «Agregar adicional»: conceptos libres con etiqueta y precio en el ítem

**Estado:** Implementado (en `development`, sin commitear)
**Fecha:** 2026-11-11
**Requerimiento:** [REQ-074](../requerimientos/REQ-074-adicionales-libres-item.md)

## Qué hace

En el cotizador de aluminio, al lado de «Agregar Opcional», y en el de PVC, en la sección
«Adicionales», hay un botón **«Agregar adicional»**. Cada adicional es una fila con:
- **Etiqueta**, con sugerencias de las ya usadas en cualquier presupuesto (por ejemplo «Albañilería»).
- **Precio**: en pesos para aluminio y en US$ para PVC.

Si el ítem tiene más de una unidad, cada adicional se marca **«Por cada unidad»** o **«Total»**.
Si no se marca, al guardar lo pregunta un SweetAlert.

| Ítem | Adicional | Resultado |
|---|---|---|
| 3 × $100 | Albañilería $5, por cada unidad | Precio unitario $105, total $315 |
| 3 × $100 | Albañilería $5, total | Precio unitario $100, total $305 |

El adicional **no lleva margen y queda fuera del IVA**: el IVA se calcula sobre el subtotal sin
los adicionales.

Dónde se ve:
- **Fila del ítem:** «Adicionales (sin margen ni IVA): Albañilería $5 × 3 = $15».
- **Ver detalle:** una sección «Adicionales» con cada concepto y su subtotal.
- **PDF del cliente:** el precio ya los incluye, y debajo del ítem se lee «Incluye: Albañilería».

## Criterios de aceptación

| Criterio | Estado |
|---|---|
| Botón en el alta y la edición de aluminio y PVC | ✅ |
| Varios adicionales por ítem, con etiqueta y precio mayor a 0 | ✅ |
| Sugerencias de etiquetas de cualquier presupuesto | ✅ |
| «Por cada unidad» o «Total» con cantidad mayor a 1 | ✅ |
| Sin margen | ✅ |
| Fuera del IVA | ✅ |
| Detalle del ítem con cada adicional | ✅ |
| «Incluye: …» en el PDF | ✅ |
| Al editar, los adicionales se cargan y se pueden cambiar | ✅ |
| Los ítems existentes no cambian | ✅ |

## Archivos modificados

- `akuna_calc/presupuestos/models.py`:
  - En el ítem: `get_adicionales*`, el adicional unitario y el fijo, y el cálculo de `precio_total` en `save()`.
  - `aplicar_recargo_renovacion` conserva los adicionales.
  - En el presupuesto: `get_total_adicionales()`; el IVA se calcula sin ellos.
- `akuna_calc/presupuestos/views.py`:
  - `_parsear_adicionales` valida, y en PVC convierte de US$ a pesos.
  - `_aplicar_adicionales` y la API `adicionales_etiquetas`.
- `akuna_calc/presupuestos/urls.py`: la ruta `presupuestos-adicionales-etiquetas`.
- `akuna_calc/usuarios/access_control.py`: la ruta nueva, con `presupuestos.view`.
- `akuna_calc/presupuestos/templates/presupuestos/detalle.html`:
  - El componente compartido `window.Adicionales` y su integración en los dos cotizadores.
  - La fila del ítem y el modal de detalle.
- `akuna_calc/presupuestos/templates/presupuestos/pdf.html`: el «Incluye: …».
- `akuna_calc/presupuestos/tests_adicionales.py`: 16 tests nuevos.

## Decisiones técnicas

- **Sin migración:** los adicionales viven en `ItemPresupuesto.resultado_json['adicionales']`, igual
  que las estructuras (ADR-022). Cada uno guarda `{etiqueta, precio (pesos), precio_usd, modo, cantidad}`.
- **Dónde suman:** los «por unidad» entran en `precio_unitario`. Los «total» se suman una sola vez en
  `precio_total` (`precio_unitario × cantidad + fijos`).
- **Sugerencias:** salen de los ítems con `resultado_json__has_key='adicionales'`. No hay ABM de etiquetas.
- **Límite conocido:** con modo «Total» y varias unidades, en el PDF el precio unitario multiplicado
  por la cantidad no da el total. Lo explica el «Incluye» debajo del ítem.
- **Fuera de alcance:** las estructuras, los productos terciarizados y el modo módulo no llevan adicionales.

## Pendiente

- Probar en el navegador los dos cotizadores, la pregunta de modo y las sugerencias.
