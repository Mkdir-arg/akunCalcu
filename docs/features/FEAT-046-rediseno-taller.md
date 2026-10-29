# FEAT-046 — Rediseño visual «Taller» de todo el sistema

- **Estado:** Implementado (rama `development`, sin desplegar a `main`)
- **Fecha:** 2026-10-29
- **Requerimiento:** [REQ-064](../requerimientos/REQ-064-rediseno-taller.md)
- **Decisión:** [ADR-023](../team/decisions.md)
- **Apps:** todas las que tienen pantallas
- **Migración:** ninguna en este rediseño (las del tiempo real están en [FEAT-047](./FEAT-047-tiempo-real.md))
- **Mockups:** [`docs/team/design/*.dc.html`](../team/design/) (67 pantallas; el sistema visual está en `Main.dc.html`)

## Qué hace

Lleva todas las pantallas al estilo «Taller»: fondo gris claro, tarjetas blancas con borde fino, azul
`#1F4FD8` como único color de acción, color solo para estados (siempre con texto), sin degradé
azul-violeta ni cabeceras de tabla oscuras. Es **solo visual**: cada pantalla conserva sus funciones.

### Shell (`core/templates/core/base.html`)

- Tokens Taller en el `tailwind.config` inline + Inter de Google Fonts.
- Sidebar agrupada (Operación / Ventas y cobros / Fábrica / Análisis / Sistema) con el campo `grupo` en
  `ACCESS_MODULES` de `usuarios/access_control.py`. Los permisos no cambian.
- Topbar con buscador visual, badge Dólar BNA, campanita de avisos y chip de usuario.
- Select2 con los tokens (se conservan SweetAlert2 y `AkunSelect2`). Bloque nuevo `{% block title %}`.
- Los mensajes de Django salen como toast.

### Componentes

- **`static/css/taller.css`:** `.btn` (+ `-primary|-secondary|-ghost|-danger`, `-sm`, `-icon`), `.card`, `.page-head`,
  `.badge` + `.b-gray|blue|violet|green|amber|red`, `.chip`, `.tabs`/`.tab`, `.tbl` + `.table-wrap`, `.toolbar`,
  `.pager`, `.field`/`.input`, `.kebab`, `.empty`, `.toast`.
- **Includes en `core/templates/core/ui/`** (usar siempre con `only`): `page_header.html`, `badge.html`,
  `empty_state.html`, `kebab_menu.html`, `pagination.html`. Se restyló `core/includes/table_filters.html`
  (lo usan 12 listados).
- **Kebab de fila:** `view_url`, `edit_url`, `extra_url`/`extra_label`/`extra_icon` y `delete_url`/`delete_name`
  (confirma con SweetAlert y hace POST con CSRF). Con `delete_label`, `delete_verb` y `delete_icon` la
  acción puede decir «Desactivar» en vez de «Eliminar» (lo usa `pricing`, que desactiva y no borra).

### Pantallas por módulo

| # | Módulo | Pantallas |
|---|---|---|
| 1 | Acceso y usuarios | login, inicio, lista y formulario de usuarios |
| 2 | Presupuestos | lista, nuevo, detalle (isla React), agregar ítem, editor de estructura, confirmar, importar REHAU |
| 3 | Cotizador y catálogo | calculadora y cotizador, catálogo de productos, perfiles, vidrios, opcionales y sus formularios (`pricing/*`, `productos/*`) |
| 4 | Comercial: ventas y clientes | dashboard, lista/detalle/formulario/cobro de ventas, clientes (lista, detalle, formulario, fusionar) |
| 5 | Comercial: compras, cuentas y reportes | compras (lista, detalle, formulario), cuentas, reportes (general, ventas, cobranzas, gastos, proveedores) solo de pantalla |
| 6 | Fábrica | pedidos de fábrica (lista y detalle), formulario de orden, pedidos por voz |
| 7 | Agenda, solicitudes y gastos | calendario y formulario de evento, solicitudes, gastos diarios |
| 8 | Facturación y contabilidad | facturas (lista, detalle, nueva), puntos de venta y números, plan de cuentas, libro IVA, balance, estado de resultados |
| 9 | Seguridad y configuración | salud, auditoría, backups (lista y login), datos de la empresa, configuración general |

### PDFs e impresión intactos

No se modificaron `presupuestos/pdf.html`, `presupuestos/recibo_blank.html`, `plantillas/orden_pdf.html`,
`comercial/recibo_pdf.html`, el PDF de venta (reportlab), los bloques `@media print` de
`comercial/reportes/*.html` ni `viewer3d.js`, `elevacion.js` y `estructura.js`. Verificado con
`git diff main` vacío sobre esos archivos.

## Criterios cumplidos

Ver los de [REQ-064](../requerimientos/REQ-064-rediseno-taller.md). Suite completa: 25 failures + 9 errors,
igual que la línea base de `main`.

## Desvíos de solo-visual a confirmar por el usuario

El pedido era «solo visual», pero hay cambios que alteran lo que se ve o se puede hacer. Hay que decidir
si se dejan, se revierten o se pasan a requerimiento propio:

1. **`user_form` (alta/edición de usuario) sin pestañas + contadores:** el formulario se reorganizó sin las
   pestañas de antes y con contadores de permisos.
2. **Login:** el campo cambió de «Email» a «Usuario» y se quitó el enlace «Regístrate».
3. **Pestañas nuevas:** `comercial/_nav_comercial.html` (**no filtra por permiso**: muestra todas las
   pestañas aunque el usuario no tenga acceso a alguna) y `security/_tabs_seguridad.html`.

## Limitaciones conocidas

- Cliente y las tablas de `pricing` no tienen fecha de modificación: el tiempo real no detecta ediciones, solo altas y bajas.
- Hay propuestas de los mockups que no se implementaron (por ser funciones nuevas); están en el [backlog](../team/backlog.md).
- Falta el recorrido completo con Playwright contra los mockups.

## Archivos

- Base: `core/templates/core/base.html`, `static/css/taller.css`, `core/templates/core/ui/*`, `core/includes/table_filters.html`, `usuarios/access_control.py` (`grupo`)
- Templates de cada módulo (ver tabla) y sus tests
- Detalle de commits: `git log main..development` (Fase 0 `ae8a00d` y un commit por módulo)
