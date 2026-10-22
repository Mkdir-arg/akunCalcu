# REQ-062 — Estructuras: varias aberturas ubicadas sobre una pared, cotizadas como un conjunto

- **Estado:** Implementado (Etapa 1; la Etapa 2 sigue pendiente)
- **Derivó en:** [FEAT-045](../features/FEAT-045-estructuras.md)
- **Fecha:** 2026-10-22
- **Complejidad:** Grande (dos etapas, cada una publicable sola)
- **Origen:** pedido del cliente "necesito poder armar las estructuras" ([plan RF Akun](../team/plan-rf-akun-2026-10.md), sección "Después")
- **Retoma:** "Combinaciones (fijo + abrir, fijo + corrediza)", que quedó fuera de alcance en [REQ-047](./REQ-047-aperturas-configurables.md)
- **Apps afectadas:** `pricing`, `presupuestos`, `usuarios` (registro de ruta), `static/js`

## User Story

Como **vendedor que cotiza aberturas** quiero **dibujar una pared y ubicar sobre ella varias
aberturas (puertas, ventanas, paños fijos), cada una con su producto y sus medidas**, para
**cotizar el conjunto como una sola estructura, con su plano y su precio total**, y que el cliente
vea en el PDF cómo queda la pared terminada.

## Contexto

Hoy no existe nada parecido:

- El presupuesto es una lista plana de ítems, sin agrupador.
- El cotizador calcula **una abertura por llamada**. Un paño fijo es un marco sin hoja.
- Los dibujos (plano con cotas y símbolos de apertura) son de una sola abertura.

Lo único que hay con ese nombre es un campo de texto libre en la Orden de Fabricación,
`OrdenFabricacion.estructura`, que nadie completa automáticamente.

## Decisiones tomadas (usuario, 2026-10-22)

| Pregunta | Decisión | Motivo |
|---|---|---|
| ¿Cómo se arma? | **Ubicación libre sobre la pared.** La pared tiene ancho × alto, es solo referencia y no se cobra. Cada abertura tiene posición (desde el borde izquierdo y desde el piso) y medidas, y puede ir separada por pared o pegada a otra | Es un plano de cómo queda la pared |
| ¿Qué se cobra en las juntas? | **Perfil de unión opcional.** Cada junta se cobra igual que un tirante: largo × peso × precio/kg, más tratamiento y margen. Sin perfil, se cobra la suma pura | Donde dos aberturas se tocan se usa un perfil de acople |
| ¿Qué recibe fábrica? | **Una orden de fabricación por abertura**, con el campo "Estructura" completado | Cada abertura puede ser de distinto producto y vidrio |
| ¿Colocación en renovación? | **Una vez por unidad de estructura** | La estructura se coloca como una pieza |
| ¿Línea, color y margen? | **Comunes a toda la estructura.** Cada abertura elige su producto, marco, hoja, vidrio, apertura y opcionales | Simplifica la carga y es coherente con el perfil de unión, que pertenece a una línea. Se puede revisar si hace falta mezclar líneas |

## Criterios de Aceptación

- [x] En un presupuesto de aluminio no bloqueado hay un botón **"Agregar estructura"** junto a "Agregar".
- [x] El editor define la pared (ancho y alto en mm), los datos comunes y el perfil de unión opcional.
- [x] Se pueden agregar aberturas. Cada una se configura con la misma cascada del cotizador actual: producto → marco → hoja → vidrio → apertura → opcionales.
- [x] Cada abertura se **arrastra sobre la pared**:
  - con imán a los bordes de la pared y de las otras aberturas, y grilla de 10 mm;
  - se ajusta con medidas exactas en mm: ancho, alto, desde la izquierda y desde el piso.
