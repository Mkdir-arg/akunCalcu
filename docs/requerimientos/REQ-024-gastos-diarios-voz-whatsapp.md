# REQ-024 — Gastos Diarios por nota de voz de WhatsApp

- **Estado:** En desarrollo
- **Fecha:** 2026-05-17
- **Derivó en:** —

## Idea original
Crear un módulo "Gastos Diarios" en AkunCalcu donde el usuario, mediante notas de voz enviadas a un WhatsApp personal, registre automáticamente los gastos del día. El audio se transcribe, se procesa con IA para extraer una lista de gastos (descripción + monto) y queda registrado en el sistema con estado **en espera** hasta que sea aprobado o rechazado desde la web.

## Contexto
- Reutiliza el patrón ya implementado en la app `pedidos` (Telegram + n8n + Whisper + GPT-4o-mini) — ver REQ-002 / FEAT-001.
- Reutiliza la misma instancia de n8n que ya recibe los audios de Telegram.
- WhatsApp se integra mediante **Evolution API** (Docker, open source, vía QR de WhatsApp Web). El usuario usará su número personal.

## User Story
> Como **dueño / administrador**, quiero **mandar una nota de voz por WhatsApp** describiendo los gastos del día para que **queden registrados automáticamente en AkunCalcu con estado "en espera"** y luego poder **aprobarlos o rechazarlos desde la web**.

## Criterios de aceptación
- [ ] Existe una app Django nueva llamada `gastos_diarios` con un model `GastoDiario` (descripción, monto, fecha, estado, número de origen, audio_id de referencia).
- [ ] Existe un model `NumeroAutorizado` con la lista blanca de números de WhatsApp que pueden registrar gastos.
- [ ] Existe un endpoint `POST /gastos-diarios/api/registrar/` que recibe N gastos y los crea en estado `EN_ESPERA`.
- [ ] El endpoint valida el header `X-Bot-Secret` contra una env var (mismo patrón que pedidos).
- [ ] El endpoint valida que el número de WhatsApp esté autorizado; si no, devuelve 403.
- [ ] Existe una vista web `/gastos-diarios/` con listado de gastos paginado, filtrable por estado y fecha.
- [ ] Cada gasto se puede aprobar o rechazar desde el listado (cambia el estado).
- [ ] La confirmación de aprobar/rechazar usa SweetAlert2.
- [ ] Existe un CRUD básico para `NumeroAutorizado` (solo staff).
- [ ] El módulo aparece en el menú principal con permisos según `usuarios.permisos`.
- [ ] Hay tests de model (`__str__`, estados), tests del endpoint API (autorización + creación) y tests de las views (status 200 con login, 302 sin login).
- [ ] La documentación incluye el JSON esperado por el endpoint para que se pueda armar el workflow n8n.

## Complejidad estimada
**Mediano** — App nueva pero el patrón está claro (similar a `pedidos`). Sin cambios en otras apps.

## Relación con backlog
No estaba en el backlog. Se agrega como US-024 al activarse `/feature`.

## Fuera de alcance
- La configuración de Evolution API y el workflow de n8n se documentan pero no se implementan en código Django (queda como tarea del usuario, igual que con Telegram).
- No hay reportes / exportación por ahora.
- No hay categorías de gasto (descripción libre por ahora).
- No hay vinculación con la app `comercial.gastos` existente (es un módulo distinto, foco en captura rápida por voz).
