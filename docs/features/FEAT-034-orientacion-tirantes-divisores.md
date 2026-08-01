# FEAT-034 — Orientación de los tirantes divisores (vertical u horizontal)

- **Estado:** Implementado
- **Fecha:** 2026-08-01
- **Requerimiento:** [REQ-044](../requerimientos/REQ-044-orientacion-tirantes-divisores.md)
- **ADR relacionado:** [ADR-016](../team/decisions.md) (puntos 3 y 10 — revisados en esta feature)
- **Antecedente:** [FEAT-031](./FEAT-031-tirantes-divisores-relleno-por-seccion.md), que dejó las divisiones verticales explícitamente fuera de alcance.

## Descripción funcional

Al activar **"Dividir con tirantes"** en el cotizador de un ítem de aluminio (`/presupuestos/<pk>/`), el vendedor ahora elige la **orientación**:

- **Horizontal** (por defecto): la abertura se divide en **bandas**. Se carga el **alto** de cada sección de arriba hacia abajo y la suma debe dar el alto de la abertura. Cada tirante mide el **ancho**. Es el comportamiento previo, sin cambios.
- **Vertical**: la abertura se divide en **columnas**. Se carga el **ancho** de cada sección de izquierda a derecha y la suma debe dar el ancho de la abertura. Cada tirante mide el **alto**.

La orientación no es sólo un cambio de dibujo: define el **área de cada sección** (`ancho_abertura × alto_sección` u `ancho_sección × alto_abertura`) y la **longitud del perfil del tirante**, así que impacta directamente en el precio. El visor 3D dibuja columnas y barras verticales cuando corresponde, y la narrativa del PDF y la nota de la orden de fabricación indican el sentido de la división.

Al girar la orientación, las secciones se **reparten automáticamente** sobre la dimensión nueva conservando los materiales ya elegidos (el sobrante va a la última para que la suma cierre exacta, que es lo que exige el backend).

## Criterios de aceptación (cumplidos)

- [x] Selector Horizontal (default) / Vertical al activar tirantes.
- [x] Horizontal mantiene el comportamiento actual; vertical reparte el ancho.
- [x] Textos de ayuda, placeholder, unidad y validación en vivo hablan del eje correcto.
- [x] Al cambiar la orientación las secciones se reinicializan sobre la dimensión nueva.
- [x] Área por sección y longitud del tirante según el eje; las secciones siguen sumando el área de la abertura en ambas orientaciones.
- [x] Validación (suma == dimensión, medidas > 0) en cliente y en servidor.
- [x] El visor 3D dibuja columnas + barras verticales; los ciegos se distinguen del vidrio en ambos ejes.
- [x] La narrativa del PDF indica la orientación ("dividida por 2 tirantes verticales en …").
- [x] La orientación se guarda en el snapshot y se reconstruye al editar el ítem.
- [x] Ítems guardados antes de esta feature: mismo precio y mismo dibujo.
- [x] Tests de cálculo vertical, validación por eje y no-regresión del caso horizontal.

## Arquitectura

**Sin cambios de base de datos** — no se tocó ningún model, no hay migración. La configuración de tirantes sigue viajando en JSON (`ItemPresupuesto.resultado_json` y `snapshot_item`).

**Contrato del payload** (extendido de forma aditiva sobre FEAT-031):
```jsonc
tirantes: {
  activo: true,
  orientacion: "horizontal" | "vertical",   // NUEVO — ausente = horizontal
  perfil_codigo: "T1",                       // opcional
  secciones: [                               // orden arriba→abajo u izq→der
    { medida_mm: 600, material: { tipo: "vidrio", codigo: "F6" } },
    { medida_mm: 400, material: { tipo: "ciego",  id: 3 } }
  ]
}
```

`medida_mm` **reemplaza a `alto_mm`** en las secciones: es la medida sobre el eje que se divide, así que en vertical el nombre viejo mentía. La lectura es retrocompatible — ver "Decisiones técnicas".

**Motor de cálculo** (`pricing/services/calculator.py`): tres helpers públicos nuevos a nivel de módulo, que son la fuente única del contrato de datos y se importan también desde `presupuestos`:

| Helper | Qué hace |
|---|---|
| `medida_seccion(seccion)` | medida de la sección, con fallback a `alto_mm` |
| `orientacion_tirantes(tirantes)` | `horizontal` \| `vertical`; sin dato → `horizontal` |
| `ejes_tirantes(orientacion, ancho, alto)` | `(medida que reparten las secciones, longitud de cada tirante)` — son ejes **opuestos** |

Y un método nuevo `PriceCalculator._cotizar_tirantes(...)` que concentra validación + relleno + perfil del tirante, con argumentos por palabra clave. Se extrajo del cuerpo de `calculate()` justamente para poder testear la elección de ejes: un ancho/alto cruzado ahí cotizaría mal sin que ningún test unitario lo notara.

`_calcular_secciones()` pasa a recibir ancho, alto y orientación, y emite en el desglose las medidas reales de cada sección (en vertical, `ancho_mm` es el de la columna). `_validar_secciones()` y los mensajes de error hablan de "ancho" o "alto" según el caso. `_calcular_tirantes_perfil()` recibe `longitud_mm` en vez de `ancho_mm`.

