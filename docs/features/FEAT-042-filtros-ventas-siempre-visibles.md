# FEAT-042 — Panel de filtros siempre visible en Ventas

- **Estado:** Implementado
- **Fecha:** 2026-10-20
- **Requerimiento:** [REQ-053](../requerimientos/REQ-053-filtros-ventas-siempre-visibles.md) (RF-025)
- **Sprint:** Sprint 1 — plan RF Akun
- **Apps:** `comercial`
- **Migración:** ninguna

## Qué hace

El listado de Ventas muestra siempre el panel de filtros, como Presupuestos, Compras y Clientes.
Se quitaron el botón "Filtros" que lo abría y cerraba, la función `toggleFiltros()` y los chips de
"filtros activos" (repetían lo que el panel ya muestra y sus links de quitar perdían `direccion`,
`tipo_fecha` y `razon_social`). Se conservan "Limpiar" y "Limpiar filtros". Los parámetros GET no
cambiaron.

## Criterios cumplidos

- [x] Panel visible sin filtros activos
- [x] Sin botón "Filtros" ni chips
- [x] "Limpiar" y "Limpiar filtros" se conservan
- [x] Mismos parámetros de filtro

## Archivos

- `comercial/templates/comercial/ventas/list.html`
- `comercial/tests.py` → `VentasListFiltrosVisiblesTest`
