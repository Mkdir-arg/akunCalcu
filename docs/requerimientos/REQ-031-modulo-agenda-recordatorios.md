# REQ-031 — Módulo de Agenda con recordatorios por WhatsApp

- **Estado:** En desarrollo
- **Fecha:** 2026-06-07
- **Derivó en:** —

## Descripción

Módulo de **Agenda** en AkunCalcu para programar eventos (visitas, vencimientos, cobros, otros) que disparan **recordatorios por WhatsApp** a los números autorizados, vía n8n + Evolution API.

Generaliza el pedido previo de "mandar un mensaje de recordatorio" y reutiliza la tabla `NumeroAutorizado` de la app `gastos_diarios`.

## User Story

```
Como administrador de Akuna
quiero agendar eventos con título, descripción, fecha/hora, anticipación y recurrencia,
y elegir a qué números autorizados avisar,
para que el sistema envíe recordatorios automáticos por WhatsApp y no se me pasen visitas, vencimientos ni cobros.
```

## Decisiones de producto

- **Recurrencia:** eventos de única vez **y** recurrentes (diaria / semanal / mensual).
- **Destinatarios:** se eligen por evento entre los números autorizados (uno, varios o todos).
- **Momento de envío:** fecha + hora del evento, con opción de **anticipación** (avisar X días antes).

## Criterios de aceptación

- [ ] Se puede **crear, editar y eliminar** un evento con: título, descripción, tipo (visita/vencimiento/cobro/otro), fecha del evento, hora de envío, anticipación (días antes), recurrencia (ninguna/diaria/semanal/mensual) y destinatarios (números autorizados).
- [ ] **Listado** de eventos con paginación, mostrando próximo envío, tipo, recurrencia, destinatarios y estado.
- [ ] Un evento de **única vez** se envía una sola vez en `(fecha − anticipación)` a la hora indicada y luego queda en estado **Enviado**.
- [ ] Un evento **recurrente** se reenvía según su recurrencia a la hora indicada, **sin duplicar** dentro del mismo período.
- [ ] Existe un **endpoint protegido** (`X-Bot-Secret`) que devuelve los eventos **pendientes de envío** y permite **marcarlos como enviados**.
- [ ] Cada recordatorio se envía por **WhatsApp a cada destinatario** (vía n8n/Evolution), con el título y la descripción del evento.
- [ ] Las vistas web requieren `@login_required` y respetan el **control de acceso por módulo** (nuevo permiso "Agenda" en el sidebar).
- [ ] Existe un **workflow n8n nuevo** (Schedule Trigger → consultar pendientes → enviar → marcar enviado), sin tocar el workflow de gastos.
- [ ] Tests: model (`__str__`, lógica de "próximo envío"), endpoint de pendientes/marcado y vistas CRUD (status/login).

## Complejidad estimada

**Grande** (app nueva, lógica de scheduling, integración n8n, control de acceso).

## Relación con otros requerimientos

- Reutiliza `NumeroAutorizado` de **REQ-024** (Gastos Diarios por voz).
- Comparte el patrón de integración n8n + `X-Bot-Secret` de REQ-024 y **REQ-028** (backups).
