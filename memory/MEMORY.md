# MEMORY — AkunCalcu

- El sistema de permisos quedó centralizado en `akuna_calc/usuarios/access_control.py`, usando códigos de acceso y mapeo por `namespace:url_name`.
- Los perfiles de acceso viven en `PerfilAccesoUsuario` y los roles globales en `RolSistema`; la migración `usuarios/0002_seed_admin_role.py` asegura el rol `Admin`.
- Si se agregan nuevas vistas o APIs que deban respetar permisos, hay que registrarlas en `ACCESS_MODULES` y/o `ROUTE_ACCESS_MAP` para mantener alineados sidebar, login y bloqueo por URL.