- [x] No se puede guardar con aberturas superpuestas o fuera de la pared, y el sistema explica el motivo.
- [x] Las juntas se detectan solas. Si hay perfil de unión, se cobran por largo.
- [x] El precio es la suma de las aberturas más las juntas, y **siempre se recalcula en el servidor**: el precio que manda el navegador no se usa.
- [x] La estructura es **un renglón** del presupuesto, con cantidad, miniatura, ver desglose, editar, eliminar y reordenar.
- [x] Al editar una estructura, el editor se abre con todo restaurado.
- [x] En renovación, el recargo de colocación se suma una vez por unidad de estructura.
- [x] En el PDF:
  - hay un renglón con el detalle de las aberturas;
  - el anexo de planos incluye el plano de la pared.
- [x] Al confirmar se crea una orden de fabricación por abertura (M1..Mn), con números consecutivos y "Estructura" completado.
- [x] Los ítems y presupuestos existentes no cambian.

## Mockup del editor

Es un modal grande, con el mismo patrón que el modal de ítem actual.

```
┌─ Nueva estructura ─────────────────────────────────────────────────────────────────── ✕ ┐
│ Nombre [Frente living   ]  Línea [Módena ▾]  Color [Blanco ▾]  Margen [30]%                │
│ Pared: ancho [5000] mm  alto [2600] mm          Perfil de unión [Ninguno ▾]                 │
├──────────────────────────────────────────────────────────────┬─────────────────────────────┤
│ [+ Agregar abertura]                          [Cotas: sí/no] │ Abertura seleccionada: M2   │
│ ┌──────────────────────────────────────────────────────────┐ │ Corrediza Módena 2 hojas    │
│ │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│ │ vidrio 4 mm float           │
│ │░┌──────┐░░░░░░░░░┏━━━━━━━━━━━━┓┌──────┐░░░░░░░░░░░░░░░░░░│ │ [Configurar abertura]       │
│ │░│  M1  │░░░░░░░░░┃ M2  ⇄    ⇄ ┃┃  M3  │░░░░░░░░░░░░░░░░░░│ │                             │
│ │░│ ╲    │░░░░░░░░░┃            ┃┃      │░░░░░░░░░░░░░░░░░░│ │ Ancho [1500]  Alto [1100]   │
│ │░│  ╲   │░░░░░░░░░┗━━━━━━━━━━━━┛└──────┘░░░░░░░░░░░░░░░░░░│ │ Desde izq     [1800]        │
│ │░│  ╱   │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│ │ Desde el piso [900]         │
│ │░│ ╱    │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│ │ Precio  $ 412.300           │
│ │░└──────┘░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│ │ [Eliminar]                  │
│ └──────────────────────── NPT ─────────────────────────────┘ │                             │
│  ├600┤──900──├───900───┤────1500────┤─700─┤──────1100──────┤ │                             │
├──────────────────────────────────────────────────────────────┴─────────────────────────────┤
│ M1 Puerta 900×2050 $580.000 · M2 Corrediza 1500×1100 $412.300 · M3 Paño fijo 700×1100 $160.200 │
│ Juntas: M2 | M3 vertical 1100 mm (sin perfil de unión)                                       │
│ Cantidad [1]          TOTAL ESTRUCTURA  $ 1.152.500        [Calcular]  [Guardar]             │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

- **"Configurar abertura"** abre el cotizador actual en *modo módulo*, encima del editor:
  - la línea, el color y el margen vienen bloqueados desde la estructura;
  - las medidas se ven, pero no se pueden editar;
  - "Aplicar al módulo" devuelve la configuración al editor.
- **Etiquetas.** Las aberturas se etiquetan **M1..Mn** por posición: de izquierda a derecha, y luego de abajo hacia arriba.
- **Precio.** Se recalcula en el servidor 700 ms después del último cambio, o al soltar un arrastre. Si el precio está desactualizado, no se puede guardar.

**Renglón del presupuesto y del PDF.** El ancho y el alto del renglón son los del **conjunto** (la
envolvente de las aberturas), no los de la pared.

```
 #3  [miniatura]  Frente living — Estructura de 3 aberturas · conjunto 3700×2050     1   $ 1.152.500
                   Línea Módena · Blanco · M1 Puerta 1 hoja 900×2050 · M2 Corrediza 1500×1100,
                   antepecho 900 · M3 Paño fijo 700×1100 · Sin perfil de unión
