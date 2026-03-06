# Comando /docu

Activa el modo Documentador. Actualiza o genera documentación del proyecto: features, fixes, requerimientos, decisiones técnicas, design system, changelog.

Usarlo cuando quieras actualizar documentación manualmente o generar docs para código existente.

---

## Instrucciones para el agente

Cuando el usuario ejecuta `/docu [qué documentar]`, activar el rol de Documentador:

**Leer antes de actuar:**
- El archivo de documentación relevante (si existe)
- El código o contexto que se va a documentar

**Tareas posibles:**

**Si se pide documentar una feature ya implementada:**
1. Leer el código de la feature
2. Crear o actualizar `docs/features/FEAT-XXX-nombre.md`
3. Actualizar `docs/features/_INDEX.md`
4. Si deriva de un REQ → actualizar `docs/requerimientos/REQ-XXX.md` con el link a la feature

**Si se pide documentar un fix:**
1. Agregar entrada en `docs/fixes/_LOG.md`
2. Si el fix afecta un `docs/features/FEAT-XXX.md` → actualizar ese archivo

**Si se pide agregar un ADR:**
1. Leer `docs/team/decisions.md`
2. Agregar el nuevo ADR con el próximo número disponible

**Si se pide actualizar el design system:**
1. Leer `docs/team/design-system.md`
2. Agregar el nuevo patrón o componente

**Si se pide algo más general:**
Identificar qué documento corresponde y actualizarlo siguiendo el formato existente.

Siempre confirmar qué archivos se modificaron al terminar.
