# REQ-065 — Actualización en vivo por polling (listados, avisos, dólar, KPIs y edición simultánea)

- **Estado:** Implementado (en la rama `development`, sin desplegar)
- **Derivó en:** [FEAT-047](../features/FEAT-047-tiempo-real.md)
- **Fecha:** 2026-10-29
- **Complejidad:** Grande
- **Apps afectadas:** `core` (infraestructura) y un `live.py` por app
- **Decisión relacionada:** [ADR-024](../team/decisions.md)

## User Story

Como **usuario que tiene varias personas trabajando sobre los mismos datos** quiero **ver los cambios
nuevos sin recargar la página y saber si alguien más está editando lo mismo**, para **no trabajar sobre
datos viejos ni pisar el trabajo de un compañero**.

## Decisiones tomadas (usuario)

- **Polling de 15 a 30 s**, sin Redis ni ASGI (se eligió 20 s).
- Alcance: listados y tableros, avisos (campanita), Dólar BNA y KPIs, y aviso de edición simultánea.

## Criterios de Aceptación

- [x] Un endpoint liviano `GET /core/api/live/` con una consulta agregada por fuente, solo para usuarios logueados y filtrado por permisos
- [x] Cada app declara sus fuentes en su propio `live.py`, sin tocar `core`
- [x] Los listados avisan «Hay cambios · Actualizar» o se refrescan solos (`?partial=1`)
- [x] Campanita con avisos por usuario: presupuesto confirmado, pedido por voz nuevo, backup fallido, solicitud asignada
- [x] Dólar BNA y KPIs del tablero se actualizan sin recargar
- [x] «Ramiro también está editando este presupuesto» en las pantallas de edición
- [x] El polling se pausa con la pestaña oculta y no cuenta como actividad (no renueva la sesión ni la inactividad, no se audita)
- [x] Tests: 200, 302 sin login, filtrado por permisos, caducidad de presencia, sesión no renovada por el poll