```

## Diseño técnico

### A) Datos: sin tabla nueva y sin migración

La estructura es un `ItemPresupuesto` más, con `resultado_json['tipo'] = 'estructura'`. El
mecanismo ya existe para `terciarizado` y `pvc_simple`.

```
resultado_json = {
  tipo: 'estructura', version: 1,
  precio_unitario_base, recargo_renovacion_*_aplicado,       ← el recargo actual sigue andando
  precio_total, subtotal, margen,                             ← sumas: el desglose sigue andando
  snapshot_item: { titulo, resumen_tecnico, linea, extrusora, tratamiento, ancho/alto del conjunto },
  estructura: {
    pared {ancho, alto}, comun {extrusora_id, linea_id, tratamiento_id, margen_porcentaje},
    perfil_union {codigo, descripcion} | null, envolvente {x, y, ancho, alto},
    union {peso_kg, precio_total},
    modulos: [ {etiqueta, x, y, ancho, alto, config, resultado, snapshot_item} ],
    juntas:  [ {a, b, orientacion, largo_mm, precio_total} ]
  }
}
ItemPresupuesto.ancho_mm / alto_mm = envolvente del conjunto
```

¿Por qué JSON y no un modelo relacional?
- Las cotizaciones ya se guardan como foto (snapshot), y editar reemplaza la estructura entera.
- No hace falta consultar por módulo.
- `version` deja margen para cambiar el esquema más adelante.

### B) Servicio de precio: `pricing/services/estructura.py` (nuevo)

- **`normalizar_estructura(data)`**
  - Pasa los valores a enteros y aplica una **lista blanca** a la config de cada módulo. Cualquier precio del cliente se descarta.
  - Agrega a cada módulo sus medidas, más el `tratamiento_id` y el `margen_porcentaje` comunes.
- **`validar_geometria`** rechaza:
  - módulos fuera de la pared o superpuestos;
  - un lado menor a 200 mm, o más de 12 módulos;
  - un módulo sin marco, de otra línea, terciarizado o con tipología `no_dibujo`.
- **`detectar_juntas`**
  - Hay junta cuando dos bordes coinciden y se solapan en un largo mayor a 0. Tocarse solo en una esquina no cuenta.
  - La tolerancia es 0, porque el imán del editor deja los bordes alineados.
- **`calcular_estructura`**
  - Llama a `calcular_precio(config)` (`pricing/services/calculator.py:1206`) una vez por módulo. Si un módulo falla, el error dice "Módulo M2: …".
  - Unión: `(Σ largo × peso_metro × precio_kg + peso × tratamiento.precio_kg) × (1 + margen%)`.
  - Reutiliza `_calcular_tirantes_perfil` (`calculator.py:1172`) con un kwarg `segmento` y un wrapper público `precio_perfil_por_largo(...)`. Lo que devuelve hoy esa función no cambia.
- **Endpoint de vista previa: `EstructuraCalculateView`** (`pricing/views.py`)
  - Ruta `api/pricing/estructura/calculate/`, nombre `pricing-estructura-calculate`.
  - Se registra en `usuarios/access_control.py` con `cotizador.view` y `presupuestos.view`.

### C) Guardado: mismas URLs de agregar y editar ítem

- **`fields_item_estructura(...)`** en un archivo nuevo, `presupuestos/estructuras.py`:
  - llama al servicio;
  - arma `build_item_snapshot` (`pdf_descriptions.py:405`) por módulo;
  - aplica el recargo de renovación igual que el camino de aluminio (`views.py` ~l.390-399).
- **`_fields_item_desde_post`** (`views.py:304`):
  - si llega `estructura_json`, desvía a `fields_item_estructura`;
  - en un presupuesto PVC, da error;
  - el JSON se valida con un `forms.Form` que tiene un `forms.JSONField`.
- **`editar_item`**: si el ítem es una estructura y el POST no trae `estructura_json`, da error.
- Se reutilizan `presupuestos-item-agregar` y `presupuestos-item-editar`, con sus bloqueos y permisos.

### D) Editor: parcial nuevo `presupuestos/templates/presupuestos/_estructura_editor.html`

- **Contenido del parcial:**
  - el modal `#modal-estructura`;
  - un form oculto con csrf, `descripcion`, `cantidad` y `estructura_json`;
  - la configuración, vía `json_script`;
  - `<script type="text/babel">` dentro de `{% verbatim %}`, para evitar el choque de `{{` con JSX.
