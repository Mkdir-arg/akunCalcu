# REQ-063 — Circuito de pedidos de fábrica: estados, trabajo del taller y Orden de Fabricación mejorada

- **Estado:** En desarrollo (Paso 1 y Paso 2 aprobados 2026-10-29, con la condición de usar el diseño «Taller» — § 10.7; implementación esperando el merge de `development`)
- **Fecha:** 2026-10-29
- **Complejidad:** Grande (se entrega en 3 etapas)
- **Origen:** Pedido directo del usuario: "una vez que se confirme el presupuesto arranquemos con los pedidos a fábrica… planificá cómo llega un pedido, cómo pasa por los estados, qué hace el de fábrica, y mejorá el PDF manteniendo la estética".
- **Continúa:** [REQ-034](./REQ-034-confirmacion-presupuesto-genera-venta-y-pedido.md) (FEAT-019) y [REQ-035](./REQ-035-ordenes-de-fabricacion-en-pedidos.md) (FEAT-021/022)
- **Se cruza con:** [REQ-056](./REQ-056-pdf-medicion-y-base-pdf-comun.md) (base común de PDFs `core/pdf.py`) y [REQ-057](./REQ-057-pdf-colocacion.md) (colocación)
- **Apps afectadas:** `plantillas`, `presupuestos`, `comercial` (estado de la venta), `usuarios` (permisos)

## User Story

Como **responsable de fábrica** quiero **recibir cada presupuesto confirmado como un pedido que reviso,
libero al taller y sigo etapa por etapa hasta la entrega**, con una Orden de Fabricación que ya trae
todo lo que el cotizador sabe, para **que el taller no fabrique órdenes incompletas o desactualizadas
y ventas sepa en todo momento en qué está cada pedido**.

---

## 1. Qué hay hoy (diagnóstico)

**Funciona:**
- Confirmar el presupuesto crea, en una sola transacción, la Venta + el `PedidoFabrica` (`PF-0001`) + una `OrdenFabricacion` por ítem (una por módulo si es estructura).
- La orden llega precargada con cliente, tipo de abertura, línea, color, vidrio (con tirantes), medida, cantidad y fecha comprometida.
- Pantallas: listado de pedidos, detalle con órdenes, editar / agregar / borrar orden, PDF A4 por orden.

**Huecos de lógica:**

| # | Hueco | Consecuencia |
|---|---|---|
| H1 | `PedidoFabrica.estado` existe pero **ninguna pantalla lo cambia** | Todos los pedidos quedan en "Borrador" para siempre; no se sabe qué está en el taller |
| H2 | Las órdenes **no tienen estado** | El taller no puede marcar avance; ventas no sabe si algo está listo |
| H3 | Nadie "libera" el pedido al taller | Una orden incompleta (sin hojas, sin lado, sin medida verificada) puede imprimirse y fabricarse |
| H4 | Se puede **editar una orden ya impresa** sin rastro | El taller trabaja con un papel viejo y nadie se entera del cambio |
| H5 | Si el presupuesto confirmado pasa a **cancelado**, el pedido **sigue vivo** | Se fabrica algo que el cliente canceló |
| H6 | El bloque "Detalle" del PDF sale **casi todo en blanco**, aunque el cotizador ya sabe mosquitero, premarco, hoja, marco, cantidad de hojas, lado de apertura y travesaños | El taller recarga a mano datos que el sistema tiene |
| H7 | El croquis es una **cuadrícula vacía**, aunque el sistema ya dibuja el plano con cotas de cada abertura (FEAT-038) | Hay que dibujar a mano algo que ya existe |
| H8 | No hay **PDF del pedido completo** | Se imprime orden por orden |
| H9 | `_generar_numero_pedido_fabrica()` usa `count()+1`; `pedido_create` procesa el POST sin Form | Número duplicado si dos confirman a la vez (lo frena el `unique`, pero da error 500); viola convención |

---

## 2. Cómo llega un pedido (flujo propuesto)

