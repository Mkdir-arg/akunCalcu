# FEAT-032 — Opcional de tipo "unidad" (cantidad × precio en el cotizador)

- **Estado:** Implementado
- **Fecha:** 2026-07-27
- **Requerimiento:** [REQ-042](../requerimientos/REQ-042-opcional-tipo-unidad.md)

> Nota de numeración: FEAT-031 quedó reservado para "Tirantes divisores" (rama `feat/req-041-tirantes-divisores`). Esta feature toma FEAT-032 para no colisionar al mergear.

## Descripción funcional

Se agrega un cuarto tipo de opcional de fábrica: **"Unidad"**. En `/opcionales/crear/` (y editar) se elige el tipo Unidad y se carga un **precio por unidad**. Al cotizar un ítem de presupuesto, cuando se agrega ese opcional aparece un campo **cantidad** (default 1); el precio del opcional es `cantidad × precio_unidad` y se suma al total del ítem, mostrándose en el desglose. Sirve para cobrar cosas que se cuentan por unidad (herrajes, accesorios sueltos, etc.), sin fórmulas ni despiece.

## Criterios de aceptación (cumplidos)

- [x] Tipo "Unidad" en el ABM de opcionales + campo `precio_unidad`.
- [x] Para el tipo unidad no se muestran secciones de fórmulas/perfiles/accesorios.
- [x] En el cotizador, input de cantidad (default 1, entero ≥ 1) por opcional unidad.
- [x] Precio = `cantidad × precio_unidad`, sumado al total y en el desglose (panel y modal de ítems guardados).
- [x] El opcional unidad aparece para cualquier producto (como el tipo `otro`).
- [x] La cantidad se persiste (snapshot) y se reconstruye al editar el ítem.
- [x] No-regresión de mosquitero / premarco / otro.

## Arquitectura

**Modelo (`plantillas.OpcionalFabrica`):** choice `('unidad', 'Unidad')` en `TIPO_CHOICES` + campo `precio_unidad` (DecimalField, default 0). Migración **`plantillas/0016`** (`AddField(precio_unidad)` + `AlterField(tipo)`), aditiva.

**Form / ABM:** `OpcionalFabricaForm` expone `precio_unidad` como **opcional** (`required=False`) y lo normaliza a 0 en `clean()` para los tipos que no son unidad (evita exigirlo al crear un mosquitero/premarco/otro). El template `opcional_form.html` agrega el wrapper `precio-unidad-wrapper` y `toggleOpcionalFields()` lo muestra solo para tipo unidad; las secciones de fórmulas/perfiles/accesorios se acotaron con `{% elif tipo == 'premarco' or tipo == 'otro' %}` para que unidad no las muestre.

**Motor (`pricing/services/calculator.py::_calcular_opcionales`):** rama nueva `if opcional.tipo == 'unidad'` (antes del `elif mosquitero` / `else`): `precio = cantidad × precio_unidad`, con `cantidad = opc_config.get('cantidad')` (default 1, saneada). Agrega un ítem al desglose `{codigo, nombre, tipo:'unidad', cantidad, precio_unidad, precio_total}`. El precio autoritativo sale del backend (DB), no del payload.

**API catálogo (`pricing/catalog_views.py::OpcionalesListView`):** devuelve `precio_unidad`; el filtro por producto suma `Q(tipo='unidad')` para que unidad aparezca siempre.

**Frontend (`presupuestos/templates/presupuestos/detalle.html`):** al agregar un opcional unidad se inicializa `cantidad: 1`; la lista de opcionales seleccionados muestra un input de cantidad + subtotal en vivo; el POST de cálculo y `guardar()` mandan `{id, cantidad}` por opcional (retrocompatible). El desglose (React + modal JS) muestra "Cantidad × $precio_unidad". La reconstrucción al editar lee cantidad/precio_unidad del snapshot.

**Snapshot (`presupuestos/pdf_descriptions.py::_serialize_options`):** guarda `cantidad` y `precio_unidad` en los opcionales de tipo unidad, para reconstruir el ítem al editar y mostrarlo en el PDF.

## Archivos involucrados

**Nuevos:** `akuna_calc/plantillas/migrations/0016_opcional_tipo_unidad.py`.

**Modificados:** `plantillas/models.py`, `plantillas/forms.py`, `plantillas/templates/plantillas/opcional_form.html`, `pricing/services/calculator.py`, `pricing/catalog_views.py`, `presupuestos/pdf_descriptions.py`, `presupuestos/templates/presupuestos/detalle.html`, `pricing/tests.py`.

## Decisiones técnicas

1. **Campo dedicado `precio_unidad`** (no reusar `precio_m2`) para semántica limpia; requiere migración aditiva.
2. **`precio_unidad` opcional en el form** + normalización a 0 en `clean()`: si fuera requerido rompería el alta de los otros tipos (regresión detectada y corregida en el Reviewer).
3. **Disponible para todos** (como `otro`), sin filtrar por producto/línea.
4. **Cantidad en el payload del opcional** (`{id, cantidad}`), aditivo: los otros tipos ignoran `cantidad`.

## Fuera de alcance

- Filtrado del opcional unidad por producto/línea.
- Unidad en presupuestos PVC (usa precio manual, no pasa por el cotizador de opcionales).

## Tests

- `pricing`: `OpcionalUnidadCalculatorTest` (cantidad × precio, default 1, cantidad inválida→1), `OpcionalUnidadListViewTest` (API incluye unidad + precio_unidad), `OpcionalUnidadFormTest` (form válido, choice presente).
- 5 tests nuevos OK. Suite `pricing`+`presupuestos`+`plantillas`: 217 corridos, 1 fail + 3 errors = baseline preexistente (tablas legacy en SQLite). Sin regresiones.

## Verificación pendiente (deploy)

- Correr la migración `plantillas/0016` en Docker/Railway.
- Verificación visual real del ABM y del cotizador (tablas legacy ausentes en SQLite).