- **Inclusión.** `detalle.html` lo incluye solo si el presupuesto es de aluminio y no está bloqueado.
- **Reutiliza el cotizador, no lo duplica:**
  - el script del cotizador expone `window.AkunUI = {Sel, Block, configDesdeSnapshot}`, extraído del mapeo de `detalle.html` ~l.1792-1823;
  - y expone `window.__cotizadorModulo({...})`, que abre el mismo `CotizadorModal` en modo módulo, aislado detrás de un estado `modulo`.
- **Modales encimados:**
  - `#modal-item` pasa a `z-[60]` cuando se abre encima del editor;
  - Escape cierra solo el modal de más arriba.
- **Arrastre:**
  - pointer events con `getScreenCTM().inverse()`;
  - grilla de 10 mm e imán a unos 12 px de los bordes de la pared y de las otras aberturas;
  - si al soltar queda superpuesta, la abertura vuelve a su última posición válida;
  - mientras se arrastra se dibuja solo el contorno, y el dibujo completo al soltar.
- **Tirantes.** Si cambia el tamaño de una abertura con tirantes, sus secciones se reescalan en proporción (la última absorbe el redondeo) y se muestra un aviso.
- **Botón "Agregar estructura"** (`fa-object-group`): va junto a "Agregar item" (`detalle.html` ~l.95-106 y l.225) y en el estado vacío.
- **Eliminar una abertura** pide confirmación con SweetAlert2.

### E) Dibujo

- **Refactor mínimo de `static/js/elevacion.js`:**
  - se extrae `dibujarAbertura(params, {ox, oy, size, apertura, composicion, idPrefijo})` de `svgElevacion` (~l.119-160);
  - `svgElevacion` tiene que devolver **exactamente el mismo texto** que antes, y se verifica con `node akuna_calc/audit_cotas.mjs`;
  - `idPrefijo` evita que dos patrones de mosquitero de la misma medida choquen en el PDF.
- **Nuevo `static/js/estructura.js`:**
  - Funciones: `etiquetarModulos`, `detectarJuntas`, `validarEstructura`, `envolvente`, `svgEstructura(p, opts)` y el despachador `svgDibujo(p, opts)`.
  - Dibuja la pared rayada con su línea de piso (NPT) y encima cada abertura con `dibujarAbertura`.
  - Juntas: línea gruesa si hay perfil de unión, punteada si no.
  - Cotas: cadena horizontal abajo y cadena vertical a la derecha, más la medida de cada abertura.
  - `opts.pared: false` recorta el dibujo a la envolvente, para la miniatura.
- **Dónde se usa `svgDibujo`:**
  - en la miniatura (`detalle.html` ~l.38-52) y en el anexo del PDF (`pdf.html` ~l.691-707);
  - el cotizador suelto sigue usando `svgElevacion`;
  - hay que subir el `?v=` de los scripts.
