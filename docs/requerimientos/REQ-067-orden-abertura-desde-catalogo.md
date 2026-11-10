# REQ-067 — Abertura de la Orden de Fabricación elegida del catálogo, con la lógica del cotizador

**Estado:** Implementado
**Derivó en:** [FEAT-051](../features/FEAT-051-orden-abertura-desde-catalogo.md)
**Fecha:** 2026-11-10
**Complejidad:** Grande
**Relacionado:** REQ-063 / FEAT-048 (circuito de pedidos, precarga M1), FEAT-023 (cotizador en «Agregar orden»), FEAT-021 (Órdenes de Fabricación)

## Problema

En la edición de la orden (`/plantillas/ordenes/<id>/editar/`) la abertura se carga en texto libre:
Tipo de abertura, Línea, Color, Tipo de marco, Modelo de hoja, Cantidad de hojas, Tipo de vidrio.
Se puede escribir cualquier cosa, nada valida que la combinación exista, y pasan cosas como:

- Orden 390 (PF-0189): «Modelo de hoja = OSCILOBATIENTE VIDRIO DVH» con «Cantidad de hojas» vacío, lo que
  deja la orden bloqueada en «Falta completar para liberar».
- Corregir una orden mal precargada exige saber de memoria el nombre exacto del perfil.

«Agregar orden» ya usa el cotizador en cascada (FEAT-023). Editar una orden no.

## User Story

Como **responsable de fábrica** quiero **corregir la abertura de una orden eligiendo de los mismos
desplegables en cascada del cotizador (Extrusora → Línea → Producto → Marco → Hoja → Vidrio + Color)**
para **que la orden tenga siempre una combinación que existe en el catálogo y llegue completa al taller**.

## Criterios de aceptación

- [ ] La edición de la orden muestra un bloque «Abertura» con los desplegables en cascada del cotizador:
      Extrusora → Línea → Producto → Marco → Modelo de hoja → Vidrio y Color.
- [ ] Cada desplegable se filtra según el anterior, con las mismas APIs y reglas que el cotizador
      (`/pricing/api/pricing/...`). Cambiar uno de arriba limpia los de abajo.
- [ ] Al elegir la hoja, «Cantidad de hojas» se completa sola con la del catálogo.
- [ ] Al guardar, se graban en la orden los textos resueltos: Tipo de abertura, Línea, Color, Tipo de marco,
      Modelo de hoja, Cantidad de hojas y Tipo de vidrio (los mismos campos que hoy, el PDF no cambia).
- [ ] Si la orden ya tiene valores (precargados o escritos a mano), se ven al abrir la pantalla. Si no se toca
      el bloque «Abertura», se guardan sin cambios.
- [ ] Si un valor guardado no existe en el catálogo (orden vieja o escrita a mano), se muestra tal cual con un
      aviso «no está en el catálogo» y no se pierde al guardar.
- [ ] En una orden ya liberada, cambiar la abertura sigue el circuito actual: pide motivo y sube la revisión.
- [ ] Los demás campos del Detalle (mosquitero, premarco, tapacinta, etc.) no cambian en este REQ.
- [ ] El cotizador de presupuestos y el de «Agregar orden» siguen funcionando igual.
- [ ] No se calcula ni se guarda precio en la orden.

## Fuera de alcance

- Pasar a SÍ / NO o listas fijas los campos que no están en el catálogo (opción A, otro REQ si se pide).
- Guardar IDs de catálogo en la orden (se decide en el diseño técnico).