```
VENTAS                          OFICINA TÉCNICA / RESPONSABLE         TALLER                         VENTAS / COLOCACIÓN
──────                          ──────────────────────────────        ──────                         ───────────────────
Confirmar presupuesto
  └─► Venta + Pedido PF-XXXX ─► [RECIBIDO]
       + N órdenes precargadas    revisa y completa cada orden
                                  (checklist de faltantes)
                                  "Liberar a fábrica" ───────────────► [EN FÁBRICA]
                                  (congela la orden: Rev. 1)            imprime / ve las órdenes
                                                                        avanza cada orden por etapa
                                                                        ─► [EN PRODUCCIÓN] (automático)
                                                                        última orden "Lista"
                                                                        ─► [TERMINADO] (automático) ──► aviso a ventas
                                                                                                        "Entregar" / "Colocado"
                                                                                                        ─► [ENTREGADO]
                                                                                                           (sincroniza Venta.estado)
```

En cualquier momento antes de ENTREGADO: **[CANCELADO]** (con motivo). Se dispara solo si el presupuesto pasa a cancelado.

---

## 3. Estados del pedido (cabecera)

| Estado | Quién lo pone | Cómo | Qué se puede hacer |
|---|---|---|---|
| **Recibido** | Sistema | Al confirmar el presupuesto | Editar órdenes libremente, agregar / borrar órdenes |
| **En fábrica** | Responsable (botón "Liberar a fábrica") | Solo si el checklist de faltantes está vacío | Órdenes congeladas (ver § 5); el taller las ve en su tablero |
| **En producción** | Sistema | Cuando alguna orden sale de "Por fabricar" | Igual que "En fábrica" |
| **Terminado** | Sistema | Cuando **todas** las órdenes están "Lista" | Avisar a ventas; habilita "Entregar" |
| **Entregado** | Ventas / responsable | Botón "Marcar entregado" o "Marcar colocado" | Solo lectura; pone `Venta.estado` = entregado / colocado |
| **Cancelado** | Responsable, o sistema si el presupuesto se cancela | Botón con motivo obligatorio | Solo lectura; las órdenes quedan "Anulada" |

**Regla clave:** "En producción" y "Terminado" **se calculan** a partir de las órdenes, nunca se eligen a mano. Así el estado del pedido no puede contradecir al de sus órdenes.

Mapeo con los estados actuales (migración de datos): `BORRADOR → Recibido`, `EN_PROCESO → En producción`, `COMPLETADO → Entregado`, `CANCELADO → Cancelado`.

---

## 4. Lo que hace el de fábrica (estados de cada orden)

Propuesta inicial, **a validar con el usuario (pregunta P1)**:

```
Por fabricar ─► Corte ─► Armado ─► Vidriado ─► Lista
                                                 (control final)
```

- Cada cambio guarda **quién y cuándo** (tabla `HistorialOrden`: orden, de, a, usuario, fecha, nota). Así se sabe cuánto tarda cada etapa y quién la hizo.
- Se puede **volver una etapa atrás** con nota obligatoria (ej.: "vidrio roto, se repite vidriado").
- Una orden "Lista" que vuelve atrás regresa el pedido de "Terminado" a "En producción" (sale del cálculo automático).
- Atraso: si hoy > `fecha_comprometida` y la orden no está "Lista", se marca en rojo en el tablero y en el listado de pedidos.

**Tablero de fábrica** (pantalla nueva, Etapa 2): columnas por etapa con las órdenes de pedidos liberados, ordenadas por fecha comprometida, con semáforo de atraso. Pensada para usar en el celular o la PC del taller: tocar una orden la pasa a la etapa siguiente. Cada orden impresa lleva un **QR** con su número: escanearlo abre esa orden en el tablero.

---

## 5. Órdenes congeladas y revisiones (resuelve H4)

- Mientras el pedido está en **Recibido**, la orden se edita libremente.
- Al **liberar**, cada orden queda en **Rev. 1** y no se edita más de forma directa.
- Si hay que cambiar algo después, el botón "Modificar orden" pide un motivo, sube la revisión (**Rev. 2**) y la deja marcada como "cambiada después de liberada" en el tablero hasta que el taller la reimprima.
- El PDF muestra la revisión en el encabezado ("N° 0001 · Rev. 2"). Así el taller sabe que el papel con Rev. 1 no vale.

---

## 6. Checklist para liberar (resuelve H3)

"Liberar a fábrica" queda deshabilitado y lista lo que falta, orden por orden:

- Medida cargada (ancho × alto) y cantidad ≥ 1
- Línea, color y tipo de vidrio
- Cantidad de hojas y lado de apertura (si la tipología tiene hojas)
- Fecha comprometida
- **Seña registrada en la venta**: no bloquea. Si falta, advertencia + "Liberar igual" con confirmación y motivo (decisión P2)

---

