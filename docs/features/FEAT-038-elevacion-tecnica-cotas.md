# FEAT-038 — Elevación técnica con cotas: cotizador, PDF (anexo de planos) y miniatura

- **Estado:** Implementado
- **Fechas:** 2026-08-26 (cotizador) · 2026-09-03 (PDF y página del presupuesto)
- **Requerimiento:** [REQ-048](../requerimientos/REQ-048-elevacion-tecnica-cotas.md) (retroactivo)
- **ADR:** [ADR-020](../team/decisions.md)
- **Apps:** `presupuestos` · módulos JS en `static/js/`
- **Commits:** `0bdec4e` (cotizador: pestañas 3D / Plano, overlay de cotas) · `994adf9` (PDF y miniatura) · `63c9afc` (anexo "Planos")

## Qué hace

Un **plano técnico vista de frente** de cada abertura, a partir de los planos de referencia de la
fábrica: cota de alto a la izquierda, cotas de cada paño y del total abajo, composición del
vidrio dentro del paño, mosquitero rayado, secciones ciegas de los tirantes en gris.

Aparece en tres lugares, desde el mismo módulo:

| Lugar | Qué se ve |
|---|---|
| **Cotizador** (modal de ítem) | pestañas **3D / Plano** en el mismo alto; en 3D, un overlay de cotas que se desvanece al girar la cámara |
| **PDF del cliente** | un **anexo "Planos de las aberturas"** después de los totales, un plano por ítem en grilla de 2 columnas, con "Ítem N", título y medidas; la tabla de precios queda limpia con la etiqueta "Ítem N" |
| **Página del presupuesto** | miniatura de solo silueta a la izquierda de cada ítem |

## Cómo está armado

- **`static/js/abertura-layout.js`** — módulo puro (sin Three.js ni DOM) que calcula en mm el
  hueco, los paños, las secciones por tirantes, el mosquitero y las cotas. Es la única fuente de
  la aritmética de cotas para la elevación 2D y para el overlay del 3D.
- **`static/js/elevacion.js`** — devuelve un string SVG; sirve en el cotizador, en la página y en
  el PDF porque el presupuesto imprime por `window.print()` (ADR-006) y el SVG inline entra tal cual.
- **`static/js/cotas3d.js`** — proyecta los anclajes 3D a pantalla y dibuja las cotas en un `<svg>`
  sobre el canvas; se desvanece pasados ~57° del frente porque en perspectiva dos paños iguales
  se proyectan con largos distintos y la cota miente.
- **`build_dibujo_params(snapshot)`** en `pdf_descriptions.py` traduce el snapshot del ítem a los
  parámetros del módulo, resolviendo la tipología igual que el cotizador (`resolver_tipologia`).
  Ítems 0×0 (terciarizados, PVC simple) y `no_dibujo` no se dibujan; snapshots viejos sin producto
  se clasifican por descripción.

## Hallazgos que cambiaron el diseño

1. **Las cotas de paño parten el ancho total**, de borde exterior a eje del travesaño: una
   corrediza de 1790 con 2 hojas cota **895 + 895**, no 840 + 840 del hueco. Verificado contra
   los tres planos de referencia (1790, 3630 y 950). El último segmento absorbe el redondeo para
   que la suma siempre cierre.
2. **El dibujo dentro de la celda de la tabla no funcionaba** (estiraba la fila, cotas ilegibles):
   por eso el anexo. El usuario lo rechazó al verlo y se movió en el mismo día.
3. **El dibujo destapa datos mal cargados**: mostró un ítem con travesaño y sección ciega arriba
   que el texto describía como "vidrio simple". Si la sección ciega no existe, el precio también
   está mal, porque se cotiza como revestimiento.

## Verificación

- Tests Django del contexto del PDF (anexo, numeración, sin dibujos no hay anexo) y de
  `build_dibujo_params`.
- `audit_cotas.mjs` (Node): suma de cotas, planos de referencia, secciones, escape de texto hostil.
- Render de `pdf.html` con ítems falsos: `json_script` con id encadenado, placeholder, `static`
  resuelto, script del módulo.
- Confirmado visualmente en producción por el usuario (PDF 703 y 875).

## Pendiente

- La composición del vidrio sale de `Vidrio.descripcion` tal cual ("FLOAT 6 MM"); si se quiere
  "3+3/9/3+3" hay que cargarlo así en el catálogo o agregar un campo.
- La cota "484" de los planos de referencia nunca se definió y no se dibuja.
