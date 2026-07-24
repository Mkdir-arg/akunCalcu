# FEAT-030 — Graficador 3D de aberturas en el cotizador de presupuestos

- **Estado:** Implementado
- **Fecha:** 2026-07-24
- **Requerimiento:** [REQ-038](../requerimientos/REQ-038-graficador-3d-aberturas-en-cotizador.md)
- **ADR relacionado:** [ADR-015](../team/decisions.md) (Three.js para 3D en el navegador)

## Descripción funcional

En el modal de "Agregar / editar ítem" de un presupuesto (`/presupuestos/<pk>/`), al **calcular el precio** de un ítem de aluminio se muestra, al lado del resultado, un **diseño 3D de la abertura** generado a partir de los parámetros ingresados. El vendedor puede rotarlo con el mouse para confirmar visualmente la configuración antes de guardarla.

El 3D **interpreta** los parámetros:
- **Tipología** (corrediza / batiente / oscilobatiente / proyectante / paño fijo / puerta batiente / puerta corrediza): se clasifica automáticamente desde `producto.descripcion` + `producto.cantidad_hojas`.
- **Ancho / alto**: a escala real.
- **Cantidad de hojas**: desde `producto.cantidad_hojas`.
- **Mosquitero / premarco**: según los opcionales elegidos (`tipo`).
- **Vidrio**: DVH / gris / bronce / esmerilado / incoloro, mapeado desde la descripción del vidrio.

## Criterios de aceptación (cumplidos)

- [x] Visor 3D al lado del resultado al calcular el ítem.
- [x] Interpreta tipología, ancho, alto, hojas, opcionales (mosquitero/premarco) y vidrio.
- [x] Clasifica la tipología automáticamente desde `producto.descripcion` + `cantidad_hojas`.
- [x] Default seguro (paño fijo) si no se puede clasificar con confianza.
- [x] Rota con el mouse y se actualiza al recalcular.
- [x] Lazy-load: Three.js se descarga solo al abrir/usar el modal.
- [x] Sin build: Three.js como módulo estático autocontenido invocado desde el modal React.
- [x] No rompe agregar/editar/eliminar ítems ni el cálculo (PVC, terciarizado, aluminio).

## Arquitectura

**Clasificador (backend, fuente única de verdad):** `pricing/tipologia.py::clasificar_tipologia(descripcion, cantidad_hojas)` — función pura, heurística por palabras clave con normalización de acentos/mayúsculas. Se expone al frontend enriqueciendo `ProductosListView` (`/pricing/api/pricing/productos/`) y `api_get_producto` con `cantidad_hojas` + `tipologia`.

**Visor (frontend):** `static/js/viewer3d.js` — módulo ESM autocontenido (Three.js + OrbitControls + RoomEnvironment + RoundedBoxGeometry vía import map desde jsdelivr). Expone `window.AkunViewer.mount(contenedor, params) / setParams / dispose`. Geometría paramétrica: marco y hojas como anillos extruidos (esquinas en inglete + junquillo), vidrio con `MeshPhysicalMaterial` (transmisión + DVH), mosquitero como malla, premarco, apertura animada según tipología, acotaciones. Auto-pausa cuando el contenedor tiene tamaño 0 (modal oculto).

**Integración (React por Babel, sin build):** import map + un `<script type="module">` que define `window.__loadAkunViewer` (carga perezosa del módulo). En `CotizadorModal`, un `useEffect` arma los `params` desde el estado (producto → tipología+hojas, opcionales → mosquitero/premarco, vidrio → tipo visual) y llama al viewer cuando hay `result`.

## Archivos involucrados

**Nuevos:**
- `akuna_calc/pricing/tipologia.py` — clasificador de tipología (función pura).
- `akuna_calc/static/js/viewer3d.js` — visor 3D como módulo ESM autocontenido.

**Modificados:**
- `akuna_calc/pricing/catalog_views.py` — `ProductosListView` agrega `cantidad_hojas` + `tipologia`.
- `akuna_calc/pricing/config_views.py` — `api_get_producto` agrega `cantidad_hojas` + `tipologia`.
- `akuna_calc/presupuestos/templates/presupuestos/detalle.html` — import map + loader lazy en `<head>`; `useRef` + `mapVidrio` + `useEffect` que monta el visor + canvas en la columna "Resultado".
- `akuna_calc/pricing/tests.py` — `ClasificarTipologiaTest` (12 tests).

**Sin migración** (no se tocó ningún model).

## Decisiones técnicas

1. **Three.js puro (no React Three Fiber).** El modal es React por Babel sin build; R3F exige bundler. Three.js se usa imperativamente desde un módulo estático → respeta el "sin build" actual. Ver ADR-015.
2. **Clasificador en el backend** (no en el JS) para tener una única fuente de verdad reutilizable a futuro (PDF, lista de ítems, override manual en el ABM).
3. **Conflicto JSX `{{ }}` vs Django:** los estilos inline de JSX (`style={{ }}`) rompen el parser de Django. Se usan clases Tailwind en su lugar. (Bug detectado y corregido en desarrollo; 11 tests de detalle volvieron a verde.)

## Fuera de alcance (fase 2)

- Persistir la tipología en `build_item_snapshot` + imagen PNG por ítem para la **lista de ítems** y el **PDF**.
- Color de perfil real y mano de apertura (izq/der) como dato (hoy default).
- `@login_required` en los catalog APIView de `pricing` (deuda preexistente, no introducida por esta feature).

## Tests

- `pricing.ClasificarTipologiaTest`: 12/12 OK (las 7 tipologías + defaults + normalización).
- `presupuestos`: 121/121 OK.
- `pricing` completo: sin regresiones (las 4 fallas restantes son baseline por tablas legacy ausentes en SQLite, idénticas al código sin los cambios).

## Verificación pendiente (manual)

El render real dentro del modal (Three.js desde CDN + producto real) requiere levantar Docker y abrir un presupuesto. El motor de render en sí ya fue validado con el prototipo (`scratchpad/visor-aberturas-3d.html`).
