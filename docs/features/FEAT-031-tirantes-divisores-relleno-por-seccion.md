# FEAT-031 — Tirantes divisores con relleno por sección en el cotizador

- **Estado:** Implementado
- **Fecha:** 2026-07-27
- **Requerimiento:** [REQ-041](../requerimientos/REQ-041-tirantes-divisores-relleno-por-seccion.md)
- **ADR relacionado:** [ADR-016](../team/decisions.md) (tirantes: relleno por sección + material ciego)

## Descripción funcional

En el cotizador de un ítem de aluminio (`/presupuestos/<pk>/`), el vendedor puede activar **"Dividir con tirantes"** y cargar el **alto de cada sección** (de arriba hacia abajo). N secciones generan N-1 tirantes horizontales. A cada sección se le asigna un **material de relleno propio**: un **vidrio** del catálogo o un **material ciego** (chapa / panel / tablero) del catálogo nuevo. El sistema calcula el **área de cada sección** (ancho de la abertura × alto de la sección) y su precio (`área × precio/m²`), y cada tirante suma el costo de su perfil (`peso × precio_kg`). El caso típico: una puerta con **vidrio arriba y chapa abajo**.

El visor 3D refleja la división (barras divisorias + panel opaco en las secciones ciegas) y la descripción narrativa del PDF menciona la división ("… dividida por 1 tirante en Float 6mm y Chapa").

## Criterios de aceptación (cumplidos)

- [x] Activar tirantes es opt-in; N secciones → N-1 tirantes, con alturas configurables.
- [x] Cada sección calcula su área y elige material: vidrio del catálogo o material ciego.
- [x] ABM nuevo de materiales ciegos (código, nombre, precio/m², activo), staff-only.
- [x] Precio = Σ relleno de secciones + perfil(es) del tirante + resto (marco, hoja, accesorios, tratamiento, mano de obra, opcionales) igual que antes.
- [x] Validación: alturas > 0 y suma == alto de la abertura (cliente + serializer).
- [x] `resultado_json` guarda `desglose.secciones` y `snapshot_item.tirantes` (reconstrucción al editar + narrativa PDF).
- [x] El visor 3D refleja tirantes y distingue el relleno ciego del vidriado.
- [x] Cotizar sin tirantes mantiene el comportamiento actual; ítems viejos intactos.
- [x] Tests: 1/2/3 secciones, validación, ABM y no-regresión.

## Arquitectura

**Modelo de datos:** nuevo `MaterialCiego` en `pricing/models.py` — tabla **administrada por Django** (a diferencia de las legacy `managed=False`), con `codigo`, `nombre`, `precio_m2`, `activo`. Migración `pricing/0005_materialciego`. La estructura de tirantes/secciones **no** agrega columnas: viaja en `ItemPresupuesto.resultado_json` (`desglose.secciones`) y en el `snapshot_item` (`tirantes`).

**Contrato del payload** (dentro del `config` que ya se manda al cotizador):
```
tirantes: {
  activo: true,
  perfil_codigo: "<NRO_PERFIL>",           // opcional
  secciones: [                              // orden arriba→abajo; N secciones = N-1 tirantes
    { alto_mm: 600, material: { tipo: "vidrio", codigo: "F6" } },
    { alto_mm: 900, material: { tipo: "ciego",  id: 3 } }
  ]
}
```

**Motor de cálculo** (`pricing/services/calculator.py`): si `tirantes.activo` con ≥2 secciones, se reemplaza el bloque de vidrio único por `_calcular_secciones` (área × precio/m² por sección, vidrio o ciego → `desglose.secciones` + `total_secciones`) y `_calcular_tirantes_perfil` (N-1 tirantes de longitud = ancho, sumados a `perfiles_items` y a `peso_total_perfiles` **antes** del tratamiento). Sin tirantes → la rama de vidrio único queda **idéntica** (no-regresión). El `resumen` agrega `total_secciones`; `total_vidrios` se mantiene (0 cuando hay tirantes).

**Serializer** (`pricing/serializers.py`): `TirantesSerializer` anidado + validación cruzada en `PricingCalculateSerializer.validate` (suma de secciones == `alto_mm`; ≥2 secciones si activo).

**Frontend** (`presupuestos/templates/presupuestos/detalle.html`): componente React `TirantesEditor` (toggle + secciones dinámicas con alto + selector vidrio/ciego + perfil del tirante + validación en vivo de la suma). El `config.tirantes` viaja en el POST de cálculo y en un input oculto `tirantes_json` al guardar. Reconstrucción al editar desde `snapshot_item.tirantes`. El desglose (modal React y modal de ítems guardados) muestra la sección "Secciones". Catálogos nuevos que consume: `vidrios` (completo), `materiales-ciegos`, `perfiles`.

**Visor 3D** (`static/js/viewer3d.js`): nuevo param `tirantes: [{alto_mm, ciego}]` → dibuja barras divisorias entre secciones y un panel opaco en las secciones ciegas.

**ABM** (staff-only, patrón existente): `MaterialCiegoForm`, vistas en `config_views.py`, `MaterialesCiegosListView` en `catalog_views.py`, rutas en `urls.py`, templates `config/materiales_ciegos.html` + `material_ciego_form.html`, y el ítem "Materiales ciegos" en el menú de Fábrica (`usuarios/access_control.py`, código de permiso `fabrica.materiales_ciegos`).

## Archivos involucrados

**Nuevos:**
- `akuna_calc/pricing/migrations/0005_materialciego.py`
- `akuna_calc/pricing/templates/pricing/config/materiales_ciegos.html`
- `akuna_calc/pricing/templates/pricing/config/material_ciego_form.html`