**Serializer** (`pricing/serializers.py`): `orientacion` como `ChoiceField` (rechaza valores inventados), `medida_mm` y `alto_mm` ambos opcionales con normalización a `medida_mm`, y la validación cruzada compara la suma contra el ancho o el alto según la orientación.

**Frontend** (`presupuestos/templates/presupuestos/detalle.html`): `TirantesEditor` recibe el prop `ancho`, muestra un toggle Horizontal/Vertical con el patrón visual de los toggles existentes, deriva todos los textos del eje activo y reparte las medidas al girar. La reconstrucción al editar lee `orientacion` y `medida_mm` con fallback al formato viejo.

**Visor 3D** (`static/js/viewer3d.js`): param nuevo `tirantes_orientacion`; `addSecciones()` recorre el eje X cuando es vertical (columnas con el alto completo y barras divisorias verticales) y mantiene intacta la rama horizontal.

## Archivos involucrados

**Nuevos:** ninguno (además de esta documentación).

**Modificados:**
- `akuna_calc/pricing/serializers.py` — `orientacion`, `medida_mm`, validación por eje.
- `akuna_calc/pricing/services/calculator.py` — helpers de contrato, `_cotizar_tirantes`, cálculo por eje.
- `akuna_calc/presupuestos/pdf_descriptions.py` — snapshot normalizado + narrativa con orientación.
- `akuna_calc/presupuestos/views.py` — nota de la orden de fabricación con el sentido de la división.
- `akuna_calc/presupuestos/templates/presupuestos/detalle.html` — toggle, textos dinámicos, reparto, reconstrucción, params 3D.
- `akuna_calc/static/js/viewer3d.js` — dibujo de columnas y barras verticales.
- `akuna_calc/pricing/tests.py`, `akuna_calc/presupuestos/tests.py` — tests.

## Decisiones técnicas

1. **`medida_mm` con fallback a `alto_mm`, en vez de reinterpretar `alto_mm`.** Los datos de tirantes quedan guardados para siempre en `resultado_json` / `snapshot_item` y se muestran al taller en la orden de fabricación; un campo llamado `alto_mm` que en realidad contiene un ancho es deuda permanente. El costo es un helper de lectura de tres líneas. Ver ADR-016 punto 10.
2. **La orientación afecta el precio, no sólo el dibujo.** Se descartó implementarla como una preferencia visual: el área de cada sección y la longitud del tirante dependen del eje, así que un 3D en columnas con un precio calculado en bandas daría presupuestos mal cotizados.
3. **Un solo lugar decide los ejes** (`ejes_tirantes` + `_cotizar_tirantes`, con kwargs): es el punto donde un error silencioso costaría plata.
4. **Multi-hoja se comporta igual en los dos ejes**: secciones y tirantes se multiplican por `cantidad_hojas`, como ya hacía la v1 (ADR-016 punto 5).

## Tests

- `pricing`: `PriceCalculatorSeccionesVerticalesTest` (áreas de columna, cobertura del área total, misma área que horizontal, validación contra el ancho, longitud del tirante), `CotizarTirantesWiringTest` (los ejes elegidos por `calculate()`, incluido un ítem en formato viejo y el multiplicador por hojas), `TirantesHelpersTest` (contrato de datos), y 5 casos nuevos en `TirantesSerializerTest`.
- `presupuestos`: narrativa vertical, narrativa del formato viejo y normalización del snapshot (`medida_mm` + `orientacion`).
- **Resultado:** `pricing` + `presupuestos` = 249 corridos, 1 failure + 3 errors = **baseline preexistente** (tablas legacy `managed=False` que no existen en SQLite + un 302). Sin regresiones. `plantillas`/`productos`/`core`/`usuarios`: 46 OK.
- Verificaciones fuera de la suite Django: el bloque React compila con Babel, `viewer3d.js` pasa `node --check`, y se comprobó numéricamente que el reparto de medidas cierra exacto y que las columnas del visor cubren el hueco sin solapes.

## Verificación pendiente (manual)

- El **render 3D real** y el **cálculo de punta a punta** necesitan Docker/MySQL (en SQLite no existen las tablas legacy `marco`, `perfiles`, `vidrios`). Cotizar una abertura con tirantes verticales y confirmar el dibujo en columnas y el precio.
- Validar con un caso real de **corredera dividida verticalmente** que multiplicar las secciones por la cantidad de hojas sea el criterio comercial correcto también en este eje.

## Fuera de alcance

- **Grilla** (filas y columnas a la vez): sigue habiendo una sola orientación por abertura.
- Tirantes en presupuestos **PVC** (usan precio manual).
- **Rebaje por sección** (se cobra área nominal).
- ⚠️ **El visor sigue sin dibujar tirantes en corredizas y batientes de 2 hojas** (limitación heredada de FEAT-031). Con la orientación vertical se nota más, porque dividir en columnas es habitual justo en esos productos: el precio sale dividido pero el dibujo no.