## 7. Orden de Fabricación (PDF): mejoras manteniendo la estética

Se mantiene **todo** lo visual: azul `#145ea7`, logo arriba a la izquierda, barras de sección azules, una hoja A4 por orden, datos del cliente, bloque de detalle con preguntas, nota, tabla de medidas, croquis cuadriculado, pie con datos de empresa y firmas.

| # | Mejora | Detalle |
|---|---|---|
| M1 | **Detalle precargado del cotizador** (resuelve H6) | Mosquitero y modelo (opcional tipo `mosquitero`), premarco (opcional tipo `premarco`), tipo de marco (`snapshot.marco`), modelo de hoja (`snapshot.hoja`), cantidad de hojas (producto), lado (`snapshot.apertura`), travesaño (`snapshot.tirantes`). Atendido por = vendedor que creó el presupuesto |
| M2 | **Casillas SÍ / NO** donde la respuesta está vacía | En vez de una línea en blanco, `☐ SÍ ☐ NO` para tildar en el papel. Si el dato vino del cotizador, se imprime la respuesta en azul como hoy |
| M3 | **Plano técnico dentro del croquis** (resuelve H7) | El plano con cotas de FEAT-038 se dibuja dentro del recuadro, sobre la cuadrícula, que sigue libre para anotar a mano. Si la orden no tiene dibujo (terciarizado, PVC sin datos), queda la cuadrícula vacía como hoy |
| M4 | **Encabezado con contexto** | Debajo del N° de orden: `Pedido PF-0012 · Presup. 875 · Orden 2 de 5 · Rev. 1` |
| M5 | **Control de etapas al pie** | Las firmas Preparó / Revisó / Producción pasan a una fila de casillas: Corte · Armado · Vidriado · Control, cada una con fecha y firma. Mismo estilo de línea fina |
| M6 | **QR del número de orden** | Esquina superior derecha, chico, para el tablero (Etapa 2) |
| M7 | **Estructura en su propio bloque** | Hoy el texto largo de estructuras (FEAT-045) se aprieta en una fila del detalle; pasa a un recuadro propio con el plano del conjunto y el módulo de la orden resaltado |
| M8 | **PDF del pedido completo** (resuelve H8) | Botón "Imprimir pedido": todas las órdenes en un PDF, una por hoja, con carátula opcional (resumen: cliente, N órdenes, fecha comprometida, estado) |

**Riesgo técnico M3/M7:** el plano hoy lo dibuja JavaScript (`static/js/elevacion.js`) y el PDF de la orden sale con xhtml2pdf, que no ejecuta JS. Opciones a evaluar en el diseño del Arquitecto:
1. Portar `abertura-layout.js` a Python y dibujar con `reportlab.graphics` (ya está en `requirements.txt`) → PNG/SVG embebido. Dos fuentes de la aritmética de cotas → necesita un test que compare ambas.
2. Generar el SVG en el navegador al confirmar el presupuesto y guardarlo en el ítem. No duplica lógica, pero los ítems viejos no lo tendrían.

Antes de decidir: prueba de render con un script de scratchpad (`render_to_string` + pisa + pypdfium2 → PNG), igual que en FEAT-022.

---

## 8. Decisiones del usuario (2026-10-29)

| # | Pregunta | Decisión | Efecto en el plan |
|---|---|---|---|
| P1 | Etapas del taller | **Corte → Armado → Vidriado → Lista**, todas las órdenes pasan por las cuatro | Estados fijos de la orden (no configurables) |
| P2 | ¿Liberar sin seña? | **No debería, pero se deja la opción** | Sin seña, el checklist muestra una advertencia y "Liberar igual" pide confirmación (SweetAlert2) + motivo, que queda en el historial |
| P3 | ¿Quién libera? | **Responsable de fábrica** | Permiso nuevo `fabrica.pedidos_gestion` (liberar, cancelar, modificar orden liberada, entregar). No se agrega paso de medición final |
| P4 | ¿El taller usa el sistema? | **Sí, celular o PC** | Tablero + QR entran en el alcance (Etapa 2) |
| P5 | ¿Quién marca Entregado / Colocado? | **Fábrica** | El responsable de fábrica escribe `Venta.estado`; ventas solo lo ve |

**Permisos resultantes:**

