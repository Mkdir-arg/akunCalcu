# REQ-033 — Productos terciarizados con precio manual

**Estado:** Implementado
**Fecha:** 2026-06-27
**Origen:** RF-015 (Requerimientos Funcionales — prioridad media). Pedido del usuario para cargar productos que Akun no fabrica (ej. cortinas roller).

## User Story

Como administrador de pricing, quiero marcar ciertos productos como **terciarizados** (no fabricados por Akun, ej. cortinas roller) y asignarles un **precio manual**, para que el cotizador use ese precio en lugar de calcularlo por fórmula.

## Contexto

Hoy el precio de un producto se calcula íntegramente por fórmula (perfiles + vidrios + accesorios + mano de obra) en `pricing/services/calculator.py`. No existe forma de cargar un producto externo cuyo precio venga dado por el proveedor. El modelo `Producto` es una tabla legacy (`managed=False`, tabla `productos`) y **no tiene campo de precio**.

## Criterios de Aceptación

- [ ] Un producto puede marcarse como **terciarizado** (no fabricado) desde su edición en `/pricing/config/productos/<id>/editar/`.
- [ ] Un producto terciarizado tiene un **precio manual** editable.
- [ ] Al cotizar un producto terciarizado, el cotizador **usa el precio manual** en lugar del cálculo por fórmula (no intenta despiezar perfiles/vidrios/accesorios).
- [ ] Los productos NO terciarizados se siguen calculando por fórmula **exactamente igual que hoy** (sin cambios de comportamiento).
- [ ] En la edición, los campos de fórmula/despiece se ocultan o se vuelven irrelevantes cuando el producto es terciarizado (UX clara).
- [x] **Unidad del precio manual: precio por m²** (decidido con el usuario, 2026-06-27). El cotizador calcula `precio_manual_m2 × m²` del ítem, escalando con las medidas, consistente con el resto del cotizador.

## Fuera de alcance

- El cálculo por fórmula de los productos fabricados (no cambia).
- Listas de precios por proveedor / actualización masiva (eso es RF-023, otro REQ).

## Estimación

**Mediano.** La tabla `productos` es legacy `managed=False` sin campo de precio → el Arquitecto debe definir dónde y cómo persistir el flag y el precio (campo nuevo en la tabla legacy vía RunSQL, o tabla companion gestionada por Django). Toca el motor de cálculo (`calculator.py`) y la UI de edición de productos.

## Riesgos identificados

- Tocar el motor de cálculo (`calculator.py`) puede afectar el cotizador de productos fabricados si no se aísla bien el branch del terciarizado.
- Persistir un campo nuevo en una tabla legacy `managed=False` requiere una migración con `RunSQL` (patrón ya usado en el proyecto) o una tabla companion.

## Derivó en

[FEAT-016](../features/FEAT-016-productos-terciarizados-precio-manual.md)
