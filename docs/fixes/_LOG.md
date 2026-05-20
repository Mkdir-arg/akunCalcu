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

### FIX-004 — Deploy web desacoplado de migraciones para evitar caídas por healthcheck
**Fecha**: 2026-05-20
**Reportado por**: Usuario
**Severidad**: Alta
**Feature afectada**: Deploy Railway / módulo core

**Síntoma**: El servicio `web` podía quedar fuera de línea en Railway cuando el arranque ejecutaba migraciones o creación de superusuario antes de exponer Gunicorn, lo que hacía fallar el healthcheck y dejaba el dominio público en fallback.
**Causa raíz**: El contenedor ataba el ciclo de vida del proceso web a tareas administrativas dependientes de MySQL. Si la base demoraba en responder o las migraciones tardaban demasiado, Railway mataba el deploy por healthcheck aunque la app en sí estuviera correcta.
**Solución**: Se hizo opcional la ejecución de migraciones y la creación de superusuario al arranque mediante variables de entorno. En producción Railway el servicio puede iniciar rápido y las tareas administrativas pasan a correrse de forma controlada, sin tocar la base de datos ni bloquear el healthcheck.
**Archivos modificados**: `entrypoint.sh`, `.env.example`

### FIX-003 — Reporte de cobranzas: total USD faltante en resumen
**Fecha**: 2026-05-17
**Reportado por**: Usuario
**Severidad**: Media
**Feature afectada**: Módulo comercial / reporte de cobranzas

**Síntoma**: Al filtrar el reporte de cobranzas por moneda USD, el listado mostraba correctamente los movimientos en dólares y el total convertido en pesos, pero el resumen superior no mostraba el total agregado en USD.
**Causa raíz**: La vista `reportes_cobranzas` contaba movimientos con `monto_usd` y los listaba en el detalle, pero no agregaba un `total_usd` en `reporte_data['cobranzas']`. El template solo disponía del total en ARS.
**Solución**: Se agregó la suma de `monto_usd` en la vista, se mostró el total USD en los bloques “Total Cobranza (ARS)” y “Total en pesos”, y se ampliaron los tests del reporte para cubrir el agregado general y el filtro solo USD.
**Archivos modificados**: `akuna_calc/comercial/views.py`, `akuna_calc/comercial/templates/comercial/reportes/reportes_cobranzas.html`, `akuna_calc/comercial/tests.py`

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