| Código | Quién | Puede |
|---|---|---|
| `despiece.pedidos` (ya existe) | Ventas y fábrica | Ver pedidos y órdenes, editar órdenes mientras el pedido está en Recibido, imprimir |
| `fabrica.pedidos_gestion` (nuevo) | Responsable de fábrica | Liberar, cancelar, modificar orden liberada (Rev. N), marcar entregado / colocado |
| `fabrica.tablero` (nuevo) | Taller | Ver el tablero y avanzar / retroceder etapas |

---

## 9. Criterios de aceptación

**Etapa 1 — Circuito y PDF (Mediano-Grande)**
- [ ] Al confirmar un presupuesto, el pedido nace en **Recibido** y sus órdenes en **Por fabricar**
- [ ] El detalle del pedido muestra el checklist de faltantes y el botón **Liberar a fábrica**, que solo se habilita con el checklist completo
- [ ] Si la venta no tiene seña, se advierte; "Liberar igual" pide confirmación y motivo, y queda en el historial
- [ ] Solo quien tiene `fabrica.pedidos_gestion` ve y puede usar Liberar, Cancelar, Modificar orden liberada y Entregar (por URL directa → 403)
- [ ] Al liberar, el pedido pasa a **En fábrica** y las órdenes quedan congeladas en Rev. 1
- [ ] Modificar una orden liberada pide motivo y sube la revisión; el PDF muestra la revisión
- [ ] Desde el detalle del pedido se cambia la etapa de cada orden; cada cambio queda en el historial con usuario y fecha
- [ ] El estado del pedido pasa solo a **En producción** y a **Terminado** según sus órdenes
- [ ] **Marcar entregado / colocado** actualiza el estado de la Venta
- [ ] Si el presupuesto confirmado pasa a cancelado, el pedido pasa a **Cancelado** y sus órdenes a **Anulada**
- [ ] El listado de pedidos filtra por estado y marca en rojo los atrasados
- [ ] El PDF de la orden incluye M1, M2, M4, M5; mismo diseño y una sola hoja A4
- [ ] Botón **Imprimir pedido** (M8)
- [ ] Número de pedido sin `count()+1` (H9)

**Etapa 2 — Taller en el sistema (Mediano)**
- [ ] Tablero de fábrica: una columna por etapa (Por fabricar · Corte · Armado · Vidriado · Lista) con las órdenes de pedidos liberados, ordenadas por fecha comprometida
- [ ] Semáforo: rojo si está atrasada, amarillo si vence en ≤ 3 días, marca "Cambiada" si tiene una revisión sin reimprimir
- [ ] Usable en celular (360 px): un toque abre la orden y un botón grande la pasa a la etapa siguiente; volver atrás pide nota
- [ ] QR en el PDF (M6) que abre esa orden en el tablero (con login)
- [ ] Permiso nuevo `fabrica.tablero`

**Etapa 3 — Planos en la orden (Mediano, con riesgo técnico)**
- [ ] Plano técnico con cotas dentro del croquis (M3)
- [ ] Bloque propio de estructura con el plano del conjunto (M7)

---

## 10. Diseño técnico — Etapa 1 (Paso 2, Arquitecto, 2026-10-29)

**Paso 1 aprobado por el usuario el 2026-10-29.** Código leído: `plantillas/{models,views,forms,urls,live}.py`,
`orden_pdf.html`, `presupuestos/views.py` (`_procesar_confirmacion`, `cambiar_estado`),
`presupuestos/pdf_descriptions.py` (`build_item_snapshot`), `pricing/aperturas.py` (`normalizar_apertura`),
`usuarios/access_control.py` (`ROUTE_ACCESS_MAP`, middleware por ruta).

### 10.1 Apps y archivos

