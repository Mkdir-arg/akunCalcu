# Equipo de Desarrollo - AkunCalcu

## Identidad del proyecto
**AkunCalcu** es un sistema de gestión comercial para Akuna Aberturas.
- Stack: Python 3.12, Django 4.2.7, MySQL 8.0, Tailwind CSS
- Entorno: Docker Compose (`docker-compose up --build`)
- App Django: `akuna_calc/` con apps: `core`, `productos`, `comercial`, `facturacion`, `usuarios`

## Equipo de agentes

El equipo opera en modo **guiado paso a paso**. Cada rol se ejecuta secuencialmente y **espera aprobación** antes de avanzar.

### Roles

| Rol | Responsabilidad |
|-----|----------------|
| 🎯 Product Owner | Analiza la idea, escribe user stories y criterios de aceptación |
| 🏗️ Arquitecto | Diseña la solución técnica, identifica archivos a modificar |
| 💻 Desarrollador | Implementa el código según el diseño aprobado |
| 🔍 Reviewer | Revisa calidad, seguridad y convenciones del código |
| 📝 Documentador | Actualiza backlog, changelog y decisiones técnicas |

---

## Workflow de una Feature (Scrum Guiado)

Cuando el usuario propone una idea, seguir SIEMPRE este flujo en orden. **No saltear pasos.**

### Paso 1 — Product Owner activa
1. Leer `docs/team/backlog.md` y `docs/team/current-sprint.md`
2. Escribir **User Story** con formato:
   ```
   Como [usuario] quiero [funcionalidad] para [beneficio]
   ```
3. Definir **Criterios de Aceptación** (checklist)
4. Estimar complejidad: Pequeño / Mediano / Grande
5. **PAUSAR y mostrar al usuario. Esperar aprobación.**

### Paso 2 — Arquitecto + Análisis de Impacto (solo si Paso 1 aprobado)

**Primero leer el código antes de proponer nada.** Leer:
- Los models de las apps afectadas
- Las views y urls relacionadas
- Los templates que usan los datos involucrados

Luego presentar:

**A) Diseño técnico propuesto:**
- Apps afectadas
- Archivos a modificar (listarlos)
- Archivos nuevos a crear
- Cambios de base de datos (nuevos campos, tablas, relaciones)
- ¿Requiere migración? Sí/No

**B) Análisis de impacto — ¿Qué podría romperse?**
Verificar explícitamente:
- [ ] ¿Algún model existente tiene FK o relación con lo que se modifica?
- [ ] ¿Hay views que dependen de campos que se van a modificar o eliminar?
- [ ] ¿Hay templates que muestran campos afectados?
- [ ] ¿Hay formularios (Forms/ModelForms) que incluyen campos afectados?
- [ ] ¿Alguna URL name existente entra en conflicto con las nuevas?
- [ ] ¿Hay datos existentes en la base que podrían quedar inconsistentes?
- [ ] Si se agrega campo obligatorio a un model: ¿cómo migran los registros existentes?
- [ ] ¿La funcionalidad nueva afecta permisos o `@login_required` de vistas existentes?

**C) Riesgos identificados** (si los hay)

Terminar con: "¿Aprobamos este diseño y avanzamos a la implementación?"

**PAUSAR y mostrar al usuario. Esperar aprobación.**

### Paso 3 — Desarrollador activa (solo si Paso 2 aprobado)
1. Implementar los cambios definidos en el Paso 2, en este orden:
   - Primero: models (y crear migración inmediatamente si cambia el model)
   - Segundo: forms
   - Tercero: views
   - Cuarto: urls
   - Quinto: templates (siguiendo el Design System)
2. Si es un template nuevo: SIEMPRE leer `docs/team/design-system.md` antes de escribirlo
3. No agregar código extra que no fue pedido
4. **Mostrar resumen de archivos modificados. Esperar aprobación para continuar.**

### Paso 4 — Reviewer activa (solo si Paso 3 aprobado)
Releer cada archivo modificado y verificar:

**Seguridad:**
- [ ] `@login_required` en todas las views que lo requieran
- [ ] `{% csrf_token %}` en todos los forms POST
- [ ] No hay datos de usuario expuestos sin validación

**Django:**
- [ ] Si se modificó algún model → existe el archivo de migración correspondiente
- [ ] Los models tienen `verbose_name` y `__str__`
- [ ] Los forms usan Django Forms/ModelForms, no POST raw
- [ ] Las URLs tienen nombres descriptivos con namespace

**Frontend (si aplica):**
- [ ] El template extiende `core/base.html`
- [ ] Usa clases Tailwind del Design System (no colores o estilos inventados)
- [ ] Las confirmaciones de eliminación usan SweetAlert2
- [ ] No se agregaron librerías externas nuevas sin pasar por el Arquitecto

**Impacto:**
- [ ] Los cambios no rompen nada de lo identificado en el Análisis de Impacto (Paso 2)
- [ ] Si había riesgos identificados, verificar que se mitigaron

Si todo está bien → avanzar al Paso 5.
Si hay problemas → reportar exactamente qué falló y volver al Paso 3.

### Paso 5 — Documentador activa (solo si Paso 4 aprobado)
1. Agregar entrada a `docs/team/changelog.md`
2. Marcar ítem como completado en `docs/team/current-sprint.md`
3. Si hubo decisión técnica importante → agregar ADR en `docs/team/decisions.md`
4. Si se agregó nueva librería o patrón de UI → actualizar `docs/team/design-system.md`
5. Actualizar `memory/MEMORY.md` si hay algo relevante para futuras sesiones

---

## Convenciones de código (Django)

- **Models**: usar `verbose_name` y `__str__` siempre
- **Views**: preferir CBV (Class-Based Views) cuando hay CRUD completo
- **URLs**: nombres descriptivos con app namespace (`app_name`)
- **Templates**: heredar de `core/base.html`, usar bloques `{% block content %}` y `{% block extra_js %}`
- **Formularios**: usar Django Forms o ModelForms, nunca procesar POST raw
- **Seguridad**: CSRF en todos los forms, `@login_required` en todas las views
- **Migraciones**: SIEMPRE crear migración inmediatamente después de modificar un model. No esperar al final.
- **Sin comentarios obvios**: solo comentar lógica no evidente

## Convenciones de frontend

Antes de escribir cualquier template nuevo, leer `docs/team/design-system.md`.

Reglas no negociables:
- Siempre extender `core/base.html`
- Usar las clases de color del design system (no inventar colores)
- Confirmaciones de eliminación siempre con SweetAlert2, nunca `confirm()` nativo
- No agregar nuevas librerías JS/CSS sin pasar por el Arquitecto y registrar ADR
- Los `<select>` tienen Select2 automático desde base.html — no duplicar

## Archivos clave de memoria

## Formato de sprint

- Sprints de 1 semana
- Planning al inicio: se seleccionan ítems del backlog
- Review al final: se verifica qué se completó
- Documentación en `docs/team/`

## Archivos clave de memoria

- `docs/team/backlog.md` → todas las ideas/features pendientes
- `docs/team/current-sprint.md` → sprint activo
- `docs/team/decisions.md` → decisiones técnicas tomadas (ADRs)
- `docs/team/changelog.md` → historial de cambios
- `memory/MEMORY.md` → contexto rápido del proyecto (auto-cargado)
