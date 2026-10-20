# REQ-053 — Panel de filtros siempre visible en Ventas

- **Estado:** Aprobado
- **Fecha:** 2026-10-20
- **Complejidad:** Pequeño
- **Origen:** RF-025 (documento de requerimientos de Akun, prioridad Alta)
- **Plan:** [Plan RF Akun — octubre 2026](../team/plan-rf-akun-2026-10.md) · Sprint 1
- **Apps afectadas:** `comercial`

## User Story

Como **administrativo o vendedor** quiero **ver siempre el panel de filtros del listado de Ventas**
para **buscar ventas sin tener que abrirlo cada vez**.

## Contexto

Ventas es el único listado con filtros colapsables: `#panel-filtros` lleva `hidden` salvo que haya
algún filtro activo, y se abre con el botón `#btn-filtros` / `toggleFiltros()`. Presupuestos,
Compras y Clientes ya los muestran siempre.

## Criterios de Aceptación

- [ ] Al entrar a `/comercial/ventas/` sin filtros, el panel de filtros se ve completo
- [ ] Desaparece el botón "Filtros" que lo abría y cerraba
- [ ] Desaparecen los chips de "filtros activos" (con el panel visible repiten la información y además están rotos: sus links de quitar pierden `direccion`, `tipo_fecha` y `razon_social`)
- [ ] Se conservan el botón "Limpiar" del panel y "Limpiar filtros" del estado vacío
- [ ] Los filtros siguen funcionando igual (mismos parámetros GET)

## Diseño técnico

Solo template, sin cambios de vista, URL ni modelo.

- `comercial/templates/comercial/ventas/list.html`
  - Quitar el botón `#btn-filtros` (~l.35-42) y la función `toggleFiltros()` (~l.437-440)
  - Quitar el `{% if ... %}hidden{% endif %}` de `#panel-filtros` (~l.74) y el comentario "colapsable"
  - Quitar el bloque de chips de filtros activos (~l.60-71)
  - Opcional: alinear las clases a la "Card de filtros" del design system (`shadow-lg mb-6`)

## Impacto

- Ningún JS ni test depende de `toggleFiltros` / `btn-filtros` (las otras apariciones de `toggle('hidden')` no tienen relación)
- Los tests de `ventas_list` (`comercial/tests.py` ~1234-1380) no se ven afectados
- En celular el panel ocupa más alto: aceptado

## Tests

- GET de `ventas_list` sin filtros → el HTML tiene `id="panel-filtros"` sin la clase `hidden` y no contiene `toggleFiltros`

**Migración:** No.
