# REQ-014 — Tipo Premarco en opcionales + relaciones con Líneas y Perfiles

**Estado:** En desarrollo
**Fecha:** 2026-05-02

## User Story
Como administrador quiero poder definir opcionales del tipo Premarco con una Línea asociada y seleccionar un Perfil en las fórmulas de cálculo para configurar correctamente ese tipo de opcional desde la interfaz.

## Criterios de Aceptación
- [ ] En la edición de Plantillas Opcionales existe una nueva opción `Premarco` dentro del campo Tipo.
- [ ] Cuando el usuario selecciona `Premarco`, se muestra debajo un campo `Línea`.
- [ ] El campo `Línea` permite seleccionar un registro existente de la configuración de líneas en `/pricing/config/lineas/`.
- [ ] Cuando el tipo seleccionado no es `Premarco`, el campo `Línea` no se muestra o no se exige.
- [ ] En la sección `Fórmulas de Cálculo` existe un nuevo campo para relacionar la fórmula con un registro de `/pricing/config/perfiles/`.
- [ ] La relación seleccionada de Línea y de Perfil se persiste correctamente al guardar la edición.
- [ ] Al volver a editar el registro, si existen relaciones guardadas, se muestran precargadas.
- [ ] La validación del formulario impide combinaciones inconsistentes, por ejemplo exigir Línea cuando el tipo es `Premarco`.

## Notas
- Complejidad: Mediano
- Alcance inicial: edición de `/plantillas/opcionales/10/editar/` y configuración asociada en fórmulas de cálculo.
- Derivará en una feature cuando se implemente.