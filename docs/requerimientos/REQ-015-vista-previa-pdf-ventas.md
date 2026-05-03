# REQ-015 — Vista previa de PDF desde ventas

**Estado:** En desarrollo
**Fecha:** 2026-05-03

## User Story
Como vendedor quiero abrir una vista previa del PDF de una venta desde `/comercial/ventas/` para revisar el comprobante antes de descargarlo o compartirlo.

## Criterios de Aceptación
- [ ] En `/comercial/ventas/` la acción `PDF` de cada venta permite abrir una vista previa del documento asociado.
- [ ] La vista previa muestra el PDF correspondiente a la venta seleccionada.
- [ ] El usuario puede seguir descargando o imprimiendo el PDF desde el visor del navegador.
- [ ] Se mantienen los permisos y validaciones actuales para acceder al PDF de una venta.
- [ ] Si el PDF no puede generarse o visualizarse, el sistema informa el problema sin romper el listado de ventas.

## Notas
- Complejidad: Pequeño
- Alcance inicial: listado de ventas en `/comercial/ventas/` y endpoint de generación/entrega del PDF asociado.
- Derivará en una feature cuando se implemente.