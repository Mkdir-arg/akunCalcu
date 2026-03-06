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
1. Leer `docs/requerimientos/_INDEX.md`, `docs/team/backlog.md` y `docs/team/current-sprint.md`
2. Escribir **User Story** con formato:
   ```
   Como [usuario] quiero [funcionalidad] para [beneficio]
   ```
3. Definir **Criterios de Aceptación** (checklist)
4. Estimar complejidad: Pequeño / Mediano / Grande
5. Crear `docs/requerimientos/REQ-XXX-nombre.md` con estado `En desarrollo` y actualizar `docs/requerimientos/_INDEX.md`
6. **PAUSAR y mostrar al usuario. Esperar aprobación.**

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
4. Escribir tests básicos para lo implementado:
   - Si se creó/modificó un model → test de `__str__` y campos críticos
   - Por cada view nueva → test de status code y redirección si no hay login
   - Ubicación: `app/tests.py` o `app/tests/` si hay muchos
   - Correr al terminar: `docker-compose exec web python manage.py test nombre_app`
5. **Mostrar resumen de archivos modificados + resultado de tests. Esperar aprobación para continuar.**

### Paso 4 — Reviewer activa (solo si Paso 3 aprobado)
Releer cada archivo modificado y verificar:

**Criterios de aceptación (verificar contra Paso 1):**
- [ ] Cada criterio de aceptación definido en el Paso 1 está cumplido — verificar uno por uno
- [ ] El flujo funciona de punta a punta, no solo compila
- [ ] Los tests pasan sin errores: `docker-compose exec web python manage.py test nombre_app`

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
1. Crear `docs/features/FEAT-XXX-nombre.md` con: descripción funcional, criterios cumplidos, archivos modificados y decisiones técnicas
2. Actualizar `docs/features/_INDEX.md` con la nueva feature
3. Actualizar `docs/requerimientos/REQ-XXX.md`: estado → `Implementado`, agregar link a FEAT-XXX
4. Agregar entrada a `docs/team/changelog.md`
5. Marcar ítem como completado en `docs/team/current-sprint.md`
6. Si hubo decisión técnica importante → agregar ADR en `docs/team/decisions.md`
7. Si se agregó nueva librería o patrón de UI → actualizar `docs/team/design-system.md`
8. Actualizar `memory/MEMORY.md` si hay algo relevante para futuras sesiones

---

## Definition of Done (aplica a TODOS los workflows)

Ningún trabajo se considera terminado hasta que cumpla todos estos puntos:

- [ ] El código implementa exactamente lo pedido (ni más, ni menos)
- [ ] Existe al menos un test por cada view nueva y por cada model nuevo
- [ ] Los tests pasan: `docker-compose exec web python manage.py test`
- [ ] Si hubo cambio de model → existe la migración
- [ ] El Reviewer aprobó el código (checklist completo)
- [ ] La documentación fue actualizada (FEAT/FIX/HFX según corresponda)
- [ ] No se introdujeron vulnerabilidades de seguridad

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
- **N+1 queries**: usar `select_related` para FK y `prefetch_related` para M2M en listados
- **404/403**: usar `get_object_or_404` y `PermissionDenied`, nunca retornar 200 con error
- **Paginación**: listados con más de 20 registros deben paginar
- **Tests**: mínimo un test por view (status code) y uno por model nuevo (`__str__`, campos críticos)

## Convenciones de frontend

Antes de escribir cualquier template nuevo, leer `docs/team/design-system.md`.

Reglas no negociables:
- Siempre extender `core/base.html`
- Usar las clases de color del design system (no inventar colores)
- Confirmaciones de eliminación siempre con SweetAlert2, nunca `confirm()` nativo
- No agregar nuevas librerías JS/CSS sin pasar por el Arquitecto y registrar ADR
- Los `<select>` tienen Select2 automático desde base.html — no duplicar

## Comandos disponibles

| Comando | Activa | Cuándo usarlo |
|---------|--------|---------------|
| `/feature [idea]` | Equipo completo (PO→Arq→Dev→Review→Docs) | Nueva funcionalidad |
| `/fix [bug]` | Arq→Dev→Review→Docs | Bug en ciclo normal |
| `/hotfix [problema]` | Dev→Review→Docs | Parche urgente en producción |
| `/idea [idea libre]` | PO + Arq (solo discovery) | Explorar una idea antes de comprometerse a desarrollarla |
| `/sprint-plan` | PO | Planificar el sprint |
| `/sprint-review` | PO + Docs | Revisar el sprint |
| `/status` | Todos | Ver estado actual del proyecto |

## Comandos directos a agentes

Para hablar con un agente específico sin seguir el flujo completo:

| Comando | Agente | Cuándo usarlo |
|---------|--------|---------------|
| `/po [pregunta]` | Product Owner | Discutir valor, user stories, priorización |
| `/arq [pregunta]` | Arquitecto | Diseño técnico, impacto, viabilidad |
| `/dev [tarea]` | Desarrollador | Código puntual, debugging, preguntas sobre el código |
| `/reviewer [archivo]` | Reviewer | Revisión de código específico |
| `/docu [qué documentar]` | Documentador | Actualizar documentación manualmente |

## Workflow de un Fix (/fix)

Flujo liviano para bugs dentro del sprint. Sin Product Owner.

```
Arquitecto → Desarrollador → Reviewer → Documentador
```

El Documentador agrega entrada en `docs/fixes/_LOG.md` con número FIX-XXX.

## Workflow de un Hotfix (/hotfix)

Flujo mínimo para producción urgente. Sin análisis extendido.

```
Desarrollador → Reviewer → Documentador
```

El Documentador agrega entrada en `docs/hotfix/_LOG.md` con número HFX-XXX.

## Workflow de una Idea (/idea)

Para explorar una idea antes de comprometerse a desarrollarla. No se escribe código.

```
Product Owner (analiza valor) → Arquitecto (evalúa viabilidad) → Documentador (crea REQ-XXX)
```

El resultado es `docs/requerimientos/REQ-XXX-nombre.md` listo para entrar a `/feature` cuando el usuario lo decida.

---

## Formato de sprint

- Sprints de 1 semana
- Planning al inicio: se seleccionan ítems del backlog
- Review al final: se verifica qué se completó
- Documentación en `docs/team/`

## Archivos clave de documentación

**Proceso del equipo (`docs/team/`):**
- `docs/team/backlog.md` → features pendientes
- `docs/team/current-sprint.md` → sprint activo
- `docs/team/decisions.md` → ADRs
- `docs/team/changelog.md` → historial resumido
- `docs/team/design-system.md` → convenciones de UI

**Documentación del sistema (`docs/`):**
- `docs/features/_INDEX.md` → tabla de todas las features implementadas
- `docs/features/FEAT-XXX-*.md` → detalle de cada feature
- `docs/fixes/_LOG.md` → log de todos los fixes
- `docs/hotfix/_LOG.md` → log de todos los hotfixes
- `docs/requerimientos/_INDEX.md` → tabla de todos los requerimientos
- `docs/requerimientos/REQ-XXX-*.md` → detalle de cada requerimiento
- `docs/V1-sistema.md` → descripción general del sistema

**Memoria:**
- `memory/MEMORY.md` → contexto rápido del proyecto (auto-cargado)
