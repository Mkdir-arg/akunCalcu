# FEAT-002 — CRUD Fábrica ABM

**Estado**: Implementado
**Fecha**: 2026-03-05
**Complejidad**: Grande
**Requerimiento origen**: REQ-003

---

## Qué hace

Permite a los administradores gestionar la configuración de fábrica completa desde la interfaz web: Extrusoras, Líneas, Productos, Marcos, Hojas, Interiores, Perfiles, Accesorios, Vidrios y Tratamientos.

Cada entidad tiene:
- **Lista** con columna Estado (activo/bloqueado) y acciones (editar / desactivar)
- **Crear** nuevo registro
- **Editar** registro existente
- **Desactivar** (soft delete — no elimina físicamente)

---

## Criterios de aceptación

- [x] El admin puede crear, editar y desactivar las 10 entidades de fábrica
- [x] La baja es lógica (soft delete via campo `bloqueado`)
- [x] Los registros desactivados se muestran con estado visible
- [x] Los formularios validan datos antes de guardar
- [x] Las entidades con PK de texto (Perfil, Accesorio, Vidrio) tienen formularios Create/Edit separados

---

## Archivos involucrados

| Archivo | Cambio |
|---------|--------|
| `akuna_calc/pricing/models.py` | Campo `bloqueado` agregado a Producto, Marco, Hoja, Interior |
| `akuna_calc/pricing/forms.py` | 10 ModelForms (Create/Edit separados para entidades con PK texto) |
| `akuna_calc/pricing/config_views.py` | 30 vistas nuevas (create/edit/delete × 10 entidades) |
| `akuna_calc/pricing/urls.py` | 30 nuevas URLs |
| `akuna_calc/pricing/migrations/0003_...py` | RunSQL: columna `bloqueado` en tablas legacy |
| Templates (10 formularios + 10 listas) | Reescritos con design system |

---

## Decisiones técnicas

- Modelos con `managed = False` (tablas legacy): IDs generados manualmente via `max(id) + 1`.
- Soft delete via `bloqueado = 'Si'` (convención existente en la DB legacy).
- Perfil, Accesorio y Vidrio tienen PK de texto (código definido por usuario) — requieren formularios Create/Edit separados para no permitir cambio de PK.

---

## Bugs resueltos durante desarrollo

- Templates referenciaban `producto.nombre`, `perfil.nombre`, `perfil.id` — campos inexistentes. Corregido a `descripcion` y `codigo`.
