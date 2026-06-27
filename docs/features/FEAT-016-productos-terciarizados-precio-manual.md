# FEAT-016 — Productos terciarizados con precio manual

**Estado:** Implementado
**Fecha:** 2026-06-27
**Deriva de:** [REQ-033](../requerimientos/REQ-033-productos-terciarizados-precio-manual.md) (RF-015)

## Descripción funcional

Permite cargar productos que Akun **no fabrica** (terciarizados/externos, ej. cortinas roller). El producto se da de **alta solo con el flag "terciarizado" (sin precio)**. El **precio por m² se ingresa al cotizar**: cuando en el cotizador se selecciona un producto terciarizado, aparece un input "Precio por m²", y el cotizador calcula `área (m²) × ese precio` en lugar de despiezar por fórmula.

El precio manual es el subtotal base; se le aplica el mismo margen del presupuesto que a los fabricados. No se despieza nada (perfiles/vidrios/accesorios/mano de obra).

## Criterios de aceptación (cumplidos)

- [x] Un producto puede marcarse como **terciarizado** desde `/pricing/config/productos/nuevo/` (o editar), **sin cargar precio**.
- [x] En el cotizador, al seleccionar un producto terciarizado aparece un input **"Precio por m²"**.
- [x] El cálculo usa ese precio (`área × precio_manual_m2`) y **no despieza** perfiles/vidrios/accesorios.
- [x] Si el producto es terciarizado y no se ingresó precio, el cálculo devuelve error claro ("Indicá el precio por m²").
- [x] Los productos fabricados se calculan por fórmula **igual que antes** (branch aislado, verificado por test).
- [x] El desglose (modal en `presupuestos/detalle.html`) muestra la línea del producto terciarizado.

## Archivos involucrados

| Archivo | Cambio |
|---------|--------|
| `pricing/models.py` | `Producto`: campo `terciarizado` (bool). El precio NO se guarda en el producto |
| `pricing/migrations/0003_producto_terciarizado.py` | NUEVO — `RunSQL` que agrega la columna `terciarizado` a la tabla legacy `productos` + `state_operations` |
| `pricing/forms.py` | `ProductoForm`: checkbox `terciarizado` (sin campo de precio) |
| `pricing/templates/pricing/config/producto_form.html` | El checkbox se renderiza en el loop del form (sin toggle de precio) |
| `pricing/catalog_views.py` | `ProductosListView` expone `terciarizado` para que el cotizador lo sepa |
| `pricing/serializers.py` | `PricingCalculateSerializer` acepta `precio_manual_m2` (opcional) |
| `pricing/services/calculator.py` | Branch en `calculate()` (si `producto.terciarizado`) + `_calcular_terciarizado` que usa el precio del payload (error si falta) |
| `pricing/templates/pricing/cotizador.html` | Input "Precio por m²" visible solo si el producto elegido es terciarizado; se manda en el payload |
| `presupuestos/templates/presupuestos/detalle.html` | Sección "Producto terciarizado" en el modal de desglose |
| `pricing/tests.py` | 4 tests del cálculo terciarizado |

## Decisiones técnicas

- **El precio se ingresa al cotizar, no en el producto** (cambio de lógica respecto del primer diseño): el mismo producto terciarizado puede cotizarse a distintos precios sin reconfigurarlo. Por eso `precio_manual_m2` viaja en el payload de cotización (`PricingCalculateSerializer` → `configuracion`), no es un campo del modelo.
- **Persistencia del flag en tabla legacy:** `Producto` es `managed=False`; la columna `terciarizado` se agrega con migración `RunSQL` + `state_operations`. Ver ADR-011.
- **Branch temprano y aislado** en `calculate()`: se corta apenas se resuelve el marco, solo si `producto.terciarizado` → cero impacto en productos fabricados.

## Pendiente de verificación en deploy

La migración `0003` no se pudo ejecutar en el entorno local de test (SQLite, sin las tablas legacy). **Debe correrse y verificarse en Docker MySQL y en producción (Railway/pythonanywhere)** — si la columna ya existiera en algún entorno, saltear con `--fake` allí.
