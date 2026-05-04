# FEAT-008 — Rediseño del PDF de presupuestos con descripción narrativa por ítem

> **Requerimiento**: [REQ-016](../requerimientos/REQ-016-rediseno-pdf-presupuestos-descripcion-narrativa.md)
> **Fecha**: 2026-05-04
> **Apps afectadas**: `presupuestos`

## Descripción funcional

Se rediseñó la vista `/presupuestos/<id>/pdf/` para que el presupuesto se vea más comercial y cada ítem se presente con una redacción legible para cliente final.

- Al agregar un ítem, el sistema guarda en `resultado_json.snapshot_item` un snapshot con etiquetas legibles de línea, extrusora, producto, marco, hoja, vidrio, tratamiento, medidas, cantidad y opcionales.
- El PDF usa ese snapshot para mostrar un título, una descripción narrativa y un resumen técnico breve por ítem.
- Los presupuestos existentes que no tienen `snapshot_item` siguen mostrando una salida razonable a partir de la descripción manual y el desglose legacy guardado en `resultado_json`.
- El layout del PDF pasó de una tabla simple a una composición de bloques con cabecera comercial, datos del cliente, tarjetas por ítem y cierre visual del total.

## Criterios de aceptación cumplidos

- [x] En el PDF de presupuesto cada ítem muestra una descripción narrativa construida con los datos seleccionados al agregarlo.
- [x] La redacción incluye, cuando existe, la descripción manual del ítem y la configuración técnica relevante.
- [x] La descripción se arma como una oración legible para cliente final.
- [x] Si faltan datos opcionales, el texto se adapta sin huecos ni separadores rotos.
- [x] Los opcionales se integran en la descripción del ítem o en el resumen técnico del mismo bloque.
- [x] El diseño visual del PDF se actualizó a una versión más comercial y ordenada.
- [x] Los presupuestos existentes conservan una salida legible mediante fallback legacy.

## Archivos modificados

- `presupuestos/views.py` — guarda el snapshot descriptivo al crear ítems y prepara `items_pdf` para la vista del PDF.
- `presupuestos/templates/presupuestos/pdf.html` — nuevo layout comercial del PDF con narrativa por ítem.
- `presupuestos/tests.py` — tests del helper narrativo y test de contenido de la vista PDF.

## Archivos creados

- `presupuestos/pdf_descriptions.py` — helper para construir snapshot, narrativa, resumen técnico y fallback legacy.

## Decisiones técnicas

- No se agregó migración ni columnas nuevas: la metadata descriptiva se congela dentro de `ItemPresupuesto.resultado_json`.
- El PDF sigue el patrón existente de HTML imprimible definido en ADR-006; no se incorporan librerías nuevas de generación PDF.
- La vista del PDF recibe un contexto preparado (`items_pdf`) para que la plantilla no tenga lógica de reconstrucción técnica.

## Validación

- `python manage.py test presupuestos.tests.PdfDescriptionsHelpersTest`
- `python -m py_compile presupuestos/pdf_descriptions.py presupuestos/views.py presupuestos/tests.py`
- Se agregó un test de vista para el PDF, pero la suite con base no pudo ejecutarse en este entorno por dependencia de MySQL remota y Docker Desktop no disponible.