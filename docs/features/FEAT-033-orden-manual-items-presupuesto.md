# FEAT-033 — Orden manual de los ítems del presupuesto (arrastrar)

- **Estado:** Implementado
- **Fecha:** 2026-07-30
- **Requerimiento:** [REQ-043](../requerimientos/REQ-043-orden-manual-items-presupuesto.md)

## Descripción funcional

En el detalle de un presupuesto (`/presupuestos/<pk>/`), al lado del contador de ítems y del botón *Agregar*, aparece un botón **"Orden"**. Abre un modal con la lista de ítems donde el vendedor puede **arrastrarlos** para acomodarlos (o usar las flechas ▲▼). Al guardar, ese orden queda persistido y es **el que se ve en el detalle y en el PDF** que recibe el cliente.

El botón sólo aparece si el presupuesto tiene **2 ítems o más** y **no está confirmado ni cancelado**.

## Criterios de aceptación (cumplidos)

- [x] Botón "Orden" junto a los botones existentes de la sección Items.
- [x] Modal con la lista de ítems, arrastrable para subir/bajar.
- [x] El orden se guarda y persiste.
- [x] El PDF del presupuesto respeta ese orden.
- [x] Los ítems nuevos se agregan al final.
- [x] No se puede reordenar un presupuesto confirmado o cancelado.
- [x] Tests del endpoint y de la visibilidad del botón.

## Arquitectura

**Sin migración.** `ItemPresupuesto` ya tenía el campo `orden` (`PositiveIntegerField(default=0)`) y `Meta.ordering = ['orden', 'created_at']`. Como **el detalle y el PDF usan `presupuesto.items.all()`**, los dos aplican ese ordering: alcanzó con darle una UI para setearlo.

**Backend** (`presupuestos/views.py`):
- `reordenar_items` (`@login_required` + `@require_POST`): recibe `orden` (lista de PKs en el orden nuevo) y asigna `orden = 1..N` dentro de una transacción. Filtra ids que no pertenezcan al presupuesto, ignora duplicados y valores no numéricos, y **manda al final** cualquier ítem que no haya venido en la lista (caso: se agregó un ítem en otra pestaña mientras se ordenaba). Rechaza presupuestos bloqueados.
- `agregar_item`: el ítem nuevo pasa a usar `max(orden) + 1` en vez de `count()`, que colisionaba con el último ítem cuando el usuario ya había reordenado a mano.

**Frontend** (`presupuestos/templates/presupuestos/detalle.html`):
- Botón "Orden" + modal `#modal-orden` con la lista `#orden-lista`.
- **Drag & drop nativo de HTML5** (`draggable`, `dragstart`/`dragover`/`dragend`), **sin librería nueva** — respeta la regla del design system de no sumar dependencias sin ADR. Se setea `dataTransfer` porque Firefox no permite el drop sin datos.
- Además de arrastrar, cada fila tiene **flechas ▲▼** (`moverFilaOrden`), que hacen la feature usable en touch, donde el drag nativo de HTML5 no funciona.
- Al guardar, `guardarOrden()` arma inputs ocultos `orden` en el orden del DOM y postea el form.
- La numeración visible se recalcula con `renumerarOrden()` en cada cambio.

## Archivos involucrados

**Nuevos:** este doc + `docs/requerimientos/REQ-043-orden-manual-items-presupuesto.md`.

**Modificados:**
- `akuna_calc/presupuestos/views.py` — view `reordenar_items`; `agregar_item` usa `max+1`.
- `akuna_calc/presupuestos/urls.py` — ruta `presupuestos-items-reordenar`.
- `akuna_calc/presupuestos/templates/presupuestos/detalle.html` — botón, modal y JS.
- `akuna_calc/presupuestos/tests.py` — `ReordenarItemsTest` (11 tests).

## Decisiones técnicas

1. **Sin librería de drag & drop.** El design system prohíbe sumar dependencias sin ADR, y el drag nativo de HTML5 alcanza para una lista corta.
2. **Flechas además del arrastre.** El drag nativo no funciona en touch; las flechas cubren tablet/celular sin sumar librerías.
3. **`max+1` al agregar ítems.** Con `count()`, después de reordenar (1..N) un ítem nuevo recibía un `orden` ya usado y el desempate quedaba a merced de `created_at`.
4. **Los ítems ausentes de la lista van al final** en vez de quedar con su `orden` viejo, que podría pisar posiciones nuevas.

## Tests

`presupuestos.ReordenarItemsTest` — 11 tests: requiere login, GET → 405, guarda el orden, el orden llega al PDF, ignora ids de otro presupuesto, ítem ausente al final, presupuesto confirmado no reordena, ids inválidos no rompen, y visibilidad del botón (2+ ítems / 1 ítem / confirmado).

Suites `presupuestos` + `pricing` + `plantillas`: 253 corridos, con el baseline conocido de tablas legacy ausentes en SQLite (1 failure + 3 errors). Sin regresiones.

## Verificación pendiente (manual)

El arrastre real en el navegador (drag & drop nativo) no se puede cubrir con tests de Django: probar en Docker/producción que se pueda arrastrar, guardar y que el PDF salga en ese orden.
