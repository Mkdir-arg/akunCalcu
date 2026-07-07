# FEAT-023 — "Agregar orden" abre el cotizador y crea la orden precargada

**Estado:** Implementado
**Fecha:** 2026-07-07
**Relacionado:** [FEAT-021](./FEAT-021-ordenes-de-fabricacion-etapa1.md). Pedido directo del usuario: "cuando tocás el botón Agregar orden se tiene que ver el pop up del cotizador ('Agregar item al presupuesto')".

## Descripción funcional

En el detalle del pedido, el botón **"Agregar orden"** ahora abre un **popup de cotizador** (igual que el de presupuestos: selectores en cascada Extrusora → Línea → Producto → Marco → Modelo de hoja → Vidrio + Color, medidas, margen, cantidad, y **cálculo de precio de referencia con vista previa**).

Al presionar **"Crear orden de fabricación"** se crea la orden con la abertura precargada desde la selección:

| Campo de la orden | Origen |
|---|---|
| Tipo de abertura | Producto (descripción) |
| Línea | Línea (nombre) |
| Color | Tratamiento / Terminación (descripción) |
| Tipo de vidrio | Vidrio (descripción) |
| Modelo de hoja | Hoja (descripción) |
| Cantidad de hojas | Hoja (campo `cantidad`) |

El **precio calculado es solo de referencia y NO se guarda en la orden** (la orden de fabricación no lleva monto). Tras crear, redirige a la edición de la orden para completar el resto de los campos (SI/NO, medidas, nota). Si se crea sin seleccionar nada, la orden nace en blanco para cargar a mano.

## Historia de la interpretación

La primera versión puso un botón "Cargar desde cotizador" en la pantalla de edición con un modal liviano de solo-selectores. El usuario corrigió: el cotizador debe dispararse desde **"Agregar orden"** y ser el **cotizador completo con precio**. Se movió allí y se removió el modal de la edición.

## Decisiones técnicas

- **No se reutilizó el componente React del cotizador de presupuestos** (está acoplado a PVC, terciarizado, opcionales, edición de ítems y a `{{ presupuesto.pk }}`; tocarlo arriesgaba el flujo crítico de presupuestos). Se hizo un **componente React propio y autocontenido** en `pedido_detail.html`, que reusa las mismas APIs de catálogo (`/pricing/api/pricing/...`) y de cálculo (`/pricing/api/pricing/calculate/`). Presupuestos queda intacto.
- La creación de la orden se hace por un **form oculto** que postea a `orden_create` los textos resueltos de la abertura; `orden_create` (ahora `@require_POST`) crea la orden con esos campos y redirige a la edición. Retrocompatible: sin campos, orden en blanco.
- Los `<select>` del cotizador llevan `no-select2` (nativos, manejados por React) para no chocar con el Select2 global.

## Archivos modificados

- `akuna_calc/plantillas/views.py` — `orden_create` acepta los campos de la abertura por POST (`@require_POST`).
- `akuna_calc/plantillas/templates/plantillas/pedido_detail.html` — botón "Agregar orden" abre el modal; modal + form oculto + componente React del cotizador (CDNs React/ReactDOM/Babel).
- `akuna_calc/plantillas/templates/plantillas/orden_form.html` — se revirtió el modal liviano de la versión anterior (la edición vuelve a ser solo el formulario).
- `akuna_calc/plantillas/tests.py`.

Sin cambios de modelo ni migraciones.

## Validación

- `python manage.py test plantillas --settings=akuna_calc.settings_test_sqlite` → **23 OK**.
- El cálculo y el catálogo usan tablas legacy de `pricing` (no disponibles en SQLite de test); el flujo real de cascada + cálculo se verifica en el entorno con MySQL. Los tests cubren: presencia del cotizador y el form en el detalle, y que `orden_create` precargue la abertura desde los datos posteados.
