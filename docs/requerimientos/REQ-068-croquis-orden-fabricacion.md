# REQ-068 — Croquis dibujado en el PDF de la Orden de Fabricación

**Estado:** Implementado
**Derivó en:** [FEAT-052](../features/FEAT-052-croquis-orden-fabricacion.md)
**Fecha:** 2026-11-10
**Complejidad:** Mediano
**Relacionado:** FEAT-021/022 (Órdenes de Fabricación + PDF), FEAT-037/038 (aperturas configurables + anexo «Planos»),
REQ-063 / FEAT-048 (circuito de pedidos), REQ-067 (abertura de la orden desde el catálogo)
**Maqueta aprobada (2026-11-10):** https://claude.ai/artifact/Goi7m8ASkT4v2SfpRmgLwi

## Problema

En el PDF de la orden (`/plantillas/ordenes/<id>/pdf/`) el bloque «CROQUIS (sentidos de apertura, paños fijos,
travesaños)» sale siempre vacío. No es un error: es una grilla de 4 × 30 celdas pensada para dibujar a mano,
y el código nunca dibuja nada ahí (`plantillas/views.py` `_contexto_pdf_base`, `_orden_hoja.html`).

Los datos para dibujarlo ya existen en el ítem de presupuesto de origen (`OrdenFabricacion.item_presupuesto`):
medidas, tipología, apertura (tipo, lado, hojas) y tirantes (travesaños y parantes). Con esos datos el anexo
«Planos» del PDF del presupuesto ya dibuja la abertura, pero lo hace con JavaScript en el navegador, y el PDF
de la orden lo arma `xhtml2pdf` en el servidor, que no ejecuta JavaScript.

## User Story

Como **responsable de fábrica** quiero **que la Orden de Fabricación traiga dibujada la abertura, con el sentido
de apertura, los paños fijos y los travesaños** para **que el taller fabrique sin tener que interpretar el texto
ni dibujarla a mano, y con el mismo dibujo que vio el cliente en el presupuesto**.

## Criterios de aceptación

- [ ] Si la orden viene de un ítem de presupuesto que tiene dibujo, el bloque CROQUIS muestra la elevación de esa
      abertura: marco, paños, hojas, travesaños y parantes en su posición.
- [ ] Cada paño lleva el símbolo de su apertura, igual que en el anexo «Planos» del presupuesto: flechas en
      corredizas, diagonales desde la bisagra en paños de abrir y puertas, vértice en banderola y brazo de
      empuje, rombo en proyectante, lateral + basculante en oscilobatiente.
- [ ] Los paños fijos llevan el rótulo «FIJO» y los ciegos se distinguen del vidrio.
- [ ] El dibujo lleva cotas de ancho y alto totales, y la altura de cada travesaño.
- [ ] Al costado del dibujo se lee en texto: apertura (con lado de la bisagra), cantidad de paños y travesaño.
- [ ] El encabezado del bloque dice desde qué lado se ve el dibujo (ver decisión pendiente).
- [ ] Las cotas nunca contradicen la tabla de MEDIDAS: si la orden tiene más de una medida, o la medida no
      coincide con la del ítem, el dibujo sale sin cotas (solo la forma y los símbolos).
- [ ] Si la abertura de la orden ya no coincide con la del ítem (por ejemplo, se cambió la cantidad de hojas o el
      tipo al corregirla), no se dibuja: queda la grilla vacía de hoy.
- [ ] Debajo del dibujo queda una franja chica de grilla para corregir a mano.
- [ ] Orden manual, vieja, sin ítem de origen, de estructura o de un producto que no se dibuja (persianas,
      cortinas, cajones): queda la grilla vacía de hoy, sin error.
- [ ] El PDF entra en una hoja A4, igual que hoy, también con el dibujo.
- [ ] El PDF de una orden y el del pedido completo (todas las órdenes) se generan igual.
- [ ] No se agregan librerías nuevas.
- [ ] Tests: orden con ítem dibujable trae la imagen del croquis; orden sin ítem trae la grilla; medidas que no
      coinciden quitan las cotas; abertura cambiada deja la grilla.

## Decisión pendiente (usuario / fábrica)

- **Vista:** se tomó «desde el interior» (la de la maqueta aprobada); falta confirmarlo con fábrica. ¿El dibujo se ve desde el interior o desde el exterior? Cambia de qué lado del papel cae la bisagra.
  El anexo «Planos» del presupuesto lo dibuja «de frente», sin aclarar.

## Fuera de alcance

- Estructuras (varias aberturas sobre una pared): siguen con la grilla. Se pueden sumar en otro REQ.
- Editar o dibujar el croquis desde la pantalla de la orden.
- Cambiar el anexo «Planos» del PDF del presupuesto.
