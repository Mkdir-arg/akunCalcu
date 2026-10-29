# REQ-064 — Rediseño visual «Taller» de todo el sistema

- **Estado:** Implementado (en la rama `development`, sin desplegar)
- **Derivó en:** [FEAT-046](../features/FEAT-046-rediseno-taller.md)
- **Fecha:** 2026-10-29
- **Complejidad:** Grande (9 módulos en paralelo)
- **Apps afectadas:** todas las que tienen pantallas (`core`, `usuarios`, `presupuestos`, `pricing`, `productos`, `comercial`, `plantillas`, `pedidos`, `agenda`, `solicitudes`, `gastos_diarios`, `facturacion`, `contabilidad`, `security`, `configuracion`)
- **Decisión relacionada:** [ADR-023](../team/decisions.md)
- **Mockups:** 67 pantallas en [`docs/team/design/*.dc.html`](../team/design/) (sistema visual en `Main.dc.html`)

## User Story

Como **usuario del sistema** quiero **que todas las pantallas tengan el mismo estilo, claro y ordenado**,
para **encontrar las cosas siempre en el mismo lugar y trabajar sin distraerme con colores o botones que
cambian de un módulo a otro**.

## Contexto

La app mezclaba estilos por módulo (degradé azul-violeta, cabeceras de tabla oscuras, botones de varios
colores). Se aprobaron en Claude Design 67 mockups con el estilo «Taller» y se llevan a los templates reales.

## Decisiones tomadas (usuario)

- **Solo lo visual:** cada pantalla conserva sus funciones de hoy. Las propuestas nuevas de los mockups
  (pestañas, filtros, acciones nuevas) van al [backlog](../team/backlog.md).
- **Los PDF no se tocan:** ni HTML, ni CSS, ni la vista que los genera. Tampoco los bloques `@media print`
  de los reportes ni los JS de dibujo que usa el PDF (`viewer3d.js`, `elevacion.js`, `estructura.js`).
- Todo en la rama `development`; Railway solo despliega `main`.

## Criterios de Aceptación

- [x] Shell nuevo en `core/base.html`: tokens Taller, sidebar agrupada, topbar con buscador visual, Dólar BNA, campanita y chip de usuario
- [x] `static/css/taller.css` e includes reutilizables en `core/templates/core/ui/`
- [x] Las pantallas de los 9 módulos usan el sistema Taller (un primario por pantalla, kebab de fila, badges por estado, sin degradé ni cabeceras oscuras)
- [x] Los mensajes de éxito salen como toast; SweetAlert queda solo para confirmar borrados
- [x] Los permisos no cambian (el agrupado de la sidebar es solo visual)
- [x] `id`, `name`, `data-*` y `action` de formularios conservados; CSRF en los forms
- [x] PDF idénticos a `main` (`git diff main` vacío en los archivos de PDF)
- [x] Suite completa igual a la línea base de `main` (25 failures + 9 errors preexistentes)
- [ ] Revisar con el usuario los [desvíos de solo-visual](../features/FEAT-046-rediseno-taller.md#desvíos-de-solo-visual-a-confirmar-por-el-usuario)
- [ ] Recorrido con Playwright pantalla por pantalla contra el mockup
