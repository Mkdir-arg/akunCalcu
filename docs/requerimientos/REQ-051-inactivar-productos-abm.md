# REQ-051 — Inactivar y reactivar productos desde el ABM (sin que aparezcan en el cotizador)

- **Estado:** Implementado
- **Fecha:** 2026-09-05
- **Complejidad:** Pequeño
- **Feature:** [FEAT-041](../features/FEAT-041-inactivar-productos-abm.md)
- **Apps afectadas:** `pricing`

## User Story

Como **administrador del catálogo** quiero **inactivar un producto desde `/pricing/config/productos/`
y volver a activarlo cuando haga falta** para **que el cotizador no lo ofrezca mientras esté inactivo,
sin perder su configuración (marcos, hojas, aperturas)**.

## Contexto

El ABM ya tiene una baja lógica: el botón con el tacho pone `Producto.bloqueado = 'Si'` ("Desactivar
producto"), el listado **oculta** los bloqueados y el cotizador (`/pricing/api/pricing/productos/`)
también los excluye. Pero al ocultarlos, el inactivo **desaparece del ABM**: no se ve como "Inactivo"
(el badge y el filtro Activos/Inactivos existen en el template pero nunca se llenan) y **no hay forma
de reactivarlo**. En la práctica el usuario lo vive como un borrado.

No hay borrado físico de productos en ningún lado: `bloqueado` es el único estado.

## Criterios de Aceptación

- [x] El listado de productos muestra **todos** los productos, activos e inactivos, con su badge de estado; el filtro Activos/Inactivos que ya está en la tabla funciona
- [x] Un producto activo tiene el botón **Inactivar** (con confirmación SweetAlert2); uno inactivo tiene el botón **Activar**
- [x] Inactivar pone `bloqueado='Si'`; activar lo limpia. Ningún otro dato del producto cambia
- [x] Un producto inactivo **no aparece en el cotizador** del presupuesto ni en la API de productos que lo alimenta
- [x] Un ítem de presupuesto ya guardado con un producto inactivo sigue abriéndose, dibujándose e imprimiendo igual (la API por id no filtra por estado)
- [x] Los selectores de producto de los ABM de Marcos y Hojas siguen ofreciendo solo activos
- [x] Los productos que se "eliminaron" hasta hoy con el tacho **reaparecen en el listado como Inactivos** (eran esto mismo); nada se pierde ni cambia de estado
- [x] Sin migración: se usa el campo `bloqueado` existente
- [x] Tests: inactivar/activar cambian el estado y redirigen; el listado muestra ambos estados; la API de productos excluye inactivos; sin login redirige

## Fuera de alcance

- Un estado "eliminado" distinto de "inactivo": hoy no existe y nadie lo pidió.
- Inactivar líneas, extrusoras, marcos u hojas (mismo patrón, se puede replicar después).
