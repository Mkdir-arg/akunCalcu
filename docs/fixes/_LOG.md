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

### FIX-006 — Fórmulas de perfiles de hojas/marcos se corrompen o no persisten con autoguardado concurrente
**Fecha**: 2026-06-12
**Reportado por**: Usuario + Romina
**Severidad**: Alta
**Feature afectada**: Módulo pricing / configuración de hojas y marcos

**Síntoma**: En `/pricing/config/hojas/53/editar/` las fórmulas de perfiles aparecían "cambiadas todas y varias veces" (filas duplicadas/alteradas) y, en otros casos, un guardado parecía no persistir: el usuario editaba una fórmula, salía y al volver la veía igual que antes.
**Causa raíz**: El guardado de fórmulas/accesorios hacía borrar-todo + recrear fila por fila **sin transacción**, asignando el `id` a mano con `max_id + 1` por cada fila (tablas legacy `managed=False` sin PK autoincremental). Combinado con el autoguardado que dispara un POST en cada tecla (debounce 900ms) y con más de un usuario/pestaña editando, dos guardados solapados calculaban el mismo `max_id` y colisionaban en la PK: el que perdía la carrera fallaba a mitad de camino (delete ya ejecutado, creates incompletos) dejando filas perdidas, duplicadas o a medias. El mismo patrón existía en 8 lugares (hojas y marcos: fórmulas y accesorios, vía AJAX y submit normal).
**Solución**: Se creó el helper `_reemplazar_filas_despiece()` que ejecuta el borrar+recrear dentro de `transaction.atomic()`, serializa guardados concurrentes sobre la misma entidad con `select_for_update()` sobre el padre, calcula el `max_id` una sola vez usando `bulk_create`, y reintenta hasta 3 veces ante colisión de id con guardados de otras entidades. Se migraron los 8 puntos de guardado a este helper. En el frontend (`hoja_form.html` y `marco_form.html`) se agregó `ejecutarGuardadoSerializado()` para que nunca haya dos autosaves en vuelo a la vez (si llega uno mientras otro corre, se encola y se ejecuta al terminar).

**Extensión a todo el sistema** (mismo día): se aplicó el mismo patrón en todos los puntos restantes con guardados delete+recrear o ids manuales:
- `vidrio_edit` (relaciones vidrio↔hojas): atomic + lock sobre el vidrio + `bulk_create`.
- `plantillas/views_opcionales.py` (fórmulas, accesorios y relaciones de opcionales): atomic + `select_for_update()` sobre el opcional + `bulk_create` (accesorios y relaciones no tenían transacción).
- Altas de entidades legacy con id manual (`Extrusora`, `Linea`, `Producto`, `Marco`, `Hoja`, `Interior`, `Tratamiento`): nuevo helper `_guardar_nuevo_con_id()` con atomic + reintento ante colisión de id.
- Guard anti-solape `ejecutarGuardadoSerializado()` también en `vidrio_form.html` y `opcional_form.html`.

**Endurecimiento contra pérdida silenciosa de filas** (2026-06-12, tras reporte de fórmulas que "se pierden al día siguiente"): el guardado descartaba sin avisar las filas incompletas, lo que borraba fórmulas en dos escenarios reales: (a) el usuario borra temporalmente el contenido de un campo y el autosave dispara a los 900ms; (b) la fórmula referencia un perfil que quedó fuera del catálogo filtrado (bloqueado o de otro tipo) y el select renderiza vacío. Cambios:
- Backend (hojas y marcos, AJAX y POST normal): una fila *a medio completar* ahora **aborta el guardado completo sin tocar la base** y devuelve error indicando la fila (`Fila N incompleta... No se guardó nada`). Las filas totalmente vacías (recién agregadas) se ignoran como antes. `marco_formulas_guardar` además no validaba nada y creaba filas basura — ahora valida igual.
- Frontend (`hoja_form.html`, `marco_form.html`): si una fórmula referencia un perfil fuera del catálogo, el select lo conserva como opción "(fuera de catálogo)" en vez de quedar vacío — cubre también el caso en que el fetch del catálogo de perfiles falla en marcos.
- `opcional_form.html` ya estaba protegido: su backend rechaza filas incompletas con error 400 sin tocar datos.

**Archivos modificados**: `akuna_calc/pricing/config_views.py`, `akuna_calc/plantillas/views_opcionales.py`, `akuna_calc/pricing/templates/pricing/config/hoja_form.html`, `akuna_calc/pricing/templates/pricing/config/marco_form.html`, `akuna_calc/pricing/templates/pricing/config/vidrio_form.html`, `akuna_calc/plantillas/templates/plantillas/opcional_form.html`

### FIX-005 — Opcional mosquitero multiplica su precio al agregarse al presupuesto
**Fecha**: 2026-06-08
**Reportado por**: Usuario
**Severidad**: Alta
**Feature afectada**: FEAT-005 (presupuestos) / módulo pricing

**Síntoma**: Al calcular un ítem en vivo ("Calcular precio"), el opcional tipo mosquitero se calculaba bien (1 sola fórmula, ej. `1 x 0.9m2 x $41.999,99/m2 = $37.799,99`). Pero al **agregar el ítem al presupuesto**, el mismo mosquitero aparecía con muchas líneas repetidas (una por producto del catálogo) y el precio quedaba multiplicado (ej. $680.399,84 en vez de $37.799,99). Ocurría con cualquier tipo de mosquitero.
**Causa raíz**: El cálculo del mosquitero filtra las `FormulaOpcional` por el producto seleccionado (`formulas.filter(perfil=str(producto_id))` en `calculator.py`), pero solo si recibe `ProductoId` en las variables. El formulario de guardado (`detalle.html`) no incluía un input oculto `producto_id`, por lo que `agregar_item` armaba el `config` sin ese dato. Sin `producto_id`, el filtro se salteaba y se sumaban **todas** las fórmulas del opcional (una por cada producto). El cálculo en vivo no tenía el bug porque su endpoint API sí envía `producto_id`.
**Solución**: Se agregó el input oculto `producto_id` al formulario de guardado, se vuelca `config.producto_id` al enviarlo, y `agregar_item` ahora lo lee dentro del `config` que pasa a `calcular_precio`. Los ítems ya guardados con el cálculo erróneo deben borrarse y volver a agregarse para recalcularse.
**Archivos modificados**: `akuna_calc/presupuestos/templates/presupuestos/detalle.html`, `akuna_calc/presupuestos/views.py`

### FIX-004 — Deploy web desacoplado de migraciones para evitar caídas por healthcheck
**Fecha**: 2026-05-20
**Reportado por**: Usuario
**Severidad**: Alta
**Feature afectada**: Deploy Railway / módulo core

**Síntoma**: El servicio `web` podía quedar fuera de línea en Railway cuando el arranque ejecutaba migraciones o creación de superusuario antes de exponer Gunicorn, o cuando esperaba MySQL indefinidamente, lo que hacía fallar el healthcheck y dejaba el dominio público en fallback.
**Causa raíz**: El contenedor ataba el ciclo de vida del proceso web a tareas administrativas dependientes de MySQL y además bloqueaba el arranque con un wait loop sin límite. Si la base demoraba en responder o las migraciones tardaban demasiado, Railway mataba el deploy por healthcheck aunque la app en sí estuviera correcta.
**Solución**: Se hizo opcional la ejecución de migraciones y la creación de superusuario al arranque mediante variables de entorno, y se agregó un timeout configurable para la espera de MySQL. En producción Railway el servicio puede iniciar rápido y las tareas administrativas pasan a correrse de forma controlada, sin tocar la base de datos ni bloquear el healthcheck.
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
