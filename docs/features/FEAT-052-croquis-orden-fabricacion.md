# FEAT-052 — Croquis dibujado en el PDF de la Orden de Fabricación

**Estado:** Implementado (en `development`, sin commitear)
**Fecha:** 2026-11-10
**Requerimiento:** [REQ-068](../requerimientos/REQ-068-croquis-orden-fabricacion.md)
**ADR:** ADR-028
**Maqueta:** https://claude.ai/artifact/Goi7m8ASkT4v2SfpRmgLwi

## Qué hace

El bloque **CROQUIS** del PDF de la orden (`/plantillas/ordenes/<id>/pdf/`) y del pedido completo
(`/plantillas/pedidos/<id>/pdf/`) ya no sale vacío cuando la orden viene de un ítem de presupuesto.
Muestra la elevación de la abertura, igual que el anexo «Planos» del presupuesto:

- Marco, hojas, vidrio y los tirantes (travesaños o parantes) en su posición; los paños ciegos en gris.
- Símbolo de apertura por paño: flechas con carril Int./Ext. en corredizas, diagonales desde la bisagra en
  paños de abrir y puertas, vértice en banderola y brazo de empuje, rombo en proyectante y lateral +
  basculante en oscilobatiente. Los paños fijos llevan «FIJO» y el mosquitero va rayado.
- Cotas: alto, ancho total, ancho de cada hoja y medida de cada sección de los tirantes.
- Al costado, en texto: apertura (con el lado de la bisagra), paños (+ mosquitero) y travesaño.
- El encabezado dice «vista desde el interior» y si lleva cotas.

Cuándo **no** dibuja (queda la grilla vacía de siempre, para dibujar a mano):
- Orden sin ítem de origen (manual o del cotizador de «Agregar orden»), ítem sin snapshot (PVC,
  terciarizados, viejos), estructura, o producto que no se dibuja (persianas, cortinas, cajones).
- La abertura de la orden ya no es la del ítem: cambió el tipo de abertura, la cantidad de hojas o el lado.
  Un lado vacío (órdenes anteriores a REQ-063) no cuenta como cambio.

Cuándo dibuja **sin cotas**: si la orden tiene más de una medida o la medida no es la del ítem. Así las
cotas nunca contradicen la tabla de MEDIDAS.

## Criterios de aceptación

- [x] Orden de un ítem con dibujo: elevación con marco, paños, hojas, travesaños y parantes.
- [x] Símbolos de apertura iguales al anexo «Planos».
- [x] Paños fijos con «FIJO» y ciegos distinguidos del vidrio.
- [x] Cotas de ancho, alto y de cada sección de tirantes.
- [x] Texto al costado: apertura, paños y travesaño.
- [x] El encabezado dice desde qué lado se ve (interior, asumido; ver Pendientes).
- [x] Las cotas no contradicen MEDIDAS (si no coinciden, sin cotas).
- [x] Abertura cambiada respecto del ítem: grilla vacía.
- [ ] ~~Franja de grilla para corregir a mano~~: se sacó porque no entraba en la A4; para anotar queda el
      espacio en blanco de la celda del dibujo (aceptado por el usuario en el Paso 3).
- [x] Orden manual, vieja, sin ítem, de estructura o no dibujable: grilla vacía, sin error.
- [x] El PDF entra en una A4 (probado con banda de revisión + nota + características).
- [x] PDF de orden y de pedido se generan igual.
- [x] Sin librerías nuevas (svglib ya viene con xhtml2pdf 0.2.17).
- [x] Tests (13 en `plantillas/tests_croquis.py`).

## Archivos

| Archivo | Cambio |
|---|---|
| `pricing/elevacion.py` | Nuevo. Espejo en Python de `abertura-layout.js` + `elevacion.js`: layout, símbolos y SVG con cotas |
| `plantillas/services/croquis.py` | Nuevo. `croquis_de_orden(orden, medidas)`: decide si dibuja, si lleva cotas y arma los textos |
| `plantillas/views.py` | `_contexto_hoja` suma `croquis`; `orden_pdf` y `pedido_pdf` hacen `select_related('item_presupuesto')` |
| `plantillas/templates/plantillas/_orden_hoja.html` | Bloque CROQUIS con dibujo + datos, o la grilla de siempre |
| `plantillas/templates/plantillas/_orden_pdf_estilos.html` | Estilos `.croquis-dib` y `.croquis-datos` |
| `plantillas/tests_croquis.py` | Nuevo. SVG por tipo de apertura, cotas, reglas de dibujo y PDF de orden y pedido |

## Decisiones técnicas

- **SVG embebido en base64**, que xhtml2pdf rasteriza con svglib. No hay PNG ni librería nueva (ADR-028).
- **El dibujo existe dos veces (JS y Python).** Cada archivo apunta al otro (ADR-028).
- **Tamaño del `<img>` como texto con punto.** El template localizado escribía «36,3mm» y xhtml2pdf
  ignoraba ese CSS, por eso la imagen salía chiquita.
- **El alto del dibujo se adapta a cada hoja** (`alto_disponible`): entre 20 y 70 mm, según cuánto ocupan
  la banda de revisión, la nota, las características, las medidas extra y un tipo de abertura largo. Los
  costos se midieron renderizando con xhtml2pdf y se verificaron 192 combinaciones: ninguna hoja que entraba
  en una A4 con la grilla pasa a dos páginas. Una orden típica queda en unos 60 mm (antes eran 30 fijos).
- **Diferencias con el JS, impuestas por svglib:** el texto se centra a mano porque no hay
  `dominant-baseline`, y el mosquitero va con rayas sueltas en lugar de `<pattern>`. Además se agregan las
  cotas de las secciones de tirantes.

## Pendientes

- Confirmar con fábrica que «vista desde el interior» es correcta. La convención del cotizador es «vista
  de frente», y el lado de la bisagra lo elige el vendedor.
- Si una orden se corrige con la cascada de REQ-067 y el texto del tipo de abertura queda distinto al del
  ítem, el croquis vuelve a la grilla. Es a propósito.
- Estructuras (una orden por módulo): siguen con la grilla. Cada módulo ya tiene su `dibujo` guardado y se
  podría sumar en otro REQ.
- Probar con órdenes reales de prod, por ejemplo la 389.
