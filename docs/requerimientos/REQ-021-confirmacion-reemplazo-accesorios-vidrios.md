# REQ-021 — Confirmación al reemplazar accesorios o vidrios en configurador de hojas

> **Estado**: En desarrollo
> **Fecha**: 2026-05-15
> **Complejidad**: Pequeño
> **Derivará en**: —

## User Story
Como vendedor quiero que el sistema me pida confirmación antes de reemplazar un accesorio o vidrio ya cargado en la configuración de hojas para evitar sobrescribir selecciones previas por error.

## Criterios de Aceptación
- [ ] Al intentar cargar un accesorio en una posición donde ya existe uno previamente seleccionado, el sistema no reemplaza automáticamente.
- [ ] Al intentar cargar un vidrio en una posición donde ya existe uno previamente seleccionado, el sistema no reemplaza automáticamente.
- [ ] En ambos casos se muestra un modal de confirmación con el mensaje: `¿Desea reemplazar este accesorio?` (o equivalente contextual para vidrio, manteniendo claridad de la acción).
- [ ] Si el usuario confirma, el sistema reemplaza el ítem existente por el nuevo.
- [ ] Si el usuario cancela, el sistema conserva el ítem previamente seleccionado sin cambios.
- [ ] El flujo funciona en la pantalla de edición del configurador de hojas (`/pricing/config/hojas/<id>/editar/`) sin romper la carga actual de accesorios ni vidrios.

## Notas
- Tipo: Bug + UX.
- Prioridad: Alta.
- URL de referencia: https://akun.pythonanywhere.com/pricing/config/hojas/10/editar/
- Se debe priorizar una interacción clara para evitar reemplazos accidentales.