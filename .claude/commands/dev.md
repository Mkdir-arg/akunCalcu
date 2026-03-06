# Comando /dev

Activa el modo Desarrollador. Implementa código puntual, responde preguntas técnicas sobre el código existente, o ayuda a depurar un problema específico.

Usarlo para tareas de código acotadas que no ameritan el flujo completo de /feature o /fix.

---

## Instrucciones para el agente

Cuando el usuario ejecuta `/dev [pregunta o tarea]`, activar el rol de Desarrollador:

**Leer antes de actuar:**
- Los archivos directamente relacionados con la tarea
- Si hay un template involucrado: leer `docs/team/design-system.md`

**Modo de respuesta:**

Pensar como Desarrollador: el foco es implementar correctamente, siguiendo las convenciones del proyecto.

- Si la tarea es implementar algo puntual → leer el código existente primero, luego implementar
- Si la pregunta es sobre cómo funciona algo → leer el código y explicar
- Si hay un error o excepción → leer el código relevante y diagnosticar
- Seguir siempre las convenciones de `CLAUDE.md`: `@login_required`, `{% csrf_token %}`, CBV para CRUD, etc.

**Importante:**
- No hacer cambios fuera del alcance pedido
- Si la tarea es más grande de lo esperado, avisar y sugerir usar `/feature` o `/fix`
