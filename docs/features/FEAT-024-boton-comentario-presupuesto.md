# FEAT-024 — Botón "Comentario presupuesto" (Observaciones del PDF)

**Estado:** Implementado
**Fecha:** 2026-07-08
**Origen:** Pedido directo del usuario.

## Descripción funcional

En el detalle del presupuesto se agregó un botón **"Comentario presupuesto"** en la fila de acciones (junto a Editar, Agregar item, Presupuesto, Recibo, Eliminar). Al tocarlo abre un popup (SweetAlert2) con el texto del comentario **que sale impreso en el presupuesto** (aparece como **"Observaciones"** en el PDF). El popup viene **precargado con las Observaciones actuales** y, al guardar, las **reemplaza**.

## Aclaración importante (2026-07-08)

El sistema tiene **dos textos distintos** en un presupuesto, y esta feature apunta al segundo:

| | Qué es | Dónde se ve | Campo |
|---|---|---|---|
| Historial de comentarios | Comentarios **internos** (autor, fecha, prioridad) | Solo en el detalle | `ComentarioPresupuesto` (endpoint `comentar`, form inline al pie del historial) |
| **Observaciones** | Texto que **sale en el presupuesto impreso** | Detalle (bloque "Notas") **y en el PDF** | `Presupuesto.notas` (endpoint nuevo `actualizar_notas`) |

El botón "Comentario presupuesto" escribe en **Observaciones** (`notas`), **no** en el historial interno. El sistema de comentarios internos queda intacto (su form inline sigue funcionando).

## Criterios de aceptación cubiertos

- [x] Botón "Comentario presupuesto" en la fila de acciones del detalle.
- [x] Al tocarlo se abre un popup pidiendo el comentario.
- [x] El comentario se guarda en `Presupuesto.notas` y **sale impreso en el PDF** (Observaciones).
- [x] El popup precarga las Observaciones actuales y las **reemplaza** al guardar (decisión del usuario).
- [x] Se registra `updated_by` (quién editó).
- [x] Cancelar el popup no cambia nada.

## Archivos modificados

- `akuna_calc/presupuestos/views.py` — view nueva `actualizar_notas` (`@login_required @require_POST`) que reemplaza `notas` + setea `updated_by`.
- `akuna_calc/presupuestos/urls.py` — ruta `presupuestos-observaciones` (`<pk>/observaciones/`).
- `akuna_calc/presupuestos/templates/presupuestos/detalle.html` — botón, form oculto (postea `notas`) y JS `comentarPresupuesto()` (SweetAlert2 precargado con las notas actuales).
- `akuna_calc/presupuestos/tests.py` — tests.

Sin cambios de modelo ni migraciones (`Presupuesto.notas` y `updated_by` ya existían).

## Decisiones técnicas

- Se usa el campo `notas` existente (el mismo que se editaba desde "Editar" y que ya se muestra como "Observaciones" en el PDF), así el comentario del popup y el PDF quedan siempre consistentes.
- Reemplazo (no acumular), por decisión del usuario; el popup precarga el texto actual para poder editarlo.
- El popup queda disponible siempre (también con el presupuesto confirmado), ya que es una observación y no una edición del cálculo.

## Validación

- `python manage.py test presupuestos --settings=akuna_calc.settings_test_sqlite` → **99 OK** (nuevos: botón presente, reemplazo de Observaciones visible en detalle **y en el PDF**, login requerido; + test del comentario interno del historial).
