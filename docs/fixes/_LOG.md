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

### FIX-014 — No se puede cargar un producto: el select de Línea queda bloqueado/vacío para cualquier extrusora
**Fecha**: 2026-06-29
**Reportado por**: Romina (vía Matu)
**Severidad**: Alta (bloquea el alta de productos en producción)
**Feature afectada**: Módulo `pricing` — alta/edición de productos (`/pricing/config/productos/nuevo/`)

**Síntoma**: Al crear un producto, después de elegir la extrusora el desplegable de **Línea** quedaba bloqueado/vacío y no dejaba seleccionar — con **cualquier** extrusora (no solo "terciarizado"). Antes funcionaba.
**Causa raíz (real)**: Desde FEAT-011 (commit `e1dbb44`, 2026-05-17) `base.html` aplica **Select2** a todos los `<select>`. Select2 dispara el evento `change` mediante **jQuery `.trigger('change')`**, que **NO ejecuta los listeners registrados con `addEventListener('change')` nativo**. Los forms de config (`producto_form`, `marco_form`, `hoja_form`) bindeaban la cascada extrusora→línea(→producto→marco) justamente con `addEventListener('change')`, así que al elegir la extrusora **nunca corría `cargarLineas`** y la Línea quedaba vacía. Por eso "antes funcionaba" (antes de FEAT-011 la extrusora era un `<select>` nativo y el change nativo sí disparaba). Secundariamente, tras rellenar la Línea por JS había que **refrescar el widget de Select2** o no mostraba las opciones.
**Solución**: (1) Se bindean los `change` de la cascada con **jQuery (`$(el).on('change', ...)`)**, que capta tanto el change nativo como el de Select2; (2) se refresca Select2 tras rellenar cada select dependiente (`reinitAkunSelect2`/`refreshAkunSelect2`). Cambio solo de template/JS, sin tocar modelos ni vistas. Se aplicó a los tres forms de config porque compartían el mismo bug latente. El cotizador no está afectado (usa componentes React, no Select2).
**Archivos modificados**: `akuna_calc/pricing/templates/pricing/config/producto_form.html`, `marco_form.html`, `hoja_form.html`
**Nota**: Para productos **terciarizados**, la extrusora "terciarizado" debe tener al menos una **línea** para que aparezca en el select (y para que el producto se vea luego en el cotizador, que navega extrusora → línea → producto). Este fix desbloquea el alta con cualquier extrusora; si "terciarizado" no tiene línea, hay que crearle una (pendiente FEAT-016).

### FIX-013 — Lista de presupuestos: quitar orden por columnas, fijar orden por más nuevo y agregar columna de creación
**Fecha**: 2026-06-29
**Reportado por**: Usuario
**Severidad**: Baja (mejora de UX)
**Feature afectada**: Módulo `presupuestos` — listado `/presupuestos/`

**Síntoma**: Al tocar los títulos de las columnas la tabla se reordenaba (`?sort=...&dir=...`). El usuario quería un orden fijo (el presupuesto más nuevo arriba) y ver la fecha de creación de cada presupuesto.
**Causa raíz**: La vista `lista` implementaba ordenamiento dinámico por columna y el template renderizaba los headers como links con íconos de orden. No existía columna de fecha de creación.
**Solución**: Se quitó la lógica de `sort_fields`/`sort`/`dir` de la vista; ahora el queryset siempre ordena por `-created_at` (más nuevo arriba). Los headers pasaron a texto plano (sin links ni íconos). Se agregó la columna "Creacion" con `created_at|date:"d/m/Y"` entre Estado y Vencimiento (`colspan` del estado vacío 7 → 8). Tests: reemplazo de los tests de orden por columna por uno de orden por defecto + uno que verifica que parámetros de orden se ignoran sin romper.
**Archivos modificados**: `akuna_calc/presupuestos/views.py`, `akuna_calc/presupuestos/templates/presupuestos/lista.html`, `akuna_calc/presupuestos/tests.py`

