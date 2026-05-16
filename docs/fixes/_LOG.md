# Log de Fixes — AkunCalcu

> Registro de bugs corregidos en ciclo normal (dentro de sprint).
> Los fixes urgentes en producción están en `docs/hotfix/_LOG.md`.

## Formato de entrada

```
### FIX-XXX — Título del bug
**Fecha**: YYYY-MM-DD
**Reportado por**: [usuario/equipo]
**Severidad**: Baja / Media / Alta
**Feature afectada**: FEAT-XXX o módulo

**Síntoma**: Qué veía el usuario.
**Causa raíz**: Por qué ocurría.
**Solución**: Qué se cambió.
**Archivos modificados**: lista
```

---

## Fixes registrados

### FIX-002 — Reporte de proveedores desincronizado con pagos cargados
**Fecha**: 2026-05-16
**Reportado por**: Usuario
**Severidad**: Alta
**Feature afectada**: Módulo comercial / reporte de proveedores

**Síntoma**: Había pagos de compras cargados que no impactaban correctamente en el reporte de proveedores, generando saldos, totales y movimientos inconsistentes entre la compra y la cuenta corriente mostrada.
**Causa raíz**: El saldo de `Compra` se recalculaba usando la relación `pagos_compra` sobre instancias que podían venir cacheadas por `prefetch_related`, y el reporte de proveedores reconstruía los pagos apoyándose en esa misma relación. Eso abría una ventana de desincronización cuando cambiaban los pagos asociados.
**Solución**: Se cambió el recálculo de saldo para consultar el total de pagos con `aggregate(Sum('monto'))` directamente en base de datos y se actualizó la cuenta corriente del proveedor para obtener los pagos con una consulta dedicada a `PagoCompra`. Además, se agregaron regresiones para edición, eliminación de pagos y recálculo con cache prefetched.
**Archivos modificados**: `akuna_calc/comercial/models.py`, `akuna_calc/comercial/views.py`, `akuna_calc/comercial/tests.py`

### FIX-001 — Formulario de usuarios: ocultar permisos para Admin y reducir scroll con solapas
**Fecha**: 2026-05-09
**Reportado por**: Usuario
**Severidad**: Media
**Feature afectada**: FEAT-009

**Síntoma**: Al elegir un rol con acceso total como `Admin`, la pantalla seguía mostrando el bloque "Permisos por módulo" aunque no aplicara. Además, la lista completa de módulos y opciones hacía el formulario demasiado largo y obligaba a scrollear de más.
**Causa raíz**: El template no conocía si el rol seleccionado tenía `acceso_total`, por lo que siempre renderizaba la sección de permisos. También todos los grupos se apilaban en una sola vista sin paginación ni navegación por secciones.
**Solución**: Se agregó al formulario un estado explícito para detectar roles con acceso total y se usó en la UI para ocultar la configuración manual cuando corresponde. La grilla de permisos se reorganizó en solapas por módulo para mostrar un solo grupo a la vez y reducir la altura total de la página.
**Archivos modificados**: `akuna_calc/usuarios/forms.py`, `akuna_calc/usuarios/templates/usuarios/user_form.html`, `akuna_calc/usuarios/tests.py`
