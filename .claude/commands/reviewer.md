# Comando /reviewer

Activa el modo Reviewer. Revisa código, detecta problemas de seguridad, convenciones o calidad, y da feedback concreto.

Usarlo cuando quieras una revisión independiente de código ya escrito.

---

## Instrucciones para el agente

Cuando el usuario ejecuta `/reviewer [archivo o descripción de qué revisar]`, activar el rol de Reviewer:

**Leer antes de revisar:**
- Los archivos indicados (leerlos completos)
- `CLAUDE.md` — convenciones del proyecto
- `docs/team/design-system.md` — si hay templates involucrados

**Checklist de revisión:**

**Criterios de aceptación (si aplica — revisar el REQ o la user story asociada):**
- [ ] Cada criterio de aceptación definido está cumplido — verificar uno por uno
- [ ] El flujo funciona de punta a punta, no solo compila
- [ ] Tests pasan: `docker-compose exec web python manage.py test nombre_app`

**Seguridad:**
- [ ] `@login_required` en todas las views que lo requieren
- [ ] `{% csrf_token %}` en todos los forms POST
- [ ] No hay datos de usuario expuestos sin validación
- [ ] No hay riesgo de inyección SQL, XSS u otros OWASP top 10

**Django:**
- [ ] Models tienen `verbose_name` y `__str__`
- [ ] Si hay cambio de model → existe la migración correspondiente
- [ ] Forms usan Django Forms/ModelForms (no POST raw)
- [ ] URLs tienen nombres descriptivos con namespace

**Frontend (si aplica):**
- [ ] Templates extienden `core/base.html`
- [ ] Usan clases Tailwind del design system
- [ ] Confirmaciones de eliminación usan SweetAlert2
- [ ] No se agregaron librerías nuevas sin ADR

**Calidad general:**
- [ ] No hay código innecesario o fuera del alcance
- [ ] La lógica es clara y no hay bugs obvios

**Modo de respuesta:**
Reportar cada problema encontrado con: archivo, línea aproximada, qué está mal, y cómo corregirlo.
Si no hay problemas: confirmarlo explícitamente.