### FIX-012 — Permitir editar el código (nombre) de un vidrio — RF-018
**Fecha**: 2026-06-27
**Reportado por**: Usuario (RF-018)
**Severidad**: Baja (mejora operativa)
**Feature afectada**: Módulo pricing / configuración de vidrios

**Síntoma**: No se podía cambiar el código con el que fue cargado un vidrio (el identificador que figura en la lista y la URL, ej. "dvh 1"); para estandarizar nombres había que eliminar el vidrio y volver a crearlo. La descripción y el precio ya eran editables; el código no.
**Causa raíz**: El código es la PK del modelo `Vidrio` (tabla legacy `managed=False`) y `VidrioEditForm` lo excluía a propósito. Renombrar una PK no se puede hacer con `obj.save()` (Django insertaría una fila nueva) y, además, las tablas que la referencian (`vidrio_hojas.vidrio_codigo` y `despiece_perfiles_vidrios.Idvidrio`) usan FK sin constraint en base, por lo que la base no cascadea el cambio.
**Solución**: Se agregó el helper `_renombrar_codigo_vidrio()` que, dentro de una transacción, actualiza por SQL crudo parametrizado las tres tablas (`vidrios`, `vidrio_hojas`, `despiece_perfiles_vidrios`). `vidrio_edit` ahora lee `codigo_nuevo` del POST, valida que el nuevo código no exista ya y ejecuta el rename. El template de edición incluye un input "Código" con aviso de que el cambio actualiza también las relaciones. Test que verifica el repunte de las tres tablas con los parámetros correctos.
**Archivos modificados**: `akuna_calc/pricing/config_views.py`, `akuna_calc/pricing/templates/pricing/config/vidrio_form.html`, `akuna_calc/pricing/tests.py`

### FIX-011 — Detalle de reporte de proveedores: quitar línea de fecha repetitiva — RF-016
**Fecha**: 2026-06-27
**Reportado por**: Usuario (RF-016)
**Severidad**: Baja (mejora UX)
**Feature afectada**: Módulo comercial / detalle del reporte de proveedores

**Síntoma**: En el detalle del reporte de proveedores, el listado de movimientos mostraba una fila separadora "Fecha: dd-mm-aaaa" antes de cada grupo de fecha, información redundante porque cada fila ya muestra la fecha en su propia columna (más las columnas Año y Mes).
**Causa raíz**: El template usaba un bloque `{% ifchanged movimiento.fecha %}` que insertaba una fila a todo el ancho con la fecha, duplicando el dato de la columna "Fecha".
**Solución**: Se eliminó el bloque separador `{% ifchanged %}` y se ajustó el subtítulo del asiento ("Cada fecha agrupa sus registros" ya no aplica). La fecha sigue visible en la columna de cada movimiento. Test que verifica la ausencia de la fila "Fecha:" y la presencia de la fecha por fila.
**Archivos modificados**: `akuna_calc/comercial/templates/comercial/reportes/reporte_proveedor_detalle.html`, `akuna_calc/comercial/tests.py`

### FIX-010 — Filtro por dirección del cliente en el listado de ventas — RF-013
**Fecha**: 2026-06-27
**Reportado por**: Usuario (RF-013)
**Severidad**: Baja (mejora operativa, no bug)
**Feature afectada**: Módulo comercial / listado de ventas

**Síntoma**: No se podía filtrar/buscar ventas por la dirección del cliente; el buscador general (`q`) solo cubría pedido, cliente y factura.
**Causa raíz**: `ventas_list` no contemplaba un filtro por `cliente.direccion` (sí tenía uno análogo para `razon_social`).
**Solución**: Se agregó el parámetro `direccion` a `ventas_list` con `filter(cliente__direccion__icontains=...)` y se sumó al contexto. En el template se agregó el input "Dirección" al panel de filtros, se incluyó en las condiciones de panel abierto/badge y se propagó a los 7 links de paginación y ordenamiento para que el filtro persista. Se mantienen intactos todos los filtros existentes.
**Archivos modificados**: `akuna_calc/comercial/views.py`, `akuna_calc/comercial/templates/comercial/ventas/list.html`, `akuna_calc/comercial/tests.py`

