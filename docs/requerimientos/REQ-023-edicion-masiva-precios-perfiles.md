# REQ-023 — Edición masiva de precios en perfiles

> **Estado:** En desarrollo
> **Fecha:** 2026-05-16
> **Complejidad:** Mediano

## User Story

Como usuario del módulo Fábrica, quiero editar en bloque los precios de varios perfiles seleccionados
para actualizar líneas completas sin tener que modificar cada perfil uno por uno.

## Criterios de Aceptación

- [ ] La pantalla de perfiles permite seleccionar múltiples registros para operar sobre ellos en conjunto
- [ ] El usuario puede aplicar una actualización de precio a todos los perfiles seleccionados en una sola acción
- [ ] La actualización masiva persiste correctamente el nuevo valor en todos los perfiles seleccionados
- [ ] El flujo evita ejecutar la edición masiva cuando no hay perfiles seleccionados
- [ ] La interfaz informa de forma clara cuántos perfiles serán afectados antes o al confirmar la operación
- [ ] La edición masiva no altera otros campos de los perfiles fuera del precio
- [ ] La operación puede usarse sobre perfiles pertenecientes a una misma línea para agilizar actualizaciones completas
- [ ] Al finalizar, el usuario recibe una confirmación visible de que la actualización fue realizada

## Contexto

Actualmente la configuración de perfiles requiere editar cada registro individualmente.
La mejora busca reducir tiempo operativo en la pantalla de perfiles, especialmente cuando se necesita
actualizar precios de una línea completa o de un conjunto grande de perfiles relacionados.