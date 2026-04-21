# REQ-011 — Navegación con retorno contextual + reporte de ventas por importe facturado

> **Estado:** En desarrollo
> **Fecha:** 2026-04-21
> **Complejidad:** Grande

## User Story

Como usuario de AkunCalcu, quiero volver a la pantalla anterior sin perder filtros ni contexto y reportar ventas según el importe efectivamente facturado,
para navegar más rápido entre módulos y obtener reportes de ingresos mensuales que reflejen el valor real de la factura emitida.

## Criterios de Aceptación

### Parte A — Volver conservando contexto
- [ ] Desde cualquier módulo, al ingresar a una pantalla de detalle, edición o alta desde un listado o reporte, el botón "Volver" regresa a la pantalla anterior
- [ ] Al volver, se conservan los filtros, búsquedas, orden y paginación que el usuario tenía aplicados
- [ ] La solución funciona de forma consistente en los módulos donde hoy existe navegación hacia atrás mediante botón "Volver"
- [ ] Si el usuario entra directamente a una URL sin venir desde un listado, el botón "Volver" sigue teniendo un destino válido y no rompe la navegación

### Parte B — Reporte de ventas por importe facturado
- [ ] En el reporte de ventas/ingresos se puede distinguir el monto total de la venta del importe efectivamente facturado
- [ ] Si una venta total es de $100 pero la factura emitida corresponde solo a una seña de $50, el reporte mensual computa $50 como ingreso facturado para ese período
- [ ] La lógica de reporte no altera los saldos ni el total operativo de la venta
- [ ] El criterio usado para determinar el importe facturado queda explícito y consistente en el reporte

## Alcance técnico

El requerimiento impacta pantallas de navegación transversal en distintos módulos y el cálculo del módulo comercial para reportes de ventas/ingresos. La solución debe preservar compatibilidad con accesos directos por URL y no modificar el cálculo financiero base de las ventas, solo la capa de navegación y reporting.