### FIX-009 — Reporte de proveedores oculta proveedores desactivados (sus pagos "no impactan") — RF-006
**Fecha**: 2026-06-27
**Reportado por**: Usuario (RF-006)
**Severidad**: Alta
**Feature afectada**: Módulo comercial / reporte de proveedores

**Síntoma**: Pagos/gastos cargados a un proveedor "no impactaban" en el reporte de proveedores: el proveedor y todos sus movimientos desaparecían del listado, y su detalle devolvía 404. Continuación del síntoma de [FIX-002], pero por una causa distinta.
**Causa raíz**: El cálculo de la cuenta corriente (`construir_cuenta_corriente_proveedor`) era correcto — verificado con tests existentes y un nuevo test de reproducción end-to-end (compra + seña + pago en pesos + pago en USD). El problema estaba en la **visibilidad**: `reportes_proveedores`, `reporte_proveedor_detalle`, `exportar_reporte_proveedores_excel` y el dropdown de `ReporteProveedorForm` filtraban por `activo=True`. Al desactivar un proveedor (que conserva sus compras/pagos), quedaba totalmente fuera del reporte aunque tuviera saldo.
**Solución**: Las cuatro consultas ahora incluyen proveedores inactivos **que conserven movimientos** (`annotate(Exists(Compra no eliminada)) + filter(Q(activo=True) | Q(tiene_movimientos=True))`), sin listar los inactivos vacíos. El detalle y la exportación dejan de exigir `activo=True` (siguen excluyendo `deleted_at`). El label "Cuenta activa" del detalle pasó a ser dinámico ("Cuenta inactiva" cuando corresponde). Se agregaron 4 tests de regresión.
**Archivos modificados**: `akuna_calc/comercial/views.py`, `akuna_calc/comercial/forms.py`, `akuna_calc/comercial/templates/comercial/reportes/reporte_proveedor_detalle.html`, `akuna_calc/comercial/tests.py`

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

---

### FIX-008 — Eliminar autosave en pricing/config (reemplazar por guardado manual)
**Fecha**: 2026-06-16
**Severidad**: Alta
**Feature afectada**: Módulo pricing/config

**Síntoma**: Las fórmulas de vidrio (rebaje_alto / rebaje_ancho) en `/pricing/config/hojas/` aparecían con valores NULL en la BD aunque en el frontend se mostraban datos. El autosave se disparaba ante cualquier `input`/`change` con debounce 900ms, causando que campos no terminados de tipear (o no confirmados) sobreescribieran la BD.
**Causa raíz**: El autosave AJAX en `hoja_form.html`, `marco_form.html` y `vidrio_form.html` se activaba por eventos del DOM incluyendo el simple foco en un campo. Los campos vacíos (placeholder) eran enviados como strings vacíos, pisando valores existentes con NULL.
**Solución**: Se eliminó completamente el autosave (timers, event listeners, funciones AJAX guardar*) de los 3 templates. El botón "Guardar" existente ya procesaba fórmulas y accesorios. Se agregó procesamiento de fórmulas de vidrio al POST normal de `hoja_edit`, accesorios al POST normal de `marco_edit`, y relaciones de hojas al POST normal de `vidrio_edit`. La sección de hojas en `vidrio_form.html` se movió dentro del `<form>` principal.
**Archivos modificados**:
- `akuna_calc/pricing/templates/pricing/config/hoja_form.html`
- `akuna_calc/pricing/templates/pricing/config/marco_form.html`
- `akuna_calc/pricing/templates/pricing/config/vidrio_form.html`
- `akuna_calc/pricing/config_views.py`
