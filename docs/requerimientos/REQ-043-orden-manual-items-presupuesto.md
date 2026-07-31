# REQ-043 — Orden manual de los ítems del presupuesto

- **Estado:** Implementado
- **Fecha:** 2026-07-30
- **Derivó en:** [FEAT-033](../features/FEAT-033-orden-manual-items-presupuesto.md)

## Contexto

Los ítems de un presupuesto se muestran (y salen en el PDF) en el orden en que se cargaron. El vendedor no tiene forma de acomodarlos para presentárselos al cliente en un orden que tenga sentido comercial (por ambiente, por importancia, agrupando aberturas parecidas).

`ItemPresupuesto` ya tiene un campo `orden` y `Meta.ordering = ['orden', 'created_at']`, y tanto el detalle como el PDF usan `presupuesto.items.all()`, así que **ya ordenan por ese campo**: sólo faltaba una forma de setearlo.

## User Story

```
Como vendedor
quiero poder arrastrar los ítems de un presupuesto para cambiarles el orden y guardarlo
para que el PDF que ve el cliente muestre los ítems en el orden que yo decido.
```

## Criterios de aceptación

- [x] En el detalle del presupuesto, al lado del contador de ítems y del botón *Agregar*, hay un botón **"Orden"**.
- [x] Al tocarlo se abre una vista donde los ítems se pueden **arrastrar** para arriba y para abajo.
- [x] El orden se **guarda** y se mantiene al recargar.
- [x] Ese orden es el que se ve en el **PDF** del presupuesto.
- [x] Los ítems nuevos se agregan **al final**.
- [x] No se puede reordenar un presupuesto **confirmado o cancelado** (igual que no se pueden agregar ni editar ítems).
- [x] El botón sólo aparece con **2 ítems o más**.
- [x] Tests del endpoint y de la visibilidad del botón.

## Alcance

**Incluye:** botón + modal de ordenamiento con drag & drop, endpoint de guardado, orden reflejado en detalle y PDF, ítems nuevos al final.

**Fuera de alcance:** agrupar ítems por ambiente/categoría, ordenar automáticamente por algún criterio (precio, medida), y reordenar desde el listado general de presupuestos.

## Complejidad estimada

**Pequeño** — el modelo ya soportaba el orden; es una view + un modal, sin migración.
