# REQ-020 — Auditoría de actividad de usuarios

> **Estado**: En desarrollo
> **Fecha**: 2026-05-10
> **Complejidad**: Grande
> **Derivará en**: —

## User Story
Como administrador quiero contar con una solapa de auditoría dentro del módulo de seguridad para ver qué hizo cada usuario en el sistema, para tener trazabilidad operativa de ingresos, ediciones, eliminaciones y otras acciones relevantes.

## Criterios de Aceptación
- [ ] Existe una nueva solapa `Auditoría` dentro del módulo `Seguridad`.
- [ ] La solapa muestra un listado cronológico de eventos realizados por usuarios autenticados.
- [ ] El sistema registra al menos los eventos de inicio de sesión, cierre de sesión, creación, edición y eliminación de registros en acciones relevantes del sistema.
- [ ] Cada evento muestra como mínimo usuario, fecha y hora, tipo de acción, módulo o sección afectada y una referencia legible del objeto o elemento impactado.
- [ ] El administrador puede filtrar la auditoría por usuario, tipo de acción, módulo o rango de fechas.
- [ ] El acceso a la auditoría está restringido a usuarios autorizados del módulo `Seguridad`.
- [ ] La auditoría no reemplaza validaciones de permisos existentes ni expone información sensible adicional fuera del contexto del evento.
- [ ] Si una acción falla y el sistema puede detectarlo de forma confiable, el evento distingue entre acción exitosa y acción fallida.

## Notas
- El objetivo es dar trazabilidad operativa transversal, no solo del módulo de seguridad.
- En el diseño técnico habrá que definir el mecanismo de captura de eventos para no duplicar lógica en cada vista.
- También habrá que definir el alcance inicial de módulos y acciones auditadas en esta primera versión para equilibrar utilidad, complejidad y rendimiento.