**Modificados:**
- `akuna_calc/pricing/models.py` — modelo `MaterialCiego`.
- `akuna_calc/pricing/forms.py` — `MaterialCiegoForm`.
- `akuna_calc/pricing/config_views.py` — ABM materiales ciegos.
- `akuna_calc/pricing/catalog_views.py` — `MaterialesCiegosListView`.
- `akuna_calc/pricing/urls.py` — rutas ABM + `api/pricing/materiales-ciegos/`.
- `akuna_calc/pricing/serializers.py` — campo `tirantes` + validación.
- `akuna_calc/pricing/services/calculator.py` — relleno por sección + perfil del tirante.
- `akuna_calc/presupuestos/views.py` — parseo de `tirantes_json` en `_fields_item_desde_post`.
- `akuna_calc/presupuestos/pdf_descriptions.py` — `_serialize_tirantes` en el snapshot + cláusula narrativa.
- `akuna_calc/presupuestos/templates/presupuestos/detalle.html` — `TirantesEditor`, hidden input, guardar/editar, desglose, params 3D.
- `akuna_calc/static/js/viewer3d.js` — dibujo de secciones/tirantes.
- `akuna_calc/usuarios/access_control.py` — ítem de menú.
- `akuna_calc/pricing/tests.py`, `akuna_calc/presupuestos/tests.py` — tests.

## Decisiones técnicas

1. **`MaterialCiego` como tabla administrada por Django** (no legacy `managed=False`): es un catálogo nuevo del sistema, sin equivalente en la base histórica. Ver ADR-016.
2. **Área bruta + multi-hoja multiplica** (auditoría 2026-07-29): cada sección cobra `ancho_total × alto_sección` (m² de abertura, sin rebaje) **× `cantidad_hojas`** del producto; los tirantes también se multiplican por hojas. Antes no multiplicaban y subcobraba en correderas. Ver ADR-016 (puntos 4 y 5).
3. **El tirante se cotiza como perfil elegido al cotizar** (longitud = ancho), reutilizando la maquinaria de perfiles; si no se elige perfil, el tirante solo divide (sin costo propio).
4. **Persistencia sin migración en `presupuestos`**: tirantes/secciones van en `resultado_json` + `snapshot_item`, aditivo y compatible con ítems viejos.

## Auditoría del cálculo (2026-07-29)

Se auditó el cálculo de punta a punta contra la base real. **Verificado correcto:** áreas por sección (suman el área de la abertura), precio = área × precio/m² del material, sin doble cobro del vidrio (`total_vidrios = 0` con tirantes), el desglose cuadra exacto contra el subtotal en todos los casos, N secciones → N-1 tirantes con peso y precio correctos, el peso del tirante entra al tratamiento, y el margen se aplica sobre el subtotal con secciones incluidas.

**Cuatro problemas encontrados y corregidos:**

| # | Problema | Impacto medido | Fix |
|---|---|---|---|
| 1 | La validación `suma secciones == alto` vivía sólo en el serializer del API y en el JS; el **guardado** del ítem no validaba | secciones 1200+400 con alto 2000 → cobraba 1,44 m² en vez de 1,8 m² ($23.760 vs $29.160) y quedaba guardado | `_validar_secciones` en el calculador (choke point de ambos caminos) |
| 2 | Material inexistente o dado de baja: la sección se **salteaba en silencio** | vidrio inexistente → $20.520; material ciego inactivo → $18.360 (−37 %) en vez de $29.160 | `PricingError` explícito por sección |
| 3 | `cantidad_hojas` no multiplicaba las secciones (el vidrio único sí) | producto de 2 hojas → secciones $19.440 vs vidrio único $28.800 | secciones y tirantes × `cantidad_hojas` |
| 4 | El cotizador standalone (`pricing/cotizador.html`) no mostraba el bloque "Secciones"; y el snapshot anunciaba un **vidrio que no se cotizó** en PDF y orden de fabricación | desglose visible que no cerraba; orden con vidrio equivocado | bloque "Secciones" agregado; `snapshot['vidrio'] = None` con tirantes y los materiales de las secciones van al casillero de vidrio + nota de la orden |

## Fuera de alcance (posible v2)

- Divisiones **verticales** / grilla de cuadrados (solo horizontales por ahora).
- Bajar los tirantes a la **orden de fabricación** como dato estructurado.
- Tirantes en presupuestos **PVC** (solo aluminio; PVC usa precio manual).
- **Rebaje por sección** (v1 usa área nominal `ancho × alto_seccion`).

## Tests

- `pricing`: `TirantesSerializerTest`, `PriceCalculatorSeccionesTest`, `PriceCalculatorTirantesPerfilTest`, `MaterialCiegoModelTest`, `MaterialCiegoFormTest`, `MaterialesCiegosListViewTest`.
- `presupuestos`: `TirantesNarrativaTest`, `SerializeTirantesTest`.
- 16 tests nuevos OK. Suite `pricing` + `presupuestos`: 203 corridos, 1 failure + 3 errors = baseline preexistente (tablas legacy ausentes en SQLite). Sin regresiones.

## Verificación pendiente (manual / deploy)

- El cálculo aluminio de punta a punta y el render 3D real requieren Docker/MySQL (las tablas legacy `marco`, `vidrios`, `perfiles` no existen en SQLite).
- Correr la migración `pricing/0005_materialciego` en Docker/Railway.
- Cargar algunos materiales ciegos (chapa/panel) en el ABM antes de usar la feature.