- **Python.** `build_dibujo_estructura(...)` arma `{tipo:'estructura', pared, modulos[{x, y, ..., dibujo: build_dibujo_params(snap)}], juntas}`.
- ⚠️ **Trampa.** `pricing/tipologia.py:81` clasifica como `no_dibujo` toda descripción que contenga "estructura". Por eso:
  - la estructura **nunca** pasa por `build_dibujo_params`;
  - los snapshots de módulo se arman sin esa palabra.

### F) PDF, detalle y desglose

- **`build_pdf_item_context`** (`pdf_descriptions.py:597`) desvía si `tipo == 'estructura'` y arma:
  - el título;
  - un `resumen_tecnico` con todas las aberturas, reutilizando `describir_apertura`;
  - un `resumen_compacto` para la fila.
- **`pdf.html`.** En el anexo, la figura de la estructura ocupa todo el ancho (`grid-column: 1/-1`).
- **"Ver desglose"** (`verDetalleItem`, `detalle.html` ~l.1075) muestra una tabla de módulos y juntas, y cada módulo abre su propio desglose.

### G) Confirmación

- `_crear_orden_desde_item` (`views.py:606`) se generaliza a `_crear_orden(..., snapshot, ancho, alto, item_medida, estructura='')`.
- Una estructura genera **una orden por módulo**, cada una con:
  - el snapshot de ese módulo y sus medidas;
  - `cantidad = item.cantidad`;
  - `MedidaOrdenFabricacion.item = 'M2'`.
- ⚠️ **Numeración.** `_procesar_confirmacion` (`views.py` ~l.702-704) numera como `base + índice de ítem`, y eso pasa a un **contador corrido**. Si no se cambia, el número de orden (que es único) se repite y se revierte toda la confirmación.
- Ejemplo del campo `estructura`: *"Estructura «Frente living» (ítem 3, PRES-2026-045) — módulo M2 de 3. Pared 5000×2600; conjunto 3700×2050. M2 a 1800 mm del borde izq., 900 mm del piso. Módulos: M1 Puerta 900×2050 · M2 … Juntas: M2-M3 vertical 1100. Sin perfil de unión."*

### H) Recargo y edición

- **Recargo de renovación sin cambios de código.** `aplicar_recargo_renovacion` y `actualizar_items_por_configuracion` (`models.py` l.381 y l.238) ya leen `precio_unitario_base` del primer nivel del JSON. Así, el recargo se aplica una vez por estructura y se multiplica por la cantidad.
- **Editar.** `editarItemBtn` (`detalle.html` ~l.911) desvía a `window.__estructuraEditar`, que restaura todo desde `resultado.estructura`.

## Etapas

| Etapa | Contenido | ¿Publicable sola? |
|---|---|---|
| **1. Cotizar, vender y fabricar** | Servicio, endpoint, guardado, edición y recargo. Editor con arrastre e imán, medidas en mm y modo módulo. `svgEstructura` con las cotas de la pared y de cada abertura. Miniatura, renglón y anexo del PDF, desglose. **Órdenes por módulo**: no se pueden postergar, porque confirmar sin ellas genera órdenes equivocadas | Sí |
| **2. Plano completo y comodidades** | Cotas encadenadas y antepechos, rayado de pared y NPT, flechas del teclado, duplicar abertura, aviso de separaciones menores a 5 mm | Sí |

## Análisis de impacto

- [x] **FK:** `OrdenFabricacion.item_presupuesto` ya admite N órdenes por ítem, y ningún código asume una relación 1:1.
- [x] **Vistas que cambian:** `_fields_item_desde_post`, `editar_item`, `_procesar_confirmacion` y `_crear_orden_desde_item`.
  - `detalle` y `pdf` cambian solo por contexto.
  - `reordenar_items` y el importador REHAU no cambian.
- [x] **Templates:**
  - cambian `detalle.html` y `pdf.html`, y se agrega el parcial nuevo;
  - `plantillas/orden_pdf.html` no se toca, porque el texto largo de "Estructura" ya se corta en renglones.
