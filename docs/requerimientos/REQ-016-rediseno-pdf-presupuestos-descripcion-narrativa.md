# REQ-016 — Rediseño del PDF de presupuestos con descripción narrativa por ítem

> **Estado**: Implementado — [FEAT-008](../features/FEAT-008-rediseno-pdf-presupuestos-descripcion-narrativa.md)
> **Fecha**: 2026-05-04
> **Complejidad**: Mediano
> **Derivará en**: FEAT-008

## User Story
Como vendedor quiero que el PDF del presupuesto describa cada ítem con una redacción comercial y técnica armada a partir de la configuración seleccionada, para enviarle al cliente un documento más claro, profesional y fácil de entender.

## Criterios de Aceptación
- [ ] En el PDF de presupuesto cada ítem muestra una descripción narrativa construida con los datos seleccionados al agregarlo.
- [ ] La redacción incluye, cuando exista, la descripción manual del ítem y la configuración técnica relevante: extrusora, línea, producto, marco, hoja, vidrio, tratamiento, medidas, cantidad y opcionales.
- [ ] La descripción se arma como una oración legible para cliente final y no como una lista técnica suelta.
- [ ] Si algún dato opcional no fue seleccionado, el texto se adapta sin dejar huecos, separadores vacíos o frases rotas.
- [ ] Los opcionales se integran en la descripción del ítem o en un subtítulo claro dentro del mismo bloque del PDF.
- [ ] El diseño visual del PDF se actualiza para que se vea más comercial y ordenado que la versión actual.
- [ ] Los presupuestos existentes que no tengan toda la metadata disponible conservan una salida legible usando la descripción manual y los datos mínimos disponibles.

## Notas
- Alcance inicial: PDF de `/presupuestos/<id>/pdf/`.
- Ejemplo de redacción esperada: `Ventana cocina en línea Módena de Aluar, modelo banderola, con marco Banderola, hoja Banderola DVH, vidrio 4+9+4, terminación blanca y medidas 1200 x 1500 mm, con opcionales asdas y asdasd.`
- Hallazgo funcional: el PDF actual solo muestra la descripción manual, medidas, cantidad y precio; para construir la oración completa había que conservar o reconstruir metadata técnica del ítem al momento de guardarlo.
- Implementado mediante snapshot descriptivo en `resultado_json.snapshot_item`, sin cambios de modelo.