| Archivo | Cambio |
|---|---|
| `plantillas/models.py` | Estados nuevos del pedido, etapa / revisión de la orden, modelo nuevo `HistorialPedidoFabrica`, `PedidoFabrica.generar_numero()` |
| `plantillas/migrations/0016_circuito_pedidos.py` | Schema + data migration (mapeo de estados viejos) |
| `plantillas/services/circuito.py` **(nuevo)** | Toda la lógica de transiciones (una sola fuente, la usan las vistas y `presupuestos`) |
| `plantillas/services/precarga.py` **(nuevo)** | `detalle_desde_snapshot(snapshot)` → campos del bloque Detalle (M1) |
| `plantillas/forms.py` | `PedidoFabricaForm`, `LiberarPedidoForm`, `CancelarPedidoForm`, `CambiarEtapaForm`, `EntregarPedidoForm`; `OrdenFabricacionForm` suma `motivo_revision` cuando la orden está liberada |
| `plantillas/views.py` | 5 vistas nuevas + reglas de bloqueo en `orden_edit` / `orden_create` / `orden_delete` + `pedido_create` con Form |
| `plantillas/urls.py` | 5 rutas nuevas |
| `plantillas/templates/plantillas/orden_pdf.html` → se parte en `_orden_hoja.html` + `orden_pdf.html` + `pedido_pdf.html` **(nuevo)** | M1, M2, M4, M5, M8 |
| `plantillas/templates/plantillas/pedido_detail.html`, `pedido_list.html`, `orden_form.html` | Botones de circuito, checklist, historial, etapa por orden, filtro y atraso. **Se tocan después del merge del rediseño «Taller»** (sesión akuncalcu-1c) y con sus clases |
| `plantillas/templatetags/` | Filtro `si_no` para las casillas del PDF (M2) |
| `plantillas/live.py` | Registrar también `OrdenFabricacion` para que el detalle se refresque solo (reusa `core.live` del rediseño) |
| `presupuestos/views.py` | `_procesar_confirmacion`: precarga M1 y "Atendido por". `cambiar_estado`: confirmado → cancelado llama a `cancelar_pedido()` |
| `usuarios/access_control.py` | 2 códigos nuevos (grupo `fabrica`) + `_register_route` de las rutas nuevas |
| `plantillas/tests.py` | Tests (§ 10.6) |

**Archivos nuevos:** `services/circuito.py`, `services/precarga.py`, `_orden_hoja.html`, `pedido_pdf.html`, migración 0016.

### 10.2 Base de datos (migración `plantillas/0016`)

**`PedidoFabrica`**
- `estado`: choices nuevos `recibido` · `en_fabrica` · `en_produccion` · `terminado` · `entregado` · `cancelado`; default `recibido`.
- Campos nuevos (todos opcionales, no rompen filas existentes): `liberado_at` (DateTime null), `liberado_por` (FK User, SET_NULL), `entregado_at` (DateTime null), `motivo_cancelacion` (Text blank).
- Métodos: `generar_numero()` (classmethod, reemplaza `count()+1`: toma el mayor `PF-NNNN` existente + 1; el `unique` de `numero` sigue siendo la red de seguridad), `faltantes_para_liberar()` → `[(orden, ['medida', 'color', …])]`, `esta_atrasado` (property), `recalcular_estado()`.

**`OrdenFabricacion`**
- `etapa`: `por_fabricar` · `corte` · `armado` · `vidriado` · `lista` · `anulada`; default `por_fabricar`.
- `revision` (PositiveSmallInteger, default 0; 0 = nunca liberada, pasa a 1 al liberar).
- `reimpresion_pendiente` (Bool, default False; se prende al subir la revisión, se apaga al generar su PDF).
- `etapa_at` (DateTime null).

**`HistorialPedidoFabrica`** (nuevo, un solo historial para pedido y órdenes)
- `pedido` (FK CASCADE, related `historial`), `orden` (FK null, SET_NULL), `tipo` (`estado_pedido` · `etapa_orden` · `revision`), `desde`, `hasta` (Char 20), `usuario` (FK SET_NULL), `nota` (Text blank), `created_at`.
- `verbose_name` y `__str__`; `ordering = ['-created_at']`.

**Data migration (mapeo de lo existente):** `BORRADOR → recibido`, `EN_PROCESO → en_produccion`, `COMPLETADO → entregado`, `CANCELADO → cancelado`. Órdenes existentes: `por_fabricar`, `revision 0`; las de pedidos `COMPLETADO` → `lista`, las de `CANCELADO` → `anulada`. Reversible (mapeo inverso). No se borra ningún dato.

### 10.3 Lógica (`plantillas/services/circuito.py`)

Todas las funciones van en `transaction.atomic()` con `select_for_update()` sobre el pedido y escriben una fila de historial.

