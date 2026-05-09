# FEAT-009 — Roles y permisos por módulo y opción

> **Requerimiento**: [REQ-019](../requerimientos/REQ-019-roles-permisos-por-modulo-y-opcion.md)
> **Fecha**: 2026-05-09
> **Apps afectadas**: `usuarios`, `core`, `security`

## Descripción funcional

Se incorporó un sistema centralizado de roles y permisos operativos para controlar qué módulos y subsecciones puede ver y usar cada usuario.

- Al crear o editar usuarios, ahora se puede elegir un rol global y marcar permisos granulares por módulo y opción.
- Se agregó el rol `Admin`, que otorga acceso total sin necesidad de tildar permisos individuales.
- El menú lateral se construye dinámicamente según los permisos efectivos del usuario autenticado.
- El acceso manual por URL queda bloqueado cuando el usuario intenta entrar a una sección no autorizada.
- El login redirige al primer módulo habilitado, evitando enviar a usuarios sin permiso al dashboard por defecto.
- Se mantuvo compatibilidad con vistas legacy que todavía dependen de `is_staff`, sincronizando ese flag solo en los accesos que todavía lo necesitan.

## Criterios de aceptación cumplidos

- [x] Al crear un usuario, el administrador puede asignarle un rol y definir sus permisos de acceso.
- [x] Al editar un usuario, el administrador puede modificar su rol y los permisos previamente asignados.
- [x] Existe un rol `Admin` con acceso total a todos los módulos y opciones del sistema.
- [x] Los módulos configurables incluyen `Dashboard`, `Presupuestos`, `Comercial`, `Reportes`, `Productos`, `Despiece`, `Cotizador`, `Fábrica`, `Facturación`, `Seguridad` y `Configuración`.
- [x] Para cada módulo habilitado, el sistema permite definir qué opciones o subsecciones internas quedan visibles y utilizables para ese usuario.
- [x] La lógica de permisos por subsección aplica a cualquier módulo que tenga secciones internas, incluyendo casos como `Reportes`, `Comercial` y `Fábrica`.
- [x] Dentro del módulo `Reportes`, se pueden habilitar de forma independiente las opciones `Reporte General`, `Reporte Ventas`, `Reporte Cobranza`, `Reporte Gastos` y `Reportes Proveedores`.
- [x] Si un usuario no tiene permiso sobre un módulo, ese módulo no se muestra en el menú lateral.
- [x] Si un usuario tiene acceso a un módulo pero no a una opción o subsección interna, esa opción o subsección no se muestra en la navegación correspondiente.
- [x] Un usuario sin permiso no puede acceder manualmente por URL a módulos, opciones o subsecciones no habilitados.
- [x] El acceso total del rol `Admin` no requiere configurar permisos manuales por cada módulo u opción.

## Archivos creados

- `akuna_calc/usuarios/access_control.py` — catálogo central de módulos, permisos y mapeo por `namespace:url_name`.
- `akuna_calc/usuarios/context_processors.py` — expone menú lateral y resumen de acceso al template base.
- `akuna_calc/usuarios/middleware.py` — bloquea acceso por URL según permisos efectivos.
- `akuna_calc/usuarios/migrations/0001_initial.py` — crea `RolSistema` y `PerfilAccesoUsuario`.
- `akuna_calc/usuarios/migrations/0002_seed_admin_role.py` — siembra el rol `Admin` y normaliza perfiles existentes.
- `akuna_calc/usuarios/tests.py` — cobertura del flujo de roles, permisos y navegación.

## Archivos modificados

- `akuna_calc/usuarios/models.py` — nuevos modelos para rol y perfil de acceso.
- `akuna_calc/usuarios/forms.py` — alta y edición de usuarios con rol y permisos granulares.
- `akuna_calc/usuarios/views.py` — gestión de usuarios con resumen de rol/acceso y toggle protegido por POST.
- `akuna_calc/usuarios/templates/usuarios/user_form.html` — UI de asignación de permisos por módulo.
- `akuna_calc/usuarios/templates/usuarios/user_list.html` — muestra rol, accesos y activación segura por POST.
- `akuna_calc/core/templates/core/base.html` — sidebar renderizado desde permisos efectivos.
- `akuna_calc/core/views.py` — login y redirección inicial según módulos habilitados.
- `akuna_calc/core/urls.py` — usa la vista de login personalizada.
- `akuna_calc/core/templates/core/login.html` — muestra mensajes de acceso y redirección.
- `akuna_calc/akuna_calc/settings.py` — incorpora middleware y context processor del sistema de permisos.
- `akuna_calc/security/views.py` — endurece acceso con `@login_required` sobre backups.
- `akuna_calc/pricing/tests.py` — ajusta la expectativa de redirección al login actual.

## Decisiones técnicas

- No se modificó `auth_user`; los permisos se modelan en `PerfilAccesoUsuario` con relación one-to-one.
- La autorización usa un registro central por nombre de ruta, para soportar módulos que atraviesan varias apps y endpoints compartidos.
- El menú lateral y el bloqueo por URL consumen la misma fuente de verdad para evitar desalineaciones entre lo visible y lo permitido.
- El flag legacy `is_staff` se sigue utilizando como compatibilidad temporal para vistas antiguas aún no migradas al nuevo esquema.

## Validación

- `python manage.py makemigrations usuarios`
- Suite `usuarios` validada en SQLite en memoria con `MIGRATION_MODULES=None` para las apps del proyecto.
- No se pudo validar la suite completa de `pricing` en SQLite porque depende de tablas legacy no gestionadas (`extrusoras`, `marco`, `perfiles`) fuera del historial migratorio actual.