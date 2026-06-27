# FEAT-016 — Productos terciarizados con precio manual

**Estado:** Implementado
**Fecha:** 2026-06-27
**Deriva de:** [REQ-033](../requerimientos/REQ-033-productos-terciarizados-precio-manual.md) (RF-015)

## Descripción funcional

Permite cargar productos que Akun **no fabrica** (terciarizados/externos, ej. cortinas roller) y cotizarlos con un **precio manual por m²**, en lugar de calcular el precio por fórmula (perfiles + vidrios + accesorios + mano de obra).

Un producto marcado como terciarizado, al cotizarse, calcula: `área (m²) × precio_manual_m2`, y se le aplica el mismo margen del presupuesto que a los fabricados. No se despieza nada.

## Criterios de aceptación (cumplidos)

- [x] Un producto puede marcarse como **terciarizado** desde `/pricing/config/productos/<id>/editar/`.
- [x] Un producto terciarizado tiene un **precio manual por m²** editable (obligatorio si está terciarizado).
- [x] Al cotizar un terciarizado, el cotizador usa el precio manual y **no despieza** perfiles/vidrios/accesorios.
- [x] Los productos fabricados se calculan por fórmula **igual que antes** (branch aislado, verificado por test).
- [x] En la edición, el campo "Precio por m²" se muestra solo cuando "Terciarizado" está tildado (toggle JS).
- [x] El desglose (modal en `presupuestos/detalle.html`) muestra la línea del producto terciarizado.

## Archivos involucrados

| Archivo | Cambio |
|---------|--------|
| `pricing/models.py` | `Producto`: campos `terciarizado` (bool) y `precio_manual_m2` (decimal) |
| `pricing/migrations/0003_producto_terciarizado.py` | NUEVO — `RunSQL` que agrega las columnas a la tabla legacy `productos` + `state_operations` |
| `pricing/forms.py` | `ProductoForm`: 2 campos nuevos + validación (terciarizado exige precio) |
| `pricing/services/calculator.py` | Branch en `calculate()` + método `_calcular_terciarizado` |
| `pricing/templates/pricing/config/producto_form.html` | Toggle JS para mostrar el precio manual |
| `presupuestos/templates/presupuestos/detalle.html` | Sección "Producto terciarizado" en el modal de desglose |
| `pricing/tests.py` | 3 tests del cálculo terciarizado |

## Decisiones técnicas

- **Persistencia en tabla legacy:** `Producto` es `managed=False`, así que Django no gestiona su esquema. Las columnas se agregan con una migración `RunSQL` (ALTER TABLE explícito) + `state_operations` para mantener alineado el estado de migraciones. Ver ADR.
- **Precio manual = subtotal base:** el `precio_manual_m2 × m²` es el subtotal, al que se le aplica el margen del presupuesto igual que a los fabricados (integración uniforme). Para un precio final sin recargo, se cotiza con margen 0.
- **Branch temprano y aislado** en `calculate()`: se corta apenas se resuelve el marco, antes de cualquier consulta de despiece, y solo si `producto.terciarizado` y `precio_manual_m2` están cargados → cero impacto en productos fabricados.

## Pendiente de verificación en deploy

La migración `0003` no se pudo ejecutar en el entorno local de test (SQLite, sin las tablas legacy). **Debe correrse y verificarse en Docker MySQL y en producción (Railway/pythonanywhere)** — si la columna ya existiera en algún entorno, saltear con `--fake` allí.
