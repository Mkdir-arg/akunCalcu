# REQ-052 — Inactivar o activar varios productos de una vez

- **Estado:** Implementado
- **Fecha:** 2026-09-05
- **Complejidad:** Pequeño
- **Feature:** [FEAT-041](../features/FEAT-041-inactivar-productos-abm.md) (sección "Acción masiva")
- **Apps afectadas:** `pricing`
- **Extiende:** [REQ-051](./REQ-051-inactivar-productos-abm.md) / FEAT-041

## User Story

Como **administrador del catálogo** quiero **seleccionar varios productos del listado y
inactivarlos (o activarlos) con un solo clic** para **no repetir la operación producto por producto
cuando hay que dar de baja una línea entera o limpiar el catálogo**.

## Criterios de Aceptación

- [x] Cada fila del listado de productos tiene una casilla de selección; la cabecera tiene una casilla **"seleccionar todos"** que marca solo las filas **visibles** con el filtro y la búsqueda actuales
- [x] Al haber al menos una fila marcada aparece una barra con la cantidad seleccionada y los botones **Inactivar seleccionados**, **Activar seleccionados** y **Limpiar selección**
- [x] Ambas acciones piden confirmación (SweetAlert2) indicando cuántos productos se van a tocar
- [x] Un solo POST cambia el estado de todos los seleccionados; el mensaje de éxito dice cuántos se inactivaron o activaron
- [x] Ids inválidos o inexistentes se ignoran sin error; si no llega ninguno, se avisa y no se hace nada
- [x] Los botones individuales Inactivar / Activar de FEAT-041 siguen funcionando igual
- [x] Solo por POST, con login y perfil staff, como el resto del ABM
- [x] Sin migración: sigue siendo `bloqueado='Si'` / `'No'`
- [x] Tests: acción masiva inactiva/activa los ids recibidos; ignora ids no numéricos; sin ids avisa; GET redirige; sin login redirige; el listado renderiza las casillas

## Fuera de alcance

- Selección que sobreviva a un cambio de página o de orden (la tabla no pagina).
- Acciones masivas en los otros ABM (Extrusoras, Líneas, Marcos, Hojas…): mismo patrón, después.