| Función | Desde | Hacia | Reglas |
|---|---|---|---|
| `liberar_pedido(pedido, user, motivo_sin_sena='')` | recibido | en_fabrica | `faltantes_para_liberar()` vacío. Si la venta tiene `sena == 0` y no hay pagos, exige `motivo_sin_sena` (va a la nota del historial). Órdenes → `revision = 1` |
| `cambiar_etapa(orden, user, etapa, nota='')` | etapa actual | siguiente o anterior | Solo con pedido en en_fabrica / en_produccion / terminado. Retroceder exige nota. Después: `pedido.recalcular_estado()` |
| `recalcular_estado()` (en el modelo) | en_fabrica / en_produccion / terminado | ídem | Todas las no anuladas en `lista` → terminado; alguna fuera de `por_fabricar` → en_produccion; si no → en_fabrica. Nunca toca recibido, entregado ni cancelado |
| `revisar_orden(orden, user, motivo)` | orden liberada | misma etapa, `revision + 1` | La llama `orden_edit` al guardar una orden de pedido liberado. Prende `reimpresion_pendiente` |
| `marcar_entregado(pedido, user, tipo)` | terminado | entregado | `tipo` ∈ `entregado` / `colocado` → se copia a `Venta.estado` si hay venta |
| `cancelar_pedido(pedido, user, motivo)` | cualquiera salvo entregado | cancelado | Órdenes → `anulada`. Si se llama desde `presupuestos` y el pedido estaba en producción, el mensaje lo advierte |

**Precarga M1** (`services/precarga.py`, desde el `snapshot_item` que ya guarda cada ítem):

| Campo de la orden | Sale de |
|---|---|
| `mosquitero` / `mosquitero_modelo` | opcional de tipo `mosquitero` → "SÍ" / su nombre |
| `premarco` | opcional de tipo `premarco` → "SÍ" |
| `tipo_marco` | `snapshot.marco.descripcion` |
| `modelo_hoja` | `snapshot.hoja.descripcion` |
| `cantidad_hojas` | `len(snapshot.apertura.hojas)` |
| `lado` | `snapshot.apertura.lado` (izq / der) |
| `travesano` | `snapshot.tirantes` → "SÍ (N horizontales / verticales)" |
| `atendido_por` | `presupuesto.created_by` (nombre completo) |

Si el dato no está en el snapshot (PVC, terciarizado, snapshots viejos), el campo queda vacío y el PDF muestra la casilla SÍ / NO.

### 10.4 Vistas, URLs y permisos

| URL name (`plantillas:`) | Vista | Método | Permiso |
|---|---|---|---|
| `pedido_liberar` | `pedido_liberar` | POST | `fabrica.pedidos_gestion` |
| `pedido_cancelar` | `pedido_cancelar` | POST | `fabrica.pedidos_gestion` |
| `pedido_entregar` | `pedido_entregar` | POST | `fabrica.pedidos_gestion` |
| `orden_etapa` | `orden_cambiar_etapa` | POST | `fabrica.pedidos_gestion` o `fabrica.tablero` |
| `pedido_pdf` | `pedido_pdf` | GET | `despiece.pedidos` |

Reglas en vistas existentes:
- `orden_edit`: pedido **recibido** → como hoy. Pedido **liberado** → solo con `fabrica.pedidos_gestion` (si no, `PermissionDenied`); el form pide `motivo_revision` y al guardar llama a `revisar_orden()`. Pedido **entregado / cancelado** → solo lectura.
- `orden_create` / `orden_delete`: solo con pedido recibido; si no, mensaje y redirect.
- `pedido_create`: pasa a `PedidoFabricaForm` y `PedidoFabrica.generar_numero()`.
- `pedido_list`: filtro por estado (GET) y marca de atraso; `select_related` como hoy; paginación de 20.

Permisos: el control de acceso es por ruta (middleware + `ROUTE_ACCESS_MAP`). Los 2 códigos nuevos van como ítems del módulo `despiece` (grupo `fabrica`). Hay que verificar en el Paso 3 que un ítem pueda existir sin entrada propia en el sidebar; si no se puede, se agrega una bandera para ocultarlo.

### 10.5 PDF

