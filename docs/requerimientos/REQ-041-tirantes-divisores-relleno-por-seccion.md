# REQ-041 — Tirantes divisores con relleno por sección en el cotizador

- **Estado:** Implementado
- **Fecha:** 2026-07-27
- **Derivó en:** [FEAT-031](../features/FEAT-031-tirantes-divisores-relleno-por-seccion.md)

## Contexto

El cotizador de `/presupuestos/` (aluminio) calcula el precio de una abertura contra `pricing.services.calculator.calcular_precio()`. Hoy ese motor considera **un único vidrio para toda la abertura**:

```
area_m2 = ancho × alto / 1.000.000
precio_vidrio = area_m2 × vidrio.precio × cantidad_hojas
```

No existe forma de decir "esta abertura se divide en varias secciones y cada una lleva un material distinto". En la fábrica es habitual una puerta o paño dividido por un **tirante** (travesaño horizontal) a cierta altura, con **vidrio arriba y chapa abajo**, y puede tener 2, 3 o 4 tirantes.

**Lo que ya existe y no alcanza:**
- `VidrioRepartido` / `Cruce` / `DespiecePerfilesVidrioRepartido` (tablas legacy en `pricing/models.py`) modelan el corte y el peso de los perfiles de un vidrio repartido, **pero no asignan materiales distintos por paño**.
- El único material con precio por m² es `Vidrio`. **No hay catálogo de chapa / panel / tablero ciego.**
- `OrdenFabricacion` ya tiene `travesano_divisor` y `altura_travesano`, pero son texto libre en la planilla (no calculan nada).
- El visor 3D (`static/js/viewer3d.js`) ya sabe dibujar travesaños y un panel ciego inferior.

**Decisiones de alcance confirmadas con el usuario (discovery):**
1. **Vive en el cotizador de presupuestos** (afecta el precio del ítem). La orden de fabricación queda fuera de este REQ.
2. **Materiales de relleno:** vidrio del catálogo actual **+ un catálogo nuevo de materiales ciegos** (chapa / panel / tablero) con precio por m². → requiere migración.
3. **Divisiones solo horizontales** (bandas de arriba hacia abajo). La grilla (divisiones verticales) queda para una v2.
4. **El perfil del tirante suma costo** (peso × precio_kg, como cualquier otro perfil).

## User Story

```
Como vendedor / proyectista
quiero dividir una abertura con uno o varios tirantes horizontales a alturas configurables
y asignar un material de relleno distinto a cada sección resultante
para cotizar correctamente aberturas mixtas (ej. vidrio arriba, chapa abajo),
calculando el área y el precio de cada paño por separado.
```

## Criterios de aceptación

- [ ] En el cotizador de un ítem de aluminio se puede **activar "dividir con tirantes"** (opt-in) e indicar la altura de uno o más tirantes; las **secciones se derivan automáticamente** (N tirantes → N+1 secciones horizontales).
- [ ] Cada sección muestra su **área calculada** automáticamente (ancho de la abertura × alto de la sección) y permite elegir el **material de relleno**: un vidrio del catálogo actual **o** un material ciego (chapa / panel) del catálogo nuevo.
- [ ] Existe un **ABM del catálogo de materiales ciegos** (código, nombre, precio por m², activo) dentro de la configuración de `pricing`, respetando los permisos existentes del módulo.
- [ ] El precio del ítem se calcula como la suma de: **relleno de cada sección** (área_sección × precio_m² del material) + **perfil(es) del/los tirante(s)** (peso × precio_kg) + el resto (marco, hoja, accesorios, tratamiento, mano de obra, opcionales) **igual que hoy**.
- [ ] **Validación:** las alturas de los tirantes son crecientes, mayores a 0 y menores al alto total; la suma de las secciones equivale al alto de la abertura.
- [ ] El **desglose** (`resultado_json`) guarda la estructura de secciones (alto, área, material, precio unitario y total) y del/los tirante(s), de modo que el ítem se pueda reconstruir y mostrar en pantalla y PDF.
- [ ] El **visor 3D** refleja los tirantes y distingue visualmente el relleno de cada banda (vidrio vs. ciego).
- [ ] Cotizar **sin tirantes** mantiene exactamente el comportamiento actual; los ítems y presupuestos existentes no se rompen.
- [ ] **Tests:** cálculo con 1, 2 y 3 tirantes; validación de alturas inválidas; ABM del material ciego; y no-regresión del cálculo sin tirantes.

## Alcance

**Incluye:** UI dinámica de tirantes en el modal del cotizador (React por Babel, sin build), extensión del motor de cálculo `pricing` para relleno por sección + costo del perfil del tirante, catálogo nuevo de materiales ciegos con su ABM y migración, persistencia en `resultado_json`, reflejo en el visor 3D y en el PDF del presupuesto.

**Fuera de alcance (posible v2):**
- Divisiones **verticales** / grilla de cuadrados.
- Bajar los tirantes a la **orden de fabricación** como dato estructurado (hoy quedan como texto).
- Tirantes en presupuestos **PVC** (este REQ es solo aluminio; PVC usa precio manual).

## Riesgos / puntos abiertos para el Arquitecto

- **Interacción con `cantidad_hojas`:** hoy el vidrio se multiplica por `marco.producto.cantidad_hojas`. Hay que definir cómo se combina eso con secciones por tirante (¿el tirante aplica al paño fijo / puerta de 1 hoja, o también a correderas multi-hoja?).
- **Qué perfil usa el tirante:** ¿se toma de un despiece existente, se elige en el ABM, o se selecciona al cotizar? Definirlo en Paso 2.
- **Motor de fórmulas:** el del cotizador (`formula_parser.py`) solo soporta `+ - * / ( )`. El cálculo de área por sección es aritmético simple, así que no debería requerir cambiar el parser.
- **Migración del catálogo de materiales ciegos:** verificar aplicación limpia en Docker/Railway antes de confiar (ver historial de migraciones divergentes).

## Complejidad estimada

**Grande** — toca el motor de cálculo (`pricing`), agrega modelo + migración + ABM (materiales ciegos), UI dinámica en el modal React, el visor 3D y el PDF, con su batería de tests y no-regresión.

## Relación con el backlog

Nueva user story **US-041**. Se apoya sobre el módulo de Presupuestos (REQ-006 / FEAT-005), el cotizador de `pricing` y el visor 3D (REQ-038 / FEAT-030). No reemplaza ningún ítem existente del backlog.
