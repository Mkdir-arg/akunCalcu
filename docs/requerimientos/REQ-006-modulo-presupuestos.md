# REQ-006 — Módulo de Presupuestos

**Estado:** En desarrollo
**Fecha:** 2026-03-11
**Derivó en:** —

---

## Descripción

Crear un módulo de presupuestos que permita vincular un cliente con una cotización formal.
El presupuesto puede tener N ítems, cada uno calculado con la lógica del cotizador.
Al confirmar, se genera un PDF descargable. Una vez confirmado, el presupuesto pasa a fábrica (pendiente para fase 2).

---

## User Story

Como vendedor, quiero armar un presupuesto vinculado a un cliente,
agregar múltiples ítems usando la lógica del cotizador, y generar un
PDF para entregar al cliente, para profesionalizar el proceso de venta
y llevar un registro formal de cada cotización.

---

## Criterios de Aceptación

- [ ] Se puede crear un presupuesto seleccionando un cliente existente
- [ ] El presupuesto tiene número autogenerado, fecha de creación y fecha de expiración
- [ ] El presupuesto tiene estados: Borrador, Enviado, Confirmado, Vencido, Cancelado
- [ ] Se pueden agregar N ítems al presupuesto, cada uno con la lógica del cotizador
- [ ] Cada ítem muestra descripción, dimensiones, margen y precio calculado
- [ ] Se puede editar o eliminar cada ítem mientras el presupuesto está en Borrador
- [ ] Al confirmar se genera un PDF descargable
- [ ] El PDF incluye: nombre empresa, cliente, número, fechas, tabla de ítems, total
- [ ] Los presupuestos Confirmados no se pueden modificar
- [ ] Hay una lista de presupuestos con filtro por estado y cliente
- [ ] El presupuesto tiene un historial de comentarios: cualquier usuario puede agregar un comentario con fecha y autor
- [ ] Los comentarios se muestran en orden cronológico dentro del detalle del presupuesto

---

## Notas

- La integración con fábrica (al confirmar → pasa a producción) queda pendiente para Fase 2.
- Clientes se toman del modelo existente en app `comercial`.
- Lógica de cálculo se reutiliza desde `pricing.services.calculator`.
