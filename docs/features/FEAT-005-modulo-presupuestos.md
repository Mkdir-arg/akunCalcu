# FEAT-005 — Módulo de Presupuestos

**Estado:** Implementado
**Fecha:** 2026-03-11
**Deriva de:** [REQ-006](../requerimientos/REQ-006-modulo-presupuestos.md)
**Rol en el proceso productivo:** Paso 1 de fábrica (cotización → confirmación → producción futura)

---

## Descripción funcional

Módulo completo para crear y gestionar presupuestos de aberturas de aluminio. Permite vincular un cliente con una cotización formal, agregarle N ítems usando la misma lógica del cotizador, agregar comentarios de seguimiento, cambiar su estado y generar un PDF imprimible.

Una vez que un presupuesto pasa a estado `Confirmado`, en una futura fase 2 se integrará con el módulo de fábrica para iniciar la producción.

---

## Criterios de aceptación cumplidos

- [x] Se puede crear un presupuesto seleccionando un cliente existente
- [x] Número autogenerado con formato `PRES-AAAA-NNN`
- [x] Fecha de creación y fecha de expiración configurable
- [x] Estados: Borrador, Enviado, Confirmado, Vencido, Cancelado
- [x] Se pueden agregar N ítems con la lógica del cotizador (extrusora → línea → producto → marco → hoja → vidrio → dimensiones → margen)
- [x] Cada ítem muestra descripción, dimensiones, margen y precio calculado
- [x] Se puede eliminar ítems mientras el presupuesto está en Borrador
- [x] Al generar PDF se abre una vista imprimible (impresión desde el browser / guardar como PDF)
- [x] Presupuestos Confirmados y Cancelados no se pueden modificar
- [x] Lista de presupuestos con filtro por estado y cliente
- [x] Historial de comentarios con fecha y autor
- [x] Comentarios en orden cronológico en el detalle
- [x] Interfaz limpia y simple de usar

---

## Archivos involucrados

### Nuevos
| Archivo | Descripción |
|---------|-------------|
| `presupuestos/__init__.py` | Módulo Python |
| `presupuestos/apps.py` | Configuración de app Django |
| `presupuestos/models.py` | Modelos: `Presupuesto`, `ItemPresupuesto`, `ComentarioPresupuesto` |
| `presupuestos/forms.py` | Forms: `PresupuestoForm`, `ItemPresupuestoForm`, `ComentarioForm` |
| `presupuestos/views.py` | 9 views: lista, crear, detalle, editar, agregar_item, eliminar_item, comentar, cambiar_estado, pdf |
| `presupuestos/urls.py` | URLs con namespace `presupuestos` |
| `presupuestos/tests.py` | 12 tests de modelos y views |
| `presupuestos/migrations/0001_initial.py` | Migración inicial (3 tablas) |
| `presupuestos/templates/presupuestos/lista.html` | Listado con filtros |
| `presupuestos/templates/presupuestos/form.html` | Crear/editar cabecera |
| `presupuestos/templates/presupuestos/detalle.html` | Detalle + ítems + comentarios + panel de estado |
| `presupuestos/templates/presupuestos/item_form.html` | Cotizador embebido (React) para agregar ítems |
| `presupuestos/templates/presupuestos/pdf.html` | Vista de impresión sin base.html |

### Modificados
| Archivo | Cambio |
|---------|--------|
| `akuna_calc/settings.py` | Agrega `presupuestos` a `INSTALLED_APPS` |
| `akuna_calc/urls.py` | Agrega `path('presupuestos/', include('presupuestos.urls'))` |
| `core/templates/core/base.html` | Link "Presupuestos" en el sidebar |

---

## Modelos

### `Presupuesto`
- `numero`: CharField único, autogenerado como `PRES-AAAA-NNN`
- `cliente`: FK → `comercial.Cliente`
- `fecha_expiracion`: DateField
- `estado`: choices (borrador / enviado / confirmado / vencido / cancelado)
- `notas`: TextField
- `total`: DecimalField recalculado al agregar/quitar ítems
- `created_by`: FK → User

### `ItemPresupuesto`
- FK → `Presupuesto`
- `descripcion`, `cantidad`, `ancho_mm`, `alto_mm`, `margen_porcentaje`
- `precio_unitario`, `precio_total` (calculado en `save()`)
- `resultado_json`: snapshot completo del resultado del calculador

### `ComentarioPresupuesto`
- FK → `Presupuesto`, FK → User (autor)
- `texto`, `created_at`

---

## Flujo de uso

```
1. Crear presupuesto → elegir cliente + fecha de expiración
2. Agregar ítems → cotizador embebido (selección cascada + dimensiones + margen → calcular → agregar)
3. Cambiar estado (Borrador → Enviado → Confirmado)
4. Agregar comentarios de seguimiento en cualquier momento
5. Generar PDF → vista imprimible para imprimir o guardar como PDF
6. [Fase 2] Al confirmar → pasa a módulo de fábrica
```

---

## Decisiones técnicas

### ADR-006: PDF via HTML de impresión (sin librería externa)
El PDF se genera como una página HTML con `@media print` optimizado. No se usaron librerías como `weasyprint` o `reportlab` para evitar dependencias extra. El usuario imprime desde el browser o usa "Guardar como PDF". Ver `ADR-006` en `docs/team/decisions.md`.

### Cotizador embebido en item_form
Se reutilizó React (ya cargado en el cotizador principal) para el formulario de ítems. La lógica de cálculo se delega al endpoint existente `/pricing/api/pricing/calculate/`. El resultado se guarda como JSON snapshot en `resultado_json` del ítem.

### Protección de presupuestos bloqueados
Los estados `confirmado` y `cancelado` bloquean toda modificación (editar, agregar ítems, eliminar ítems, cambiar estado). Se verifica en cada view con `presupuesto.esta_bloqueado()`.

---

## URLs

| URL | Nombre | Descripción |
|-----|--------|-------------|
| `/presupuestos/` | `presupuestos:presupuestos-lista` | Listado con filtros |
| `/presupuestos/nuevo/` | `presupuestos:presupuestos-crear` | Crear |
| `/presupuestos/<pk>/` | `presupuestos:presupuestos-detalle` | Detalle |
| `/presupuestos/<pk>/editar/` | `presupuestos:presupuestos-editar` | Editar cabecera |
| `/presupuestos/<pk>/item/agregar/` | `presupuestos:presupuestos-item-agregar` | Agregar ítem |
| `/presupuestos/<pk>/item/<ipk>/eliminar/` | `presupuestos:presupuestos-item-eliminar` | Eliminar ítem |
| `/presupuestos/<pk>/comentar/` | `presupuestos:presupuestos-comentar` | Agregar comentario |
| `/presupuestos/<pk>/estado/` | `presupuestos:presupuestos-estado` | Cambiar estado |
| `/presupuestos/<pk>/pdf/` | `presupuestos:presupuestos-pdf` | Vista PDF |

---

## Pendiente (Fase 2)

- Integración con módulo de fábrica: al confirmar un presupuesto, generar una orden de producción
- Envío del PDF por email al cliente
- Vencimiento automático de presupuestos (tarea programada)