- [x] **Forms:** solo se agrega uno nuevo; `ItemPresupuestoForm` no se toca.
- [x] **URLs:** `pricing-estructura-calculate` no choca con ninguna existente.
- [x] **Datos existentes:** no hay migración, y los ítems sin `tipo` siguen exactamente igual.
- [x] **Campo obligatorio nuevo:** no hay.
- [x] **Permisos:**
  - el endpoint nuevo se registra en `access_control.py`;
  - el resto hereda los permisos actuales;
  - DRF cubre el CSRF.

## Riesgos

1. **Modo módulo dentro de `CotizadorModal`** (unas 1000 líneas). Queda aislado detrás del estado `modulo`, y hay que probar que el modal normal no cambie.
2. **Geometría duplicada en Python y JS.** Se mitiga con fixtures JSON compartidos entre los tests de ambos lados.
3. **Refactor de `elevacion.js`.** Se exige salida idéntica y `audit_cotas.mjs` en verde.
4. **Tiempo de la vista previa.** Cada vista previa hace N cálculos. Se limita a 12 módulos y a 700 ms de espera entre cambios.
5. **REQ-057** (aprobado, sin implementar) lee los ítems con `build_ficha_item` y tiene que contemplar `tipo == 'estructura'`. La nota ya quedó en ese requerimiento.

## Fuera de alcance

- 3D de la estructura (solo plano 2D).
- Presupuestos PVC (sus ítems son montos manuales en US$).
- Aberturas terciarizadas o complementos dentro de una estructura.
- Esquineros, estructuras en L y módulos rotados.
- Plantillas reutilizables de estructuras.
- Estructuras en el cotizador suelto.
- Croquis en el PDF de la orden de fabricación (ahí va solo texto).
- Cambiar el tamaño de una abertura arrastrando su borde.
- Convertir ítems existentes en estructura.
- Cobrar la pared o la obra.

## Tests

- **`pricing/tests.py`:**
  - juntas: vertical, horizontal, solape parcial, solo esquina y separadas;
  - validaciones: fuera de pared, solape, mínimos, máximo de módulos, otra línea y terciarizado;
  - el total sin perfil es la suma, y con perfil sigue la fórmula;
  - el error lleva el prefijo "Módulo M2:" y se ignora el precio del cliente;
  - el endpoint responde 200, 400 y 403;
  - los tests de tirantes siguen en verde.
- **`presupuestos/tests.py`:**
  - el alta guarda la medida del conjunto y el precio del servidor;
  - el recargo de renovación se aplica una vez por estructura y se multiplica por la cantidad;
  - un presupuesto PVC rechaza la estructura, y un JSON inválido no crea el ítem;
  - editar reemplaza la estructura;
  - el botón aparece solo en aluminio no bloqueado;
  - el contexto y el anexo del PDF;
  - **confirmar 1 ítem + 1 estructura de 3 módulos genera 4 órdenes consecutivas**, con `estructura`, `item='M2'` y la cantidad correcta.
- **JS:**
  - nuevo `akuna_calc/audit_estructura.mjs` (node), con fixtures compartidos;
  - el SVG no tiene NaN ni undefined, y los ids son únicos;
  - se vuelve a correr `audit_cotas.mjs`.
- **Navegador (local), de punta a punta:**
  - armar una pared con puerta + corrediza + paño fijo pegados;
  - arrastrar y comprobar el imán;
  - calcular, guardar, editar y cambiar a renovación;
  - imprimir el PDF;
  - confirmar y revisar las 4 órdenes en el pedido de fábrica.

## Hallazgo aparte (no entra en este REQ)

`usuarios/access_control.py` (~l.339-343) deja entrar a cualquier usuario logueado en las rutas no
registradas. Hoy quedan abiertas así `presupuestos-item-editar`, `presupuestos-items-reordenar`,
`presupuestos-observaciones` y `perfiles-list`. Conviene corregirlo con un `/fix` separado.