- `orden_pdf.html` se parte: la hoja va a `_orden_hoja.html`; `orden_pdf.html` incluye una; `pedido_pdf.html` hace un loop con `<pdf:nextpage />` entre órdenes (M8). Antes de la primera orden va una carátula con el cliente, la cantidad de órdenes, la fecha comprometida y el estado.
- **M2:** las casillas SÍ / NO se dibujan como dos celdas con borde (no con el carácter ☐, que la fuente base de xhtml2pdf no trae).
- **M4:** una línea chica bajo el recuadro N° ORDEN: `Pedido PF-0012 · Presup. 875 · Orden 2 de 5 · Rev. 1`.
- **M5:** la fila de firmas pasa a 4 celdas: CORTE · ARMADO · VIDRIADO · CONTROL, cada una con "Fecha ___ Firma ___", con la misma línea fina.
- **Restricciones de xhtml2pdf** (memoria del proyecto): sin flexbox/grid, sin `height:%`, ignora `nowrap`, se rompe con colspan complejos. Verificación: script de scratchpad (`render_to_string` + pisa + pypdfium2 → PNG) antes y después, y comparación visual de que entra en **una sola hoja A4**.
- **Etapa 3 (planos):** xhtml2pdf 0.2.17 trae `svglib` (verificado en `.venv`), así que un SVG embebido es viable. Falta decidir cómo se genera el SVG (portar `abertura-layout.js` a Python o guardar el SVG al cotizar). Se decide en el diseño de la Etapa 3, no ahora.

### 10.6 Tests (Paso 3)

- Modelos: `__str__` de `HistorialPedidoFabrica`; `generar_numero()` con huecos y con números manuales; `recalcular_estado()` en sus 3 salidas; `faltantes_para_liberar()`.
- Servicios: liberar con y sin faltantes, sin seña con y sin motivo; avanzar y retroceder etapa (sin nota → error); última orden lista → terminado; lista que vuelve → en_produccion; entregar copia el estado a la venta; cancelar anula las órdenes.
- Vistas: status 200/302 de cada vista nueva; sin login → login; sin `fabrica.pedidos_gestion` → 403; `orden_edit` de pedido liberado sube la revisión.
- Integración: confirmar presupuesto → pedido recibido con detalle precargado; cancelar presupuesto confirmado → pedido cancelado.
- PDF: `orden_pdf` y `pedido_pdf` devuelven `application/pdf`; la carátula y la revisión aparecen en el HTML.

### 10.7 Diseño de pantallas: sistema «Taller» (condición del usuario al aprobar el Paso 2)

Todas las pantallas de REQ-063 usan **el mismo diseño que el rediseño «Taller»** de la sesión akuncalcu-1c.
Fuente: [brief-rediseno-taller.md](../team/brief-rediseno-taller.md), `static/css/taller.css`, includes de
`core/templates/core/ui/`, mockups en `docs/team/design/*.dc.html` (para fábrica: `Pedidos-Lista`, `Pedido-Detalle`,
`Orden-Form`; base: `Main.dc.html`). No se inventan clases ni colores. El menú de fila usa la versión de
`kebab_menu.html` con texto configurable que deja el revisor final del rediseño.

- **Base:** `{% extends 'core/base.html' %}` + `{% block title %}`; cabecera con `core/ui/page_header.html` (o markup `.page-head` si lleva más botones).
- **Un solo botón primario por pantalla:** en el detalle del pedido, el primario es la próxima acción del circuito (Liberar a fábrica / Marcar entregado). Cancelar va como `.btn-danger` con SweetAlert; el resto, en `.btn-secondary` o en el `kebab_menu`.
- **Estados con `core/ui/badge.html`** (siempre con texto y `dot=True`):

| Pedido | Tono | Orden (etapa) | Tono |
|---|---|---|---|
| Recibido | amber (necesita acción) | Por fabricar | gray |
| En fábrica | violet (el brief reserva violet para "en fábrica") | Corte / Armado / Vidriado | blue (en curso) |
| En producción | blue | Lista | green |
| Terminado | green | Anulada | red |
| Entregado | gray | | |
| Cancelado | red | Atrasado (extra) | red, ícono reloj |

