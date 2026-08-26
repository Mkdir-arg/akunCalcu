# FEAT-036 — Revestimientos en el catálogo de vidrios

- **Estado:** Implementado
- **Fecha:** 2026-08-18
- **Requerimiento:** [REQ-046](../requerimientos/REQ-046-revestimientos-catalogo-vidrios.md)
- **ADR:** [ADR-018](../team/decisions.md)
- **App principal:** `pricing` · toca `presupuestos` (cotizador React y PDF)

## Qué hace

El catálogo de vidrios (`/pricing/config/vidrios/`) gana un campo **Tipo** con dos valores:
**Vidrio** y **Revestimiento**. En el editor de secciones del cotizador, los botones
*Vidrio* / *Ciego (chapa/panel)* filtran el selector por ese campo, alimentándose del **mismo
catálogo** en lugar de dos separados.

El selector de vidrio principal de la abertura también filtra `tipo='vidrio'`: antes nada impedía
ofrecer un revestimiento como vidrio de toda la ventana.

## Cómo quedó

Un solo endpoint con dos vistas:

```js
fetch('/pricing/api/pricing/vidrios/?tipo=vidrio')        // → selector de vidrio
fetch('/pricing/api/pricing/vidrios/?tipo=revestimiento') // → selector de sección ciega
```

La sección sigue guardando el discriminador `tipo: 'ciego'` pero referencia **`codigo`** en vez de
`id`:

```js
{ tipo: 'ciego', codigo: 'REV-CHAPA', id: null }
```

Mantener `'ciego'` era obligatorio: de él dependen el visor 3D y la detección de revestimiento del
PDF (FIX-023). Lo único que cambió es **de dónde se resuelve el material**, no la semántica.

## La columna en una tabla legacy

`Vidrio` es `managed = False` (tabla legacy `vidrios`), así que Django **no emite DDL** por un
`AddField`. La migración `pricing/0006_vidrio_tipo` separa estado y schema con
`SeparateDatabaseAndState`, y el `ALTER TABLE` se hace a mano:

```sql
ALTER TABLE vidrios ADD COLUMN tipo VARCHAR(20) NOT NULL DEFAULT 'vidrio'
```

El `DEFAULT` deja **todos los registros existentes como Vidrio** sin un UPDATE aparte. El ALTER es
idempotente y verifica que la tabla exista antes de tocarla (igual que `pricing/0002`, porque en
tests y bases nuevas las tablas legacy no están).

## Compatibilidad con presupuestos ya guardados

Las dos rutas que resuelven material —el calculador y el PDF— tienen **fallback**: si una sección
trae `id` y no `codigo`, se resuelve contra `MaterialCiego` como antes. Un presupuesto viejo sigue
cotizando e imprimiendo sin intervención. Por eso `MaterialCiego` **no se borró**: eliminarlo
exigiría otra migración y mataría el fallback.

Los snapshots viejos guardan `codigo` y `nombre` además del `id`, así que el PDF puede renderizar la
sección incluso sin resolver el registro.

## Decisiones técnicas

1. **Se reemplaza `MaterialCiego`, no conviven** (ADR-018). Si convivieran, el campo `tipo` sería
   redundante con el botón que ya existía.
2. **El precio sale de `Vidrio.precio`** ("Precio / m²"), la misma unidad que `MaterialCiego.precio_m2`,
   así que el cálculo por área no cambia.
3. **La columna Tipo del listado es texto plano, no badge.** La paleta de badges del design system es
   semántica de estado (amarillo = "hay que mirarlo"); un badge para una clasificación leería mal y
   competiría con el badge de Estado de la columna de al lado.
4. **`tipo_rev` (TIPO_REV) no se tocó.** Es una columna legacy de la misma tabla, declarada en el
   modelo y **sin uso en ninguna parte del código**. Podría ser el equivalente viejo de esta
   clasificación; conviene revisar si tiene datos antes de que queden dos clasificaciones.

## Archivos modificados

- `akuna_calc/pricing/models.py` — campo `tipo` + `TIPO_CHOICES`
- `akuna_calc/pricing/migrations/0006_vidrio_tipo.py` — **nuevo**
- `akuna_calc/pricing/forms.py` — `VidrioCreateForm` y `VidrioEditForm`
- `akuna_calc/pricing/catalog_views.py` — `VidriosListView` acepta `?tipo=` y expone el campo
- `akuna_calc/pricing/config_views.py` — orden por `tipo` en el listado
- `akuna_calc/pricing/services/calculator.py` — rama ciega por `codigo` + fallback
- `akuna_calc/pricing/templates/pricing/config/vidrios.html` — columna Tipo
- `akuna_calc/pricing/templates/pricing/config/vidrio_form.html` — selector
- `akuna_calc/presupuestos/pdf_descriptions.py` — resolución por código + fallback
- `akuna_calc/presupuestos/templates/presupuestos/detalle.html` — cotizador React
- Tests: `pricing/tests.py`, `presupuestos/tests.py`

## Validación

11 tests nuevos: 4 del modelo y los forms, 4 del calculador (revestimiento por código · fallback por
`id` · el código gana sobre el `id` viejo · inexistente falla), 3 de la API (filtra · sin tipo no
filtra · expone `tipo`), más 2 del PDF. Suite completa: 340 tests contra 323 del baseline, sin
regresiones.

## Pendiente

**Cargar los revestimientos** en `/pricing/config/vidrios/` con Tipo = Revestimiento. Hasta que
exista al menos uno, el botón "Ciego (chapa/panel)" muestra lista vacía — igual que antes del cambio.
