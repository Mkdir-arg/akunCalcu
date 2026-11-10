# FEAT-051 — Abertura de la Orden de Fabricación elegida del catálogo

**Estado:** Implementado (en `development`, sin commitear)
**Fecha:** 2026-11-10
**Requerimiento:** [REQ-067](../requerimientos/REQ-067-orden-abertura-desde-catalogo.md)
**ADR:** ADR-027

## Qué hace

En la edición de la orden (`/plantillas/ordenes/<id>/editar/`), la tarjeta **«Abertura»** reemplaza
el texto libre por los desplegables en cascada del cotizador:
Extrusora → Línea → Tipo de abertura → Marco → Modelo de hoja → Vidrio, más Color.

- Cada desplegable se llena con las mismas APIs que el cotizador (`/pricing/api/pricing/...`). Cambiar
  uno limpia los de abajo.
- Al elegir la hoja, **Cantidad de hojas** se completa con la del catálogo y queda bloqueada. Si el
  catálogo no la tiene, se carga a mano.
- Un recuadro **«Guardado en la orden»** muestra lo que imprime el PDF hoy.
- Si lo guardado se escribió a mano o ya no está en el catálogo, un aviso amarillo lo dice y el dato se
  conserva mientras no se toquen los desplegables.
- El servidor valida la combinación: no se puede guardar un marco de otro producto, un vidrio que la
  hoja no admite ni nada bloqueado.
- En una orden liberada se mantiene el circuito: motivo obligatorio y sube la revisión.

## Criterios de aceptación

- [x] Bloque «Abertura» con los desplegables en cascada del cotizador
- [x] Filtrado con las mismas APIs y reglas; cambiar uno limpia los de abajo
- [x] Cantidad de hojas automática desde la hoja
- [x] Se guardan los mismos 7 textos; el PDF no cambia
- [x] Lo guardado se ve al abrir; sin tocar el bloque, no cambia
- [x] Valor fuera del catálogo: aviso y no se pierde
- [x] Orden liberada: motivo y revisión nueva
- [x] Los demás campos del Detalle no cambian
- [x] Cotizador de presupuestos y de «Agregar orden» sin cambios
- [x] No se calcula ni se guarda precio

## Archivos

| Archivo | Cambio |
|---|---|
| `plantillas/models.py` | `OrdenFabricacion.seleccion_catalogo` (JSON, default `{}`) |
| `plantillas/migrations/0018_orden_seleccion_catalogo.py` | Agrega el campo. Sin datos |
| `plantillas/services/abertura_catalogo.py` (nuevo) | `resolver_cadena`, `resolver_color`, `seleccion_inicial` |
| `plantillas/forms.py` | Textos de la abertura como ocultos; campos `cat_*` y `cat_cambios`; `clean()` resuelve y recorta al `max_length` |
| `plantillas/views.py` | `orden_edit`: guarda `seleccion_catalogo`, selección inicial y recuadro «Guardado» |
| `plantillas/templates/plantillas/orden_form.html` | Tarjeta Abertura y cascada en JS simple. Marco, Hoja, Cantidad y Vidrio salen del bloque Detalle |
| `usuarios/access_control.py` | `despiece.pedidos` puede leer extrusoras, líneas, productos, marcos, hojas, vidrios y tratamientos. El cálculo sigue cerrado |
| `plantillas/tests_abertura_catalogo.py` (nuevo) | 21 tests (crean a mano las tablas legacy de pricing) |

## Decisiones técnicas

- **El navegador manda IDs, el servidor escribe los textos.** Así la orden solo guarda combinaciones
  que existen. Los textos siguen siendo la fuente del PDF.
- **`cat_cambios` decide qué se reemplaza** (`cadena` y/o `color`). Sin cambios no se toca nada,
  aunque lleguen IDs: protege las órdenes viejas escritas a mano.
- **Selección inicial:** primero `seleccion_catalogo`; si está vacío, los IDs del snapshot del ítem
  del presupuesto, pero solo si el marco del snapshot coincide con el texto de la orden (en una
  estructura el ítem no es el módulo).
- **JS simple en vez de React:** son 7 selects y así no se toca el cotizador de «Agregar orden».
  Los selects llevan `no-select2`.

## Pendiente

- Probar la cascada en prod con el catálogo real (orden 390 de PF-0189).
- «Agregar orden» sigue sin guardar el Tipo de marco (FEAT-023). Candidato a `/fix`.