- **Listado:** `.card` > `.toolbar` (filtro por estado con `.tabs` y contador `.cnt`) > `.table-wrap .tbl` > `core/ui/pagination.html`; vacío con `core/ui/empty_state.html`.
- **Detalle:** cards con `.sec-label`: Datos · Checklist para liberar (faltantes en `text-warn`, advertencia de seña en `bg-warn-soft`) · Órdenes (tabla `.tbl` con badge de etapa, botón `.btn-sm` "Siguiente etapa" y kebab: editar / PDF / retroceder) · Historial (lista cronológica `muted`).
- **Formularios** (liberar sin seña, cancelar, retroceder etapa, motivo de revisión): `.field` + `.input`, en un modal SweetAlert o en la misma card; siempre `{% csrf_token %}`.
- **Tiempo real:** `plantillas/live.py` suma la fuente `ordenes_fabrica` (`OrdenFabricacion`, `updated_at`, permiso `despiece.pedidos`). El detalle del pedido lleva `data-live="pedidos_fabrica,ordenes_fabrica" data-live-partial` y la vista responde a `?partial=1` con `_pedido_detalle_cuerpo.html`. La edición de orden lleva `data-live-edit="plantillas.ordenfabricacion:{{ orden.pk }}"`.
- **Avisos (campanita, `crear_aviso`):** pedido terminado → al vendedor del presupuesto ("PF-0012 listo para entregar"); pedido cancelado por el presupuesto → a quienes tienen `fabrica.pedidos_gestion`; orden revisada después de liberar → idem.
- **Tablero (Etapa 2):** mismas clases; en celular, `.tabs` por etapa y cada orden como `.card` con botón `.btn-primary` grande "Pasar a …".
- **El PDF NO usa Taller:** conserva su identidad (azul `#145ea7`, A4), como pidió el usuario y como fija el brief («PDFs e impresión, prohibido tocar» para el rediseño).
- Verificación visual con Playwright contra el mockup antes del Reviewer (se le propone al usuario).

---

## 11. Análisis de impacto (Paso 2)

- [x] **FKs:** `PedidoFabrica.presupuesto` y `OrdenFabricacion.item_presupuesto` no cambian. `HistorialPedidoFabrica` es nueva y cuelga del pedido con CASCADE (el pedido nunca se borra desde la UI).
- [x] **Vistas que dependen de `estado`:** `pedido_list.html` y `pedido_detail.html` comparan contra `'BORRADOR'` / `'EN_PROCESO'`… en mayúsculas → se actualizan sí o sí. El admin (`list_filter = ['estado']`) sigue andando. `pedidos/views.py` usa otro modelo (pedidos por voz): no se afecta.
- [x] **Templates:** los 3 de `plantillas` + `orden_pdf.html`. Los primeros 3 los está rediseñando la otra sesión → se tocan **después** de su merge.
- [x] **Forms:** `OrdenFabricacionForm` mantiene sus campos; solo suma `motivo_revision` (no es del modelo) cuando corresponde.
- [x] **URL names:** los 5 nombres nuevos no existen hoy en `plantillas`.
- [x] **Datos existentes:** mapeo completo de estados (§ 10.2). Los pedidos viejos en `BORRADOR` quedan en `recibido` y hay que liberarlos para seguirlos; no se pierde nada.
- [x] **Campos obligatorios nuevos:** ninguno sin default.
- [x] **Permisos:** las vistas existentes conservan `despiece.pedidos`. Los usuarios actuales **no** pueden liberar ni entregar hasta que un admin les asigne `fabrica.pedidos_gestion` desde el ABM de usuarios. Los admin tienen todo.

## 12. Riesgos

| Riesgo | Mitigación |
|---|---|
| Cruce con el rediseño «Taller» (otra sesión, rama `development`) en templates de `plantillas`, `presupuestos/views.py` y `access_control.py` | Acordado: implemento después de su merge, en un worktree aparte, con sus clases CSS. Sus números son FEAT-046/047 y ADR-023/024; los míos, FEAT-048+ y ADR-025+ |
| Cancelar el presupuesto cancela un pedido que ya está en producción | Se hace igual (criterio aprobado), pero el mensaje lo advierte y queda en el historial con el usuario |
| `Venta.estado` también se cambia a mano desde Ventas | No hay sincronización de vuelta: la venta no mueve el pedido. Se documenta en el ADR |
| El PDF deja de entrar en una hoja A4 por la línea de contexto o las 4 casillas del pie | Render a PNG antes y después; si no entra, se achica la cuadrícula del croquis (hoy 13 filas) |
| REQ-056 exige que la orden "salga idéntica" después de mover los helpers a `core/pdf.py` | REQ-063 va primero; REQ-056 compara contra el PDF nuevo. Se anota en REQ-056 |
| Etapas fijas en código: si el taller suma una etapa, hace falta una migración | Aceptado (decisión P1) |

**ADR a registrar en el Paso 5 (ADR-025):** estados del pedido calculados desde las etapas de las órdenes + revisiones de orden liberada + historial único.

## Fuera de alcance

- Despiece / cálculo de cortes (eliminado en REQ-036 / ADR-013).
- Avisos por WhatsApp al cliente (exigen templates aprobados de Meta).
- Stock de perfiles y vidrios.
