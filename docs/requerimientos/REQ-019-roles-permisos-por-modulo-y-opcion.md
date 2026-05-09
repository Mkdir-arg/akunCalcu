# REQ-019 — Roles y permisos por módulo y opción

> **Estado**: Implementado
> **Fecha**: 2026-05-09
> **Complejidad**: Grande
> **Derivará en**: FEAT-009

## User Story
Como administrador quiero definir al crear o editar un usuario qué módulos del sistema y qué opciones o subsecciones internas de cada módulo puede ver y usar, para controlar el acceso operativo según el rol de cada persona sin mostrar menús no autorizados.

## Criterios de Aceptación
- [x] Al crear un usuario, el administrador puede asignarle un rol y definir sus permisos de acceso.
- [x] Al editar un usuario, el administrador puede modificar su rol y los permisos previamente asignados.
- [x] Existe un rol `Admin` con acceso total a todos los módulos y opciones del sistema.
- [x] Los módulos configurables incluyen `Dashboard`, `Presupuestos`, `Comercial`, `Reportes`, `Productos`, `Despiece`, `Cotizador`, `Fábrica`, `Facturación`, `Seguridad` y `Configuración`.
- [x] Para cada módulo habilitado, el sistema permite definir qué opciones o subsecciones internas quedan visibles y utilizables para ese usuario.
- [x] La lógica de permisos por subsección aplica a cualquier módulo que tenga secciones internas, incluyendo casos como `Reportes`, `Comercial`, `Fábrica` y otros módulos equivalentes de la aplicación.
- [x] Dentro del módulo `Reportes`, se pueden habilitar de forma independiente las opciones `Reporte General`, `Reporte Ventas`, `Reporte Cobranza`, `Reporte Gastos` y `Reportes Proveedores`.
- [x] Si un usuario no tiene permiso sobre un módulo, ese módulo no se muestra en el menú lateral.
- [x] Si un usuario tiene acceso a un módulo pero no a una opción o subsección interna, esa opción o subsección no se muestra en la navegación correspondiente.
- [x] Un usuario sin permiso no puede acceder manualmente por URL a módulos, opciones o subsecciones no habilitados.
- [x] El acceso total del rol `Admin` no requiere configurar permisos manuales por cada módulo u opción.

## Notas
- El objetivo es centralizar la gestión de acceso desde la creación y edición de usuarios, contemplando roles y permisos operativos visibles en la interfaz.
- El pedido incluye ocultar elementos del menú lateral según permisos efectivos del usuario autenticado.
- En esta primera definición quedaron explicitadas las opciones internas del módulo `Reportes` como ejemplo concreto; el detalle equivalente de módulos con subsecciones como `Comercial`, `Fábrica` y otros se completará en el diseño técnico según la estructura actual del sistema.