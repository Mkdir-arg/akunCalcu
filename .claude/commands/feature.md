# Comando /feature

Activa el equipo completo para implementar una nueva feature siguiendo el workflow Scrum definido en CLAUDE.md.

## Instrucciones para el agente

Cuando el usuario ejecuta `/feature [descripción de la idea]`, seguir EXACTAMENTE este proceso:

---

### PASO 1 — Product Owner

Leer primero:
- `docs/requerimientos/_INDEX.md` — para asignar el próximo número REQ
- `docs/team/backlog.md`
- `docs/team/current-sprint.md`

Luego presentar al usuario:

**User Story propuesta:**
```
Como [rol del usuario] quiero [funcionalidad] para [beneficio]
```

**Criterios de aceptación:**
- [ ] criterio 1
- [ ] criterio 2
- [ ] ...

**Complejidad estimada:** Pequeño / Mediano / Grande

**¿Está relacionada con algún ítem del backlog existente?** Sí/No

Crear el archivo `docs/requerimientos/REQ-XXX-nombre-corto.md` con estado `En desarrollo` antes de continuar.
Actualizar `docs/requerimientos/_INDEX.md` agregando la fila.

Terminar con: "¿Aprobamos esta user story y avanzamos al diseño técnico?"

**ESPERAR RESPUESTA DEL USUARIO ANTES DE CONTINUAR.**

---

### PASO 2 — Arquitecto + Análisis de Impacto (solo si Paso 1 aprobado)

**Antes de proponer nada, leer el código:** models, views, urls y templates de las apps afectadas.

Presentar al usuario:

**Diseño técnico:**
- Apps afectadas: ...
- Archivos a modificar: (listar cada uno)
- Archivos nuevos: (listar cada uno)
- Cambios de base de datos: ...
- ¿Requiere migración? Sí/No

**Análisis de impacto — ¿Qué podría romperse?**
Revisar explícitamente y reportar:
- [ ] FKs o relaciones en otros models que dependen de lo modificado
- [ ] Views que usan campos que se modifican o eliminan
- [ ] Templates que muestran esos campos
- [ ] Formularios que incluyen esos campos
- [ ] Conflictos de nombres en URLs
- [ ] Registros existentes en la DB que quedan inconsistentes
- [ ] Campos obligatorios nuevos: cómo migran los datos existentes

Si algún punto tiene riesgo → describir el riesgo y proponer cómo mitigarlo.

Terminar con: "¿Aprobamos este diseño y avanzamos a la implementación?"

**ESPERAR RESPUESTA DEL USUARIO ANTES DE CONTINUAR.**

---

### PASO 3 — Desarrollador (solo si Paso 2 aprobado)

Implementar en este orden:
1. Models → crear migración INMEDIATAMENTE después de cada cambio de model
2. Forms
3. Views
4. URLs
5. Templates → leer `docs/team/design-system.md` antes de escribir cualquier template

Seguir las convenciones de `CLAUDE.md`. No agregar código no pedido.

Al terminar, mostrar lista de archivos modificados/creados.

Terminar con: "¿Procedemos con la revisión?"

**ESPERAR RESPUESTA DEL USUARIO ANTES DE CONTINUAR.**

---

### PASO 4 — Reviewer (solo si Paso 3 aprobado)

Releer cada archivo modificado y verificar:

**Criterios de aceptación (del Paso 1):**
- [ ] Revisar cada criterio de aceptación definido en el Paso 1 — verificar uno por uno que esté cumplido
- [ ] El flujo funciona de punta a punta, no solo compila
- [ ] Tests pasan: `docker-compose exec web python manage.py test nombre_app`

**Seguridad:**
- [ ] `@login_required` donde corresponde
- [ ] `{% csrf_token %}` en todos los forms POST

**Django:**
- [ ] Si se modificó un model → existe la migración
- [ ] Models tienen `verbose_name` y `__str__`
- [ ] Forms usan Django Forms/ModelForms
- [ ] Listados con muchos registros tienen paginación
- [ ] Se usa `get_object_or_404` donde corresponde

**Frontend:**
- [ ] Templates extienden `core/base.html`
- [ ] Usan clases Tailwind del design system (no colores inventados)
- [ ] Confirmaciones usan SweetAlert2, no `confirm()` nativo
- [ ] No se agregaron librerías nuevas sin ADR

**Impacto:**
- [ ] No se rompió nada de lo identificado en el análisis de impacto

Si todo está bien → avanzar al Paso 5.
Si hay problemas → reportar exactamente qué falló y volver al Paso 3.

---

### PASO 5 — Documentador (solo si Paso 4 aprobado)

1. Crear `docs/features/FEAT-XXX-nombre.md` con el detalle de la feature:
   - Qué hace (descripción funcional)
   - Criterios de aceptación (todos marcados como cumplidos)
   - Archivos involucrados con descripción del cambio
   - Decisiones técnicas tomadas
2. Actualizar `docs/features/_INDEX.md` agregando la fila de la nueva feature
3. Actualizar el REQ correspondiente en `docs/requerimientos/REQ-XXX.md`:
   - Estado → `Implementado`
   - Agregar `Derivó en: FEAT-XXX`
4. Agregar la user story al `docs/team/backlog.md` como ✅ Completado
5. Actualizar `docs/team/current-sprint.md`
6. Agregar entrada en `docs/team/changelog.md`
7. Si hubo decisión técnica → agregar ADR en `docs/team/decisions.md`
8. Si se usó un patrón de UI nuevo → actualizar `docs/team/design-system.md`
9. Si hay algo relevante para futuras sesiones → actualizar `memory/MEMORY.md`

Terminar con: "Feature **FEAT-XXX** completada. Documentación actualizada."
