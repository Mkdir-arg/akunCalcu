# Architecture Decision Records (ADRs) — AkunCalcu

> Las decisiones técnicas importantes se registran acá para mantener contexto entre sesiones.

## Formato ADR

```
### ADR-NNN: Título
**Fecha**: YYYY-MM-DD
**Estado**: Activo / Deprecado / Reemplazado por ADR-XXX

**Contexto**: Por qué se tomó esta decisión.
**Decisión**: Qué se decidió.
**Consecuencias**: Qué implica esta decisión.
```

---

## ADR-001: Stack tecnológico inicial
**Fecha**: 2026-03-04
**Estado**: Activo

**Contexto**: Sistema de gestión comercial para una empresa de aberturas.

**Decisión**: Django 4.2 + MySQL 8 + Tailwind CSS + Docker Compose.

**Consecuencias**: El equipo sigue patrones Django estándar (MVT). Todas las nuevas features deben ser apps Django o extensiones de apps existentes.

---

## ADR-003: Design System del frontend
**Fecha**: 2026-03-04
**Estado**: Activo

**Contexto**: Para mantener consistencia visual a medida que el proyecto crece, se necesita una referencia del estilo de la aplicación.

**Decisión**: El design system está documentado en `docs/team/design-system.md`. Todo template nuevo debe seguirlo. Las librerías disponibles son Tailwind CSS, FontAwesome 6.4.0, jQuery 3.6.0, Select2 4.1.0 y SweetAlert2 11 — ya incluidas en `core/base.html`. No se agregan librerías nuevas sin un ADR.

**Consecuencias**: Cualquier cambio de UI debe referenciar `design-system.md`. Si se necesita un patrón nuevo, se documenta ahí.

---

## ADR-002: Apps Django del proyecto
**Fecha**: 2026-03-04
**Estado**: Activo

**Decisión**: El proyecto tiene 5 apps: `core` (auth/home), `productos` (CRUD + calculadora), `comercial` (ventas/gastos/clientes), `facturacion` (facturación electrónica), `usuarios` (gestión de usuarios staff).

**Consecuencias**: Cualquier nueva funcionalidad debe evaluarse si encaja en una app existente o requiere una nueva app.

---

## ADR-004: App pedidos para integración con Telegram
**Fecha**: 2026-03-04
**Estado**: Activo

**Contexto**: Se implementó un flujo de pedidos por voz via Telegram. La funcionalidad es suficientemente distinta de `comercial` (no tiene precio, cliente, ni factura) como para justificar una app separada.

**Decisión**: Nueva app `pedidos` con modelos `PedidoTelegram` e `ItemPedidoTelegram`. Los pedidos por voz se guardan con descripción libre (no FK a `Producto`) ya que el texto transcripto no garantiza coincidencia exacta con productos del catálogo. La autenticación entre n8n y Django se hace via header `X-Bot-Secret` (variable de entorno `TELEGRAM_BOT_SECRET`).

**Consecuencias**: El estado del pedido (pendiente/confirmado/cancelado) se guarda en Django, no en n8n — esto simplifica el workflow y hace el sistema resiliente a reinicios de n8n.

## ADR-006: PDF via HTML de impresión (sin librería externa)
**Fecha**: 2026-03-11
**Estado**: Activo

**Contexto**: El módulo de presupuestos requiere generar un PDF para entregar al cliente. Las opciones eran: weasyprint, reportlab, xhtml2pdf (librerías Python) o una vista HTML optimizada para impresión.

**Decisión**: Usar un template HTML dedicado (`presupuestos/pdf.html`) con estilos `@media print` y `@page`. No extiende `base.html`. El usuario abre la vista en nueva pestaña y usa la función de impresión del browser para guardar como PDF.

**Consecuencias**: Sin dependencias extra. El resultado visual es controlado 100% con HTML/CSS. Si en el futuro se necesita generación server-side (adjuntar PDF a un email), se deberá agregar weasyprint y crear un nuevo ADR.

---

## ADR-007: Snapshot descriptivo para PDFs de presupuestos
**Fecha**: 2026-05-04
**Estado**: Activo

**Contexto**: El PDF de presupuestos necesita mostrar una descripción comercial construida con labels legibles de modelos legacy (`Marco`, `Producto`, `Línea`, `Extrusora`, `Vidrio`, `Tratamiento`, opcionales). Reconstruir esos textos en cada render hace que los PDFs históricos dependan de catálogos que pueden cambiar y hubiera empujado cambios de modelo innecesarios.

**Decisión**: Guardar un snapshot descriptivo por ítem en `ItemPresupuesto.resultado_json["snapshot_item"]` al momento de crear el ítem. Ese snapshot incluye labels seleccionados, una narrativa ya armada, un resumen técnico y la metadata mínima para recomponer el texto. El PDF consume ese snapshot y solo usa fallback al desglose legacy para presupuestos anteriores.

**Consecuencias**: No se requieren migraciones. Los presupuestos nuevos mantienen estabilidad histórica aunque cambien los nombres del catálogo. Cualquier evolución futura del PDF debe preservar compatibilidad con `snapshot_item` y con el fallback legacy.

---

## ADR-008: Registro central de permisos por nombre de ruta
**Fecha**: 2026-05-09
**Estado**: Activo

**Contexto**: Los módulos visibles en el sidebar y las rutas reales del sistema no coinciden uno a uno con las apps Django. Hay subsecciones repartidas entre `comercial`, `pricing`, `plantillas`, `productos`, `security` y `configuracion`, además de endpoints compartidos entre `Cotizador` y `Presupuestos`.

**Decisión**: Centralizar la autorización en `usuarios/access_control.py` con un catálogo de módulos/opciones y un mapa por `namespace:url_name`. El sidebar, la redirección inicial luego del login y el middleware de bloqueo por URL consumen esa misma fuente de verdad. El `auth_user` no se modifica; la asignación se guarda en `PerfilAccesoUsuario` y el rol `Admin` se materializa en `RolSistema`.

**Consecuencias**: El menú lateral y el acceso real quedan alineados. Cada nueva ruta que deba quedar protegida debe registrarse en el catálogo central. Se mantiene `is_staff` como compatibilidad transitoria para vistas legacy que todavía no migraron a un chequeo explícito por permiso.

---

## ADR-009: Backups automatizados con n8n + endpoint Django streaming
**Fecha**: 2026-05-24
**Estado**: Activo

**Contexto**: Tras HFX-001 quedó claro que los backups guardados en `/app/backups/` del contenedor son efímeros (Railway recicla el filesystem en cada deploy/reinicio). Se necesitaba un respaldo externo confiable, automatizado y resistente a reinicios. Las opciones eran: (a) `django-crontab`/Celery dentro de Django, (b) cron del host Railway, (c) usar n8n que ya está en la infraestructura del proyecto.

**Decisión**: 
1. **Cron en n8n, no en Django**: Schedule Trigger diario a 00:00 hora Argentina (UTC-3) llama a un endpoint Django que devuelve el dump SQL como respuesta binaria, y n8n lo sube a Google Drive (`Backups AkunCalcu/`). Evita instalar `django-crontab`/Celery solo para este caso. n8n maneja timezone, retries y errores visualmente.
2. **`StreamingHttpResponse` envolviendo `subprocess.Popen(mysqldump)`**: el endpoint streamea el stdout del `mysqldump` directo al response sin cargar el dump en RAM, lo que permite soportar dumps grandes en contenedores con memoria limitada.
3. **Auth por header `X-Bot-Secret`**: secret separado del de Telegram (`BACKUP_BOT_SECRET` ≠ `TELEGRAM_BOT_SECRET`) para poder rotarlo independientemente. El path `/security/backups/api/` se exime de `SecurityMiddleware` (vía `SECURITY_EXEMPT_PREFIXES`) y de `AuditMiddleware.EXCLUDED_PATHS` para no llenar `AuditLog` con la cron diaria.
4. **`storage_location` como string corto en el modelo `Backup`**: solo dos valores hoy (`local`, `drive`), con badge "Auto - Drive" en el listado. Si crece a más destinos (S3, Dropbox, etc.) se promoverá a `choices` formal o tabla.

**Consecuencias**: El sistema queda con respaldo externo diario sin acoplarse a Django para cron. Si en el futuro se quiere trazabilidad de las corridas, conviene loguearlas explícitamente desde la view (no via middleware, ya está exenta). Cualquier nuevo destino de backup debe respetar el contrato del endpoint (header secret + streaming).

---

## ADR-011: Columnas nuevas en tablas legacy `managed=False` vía RunSQL + state_operations
**Fecha**: 2026-06-27
**Estado**: Activo

**Contexto**: RF-015/FEAT-016 necesitó agregar la columna `terciarizado` al modelo `Producto`, que mapea a la tabla legacy `productos` con `managed=False`. Django no gestiona el esquema de modelos `managed=False`, por lo que un `AddField` normal queda como no-op a nivel DDL y la columna nunca se crea en la base.

**Decisión**: Para agregar columnas a una tabla legacy `managed=False` se usa una migración con `migrations.RunSQL` que ejecuta el `ALTER TABLE ... ADD COLUMN` explícito (con `reverse_sql` para revertir), envolviendo los `migrations.AddField` correspondientes en `state_operations` para mantener alineado el estado de migraciones de Django con los campos del modelo. Los campos se agregan también al modelo con su `db_column`.

**Consecuencias**: La migración debe ejecutarse y verificarse en TODOS los entornos (docker local, Railway, pythonanywhere), porque el esquema legacy puede divergir entre ellos. Si una columna ya existe en algún entorno, el `ALTER` falla y hay que saltear esa migración con `--fake` allí. Ver [[deploy_migraciones_railway]].

---

## ADR-014: Reparto round-robin de solicitudes decidido en Django, no en n8n
**Fecha**: 2026-07-18
**Estado**: Activo

**Contexto**: FEAT-025 (REQ-037) automatiza el reparto de pedidos de presupuesto que llegan por email. n8n toma el mail y lo empuja a AkunCalcu. La decisión de "a qué vendedor le toca" (round-robin equitativo) podía vivir en n8n (guardando el puntero en una Data Table del propio n8n) o en Django (puntero en la base). Dos mails casi simultáneos podrían recibir el mismo vendedor si el puntero no se actualiza de forma atómica.

**Decisión**: El round-robin lo resuelve Django. El puntero del último vendedor asignado se guarda en un singleton `ConfiguracionSolicitudes` (pk=1) y `asignar_siguiente_vendedor()` lo toma con `select_for_update()` dentro de `transaction.atomic`, de modo que dos solicitudes concurrentes no reciben el mismo vendedor. El pool son los usuarios con `perfil_acceso.rol.codigo == 'vendedor'` activos y con email cargado. n8n queda como transporte (Gmail → IA → HTTP), sin lógica de negocio. La autenticación del endpoint usa `X-Bot-Secret` con un secret dedicado `SOLICITUDES_BOT_SECRET`, y la creación es idempotente por `gmail_thread_id`.

**Consecuencias**: El reparto es auditable y consistente aunque n8n reintente o se reinicie (el estado no vive en el filesystem efímero de n8n, a diferencia del incidente de credenciales del 02-03/07). El WhatsApp del vendedor reusa `NumeroAutorizado` (FK en el perfil) en lugar de duplicar números. El rol `vendedor` se siembra por migración porque no existía. Si el pool queda vacío, la solicitud entra en estado `sin_asignar` y se reasigna a mano desde el panel.

---

## ADR-013: Eliminación del módulo de despiece de `plantillas`
**Fecha**: 2026-07-07
**Estado**: Activo

**Contexto**: La app `plantillas` nació como calculadora de despiece (medidas de corte): plantillas configurables, motor de fórmulas propio (Shunting Yard con MIN/MAX/IF/unidades), pantalla Calcular, Historial y pedidos con ítems de despiece. El módulo quedó obsoleto sin uso operativo, y Pedidos de Fábrica pasa a ser el contenedor de las Órdenes de Fabricación (REQ-035). En la misma app conviven los **Opcionales de Fábrica**, que NO son despiece: los consume el cotizador de `pricing` (mosquitero/premarco) para los presupuestos de aluminio.

**Decisión**: Se eliminó el mundo despiece completo — modelos `ProductoPlantilla`/`CampoPlantilla`/`CalculoEjecucion`/`PedidoFabricaItem`/`PedidoFabricaFila` con sus datos (migración `0014`), 16 views, 8 templates, `formula_engine`, `seed_plantillas`, `templatetags` y los permisos `despiece.calcular/plantillas/historial`. Se conservó `PedidoFabrica` (cabecera + FK `presupuesto` de FEAT-019) y todo el mundo Opcionales. `/plantillas/` redirige a pedidos. El code de permiso `despiece.pedidos` se mantuvo para no invalidar roles guardados, y la app conserva el nombre `plantillas` (renombrarla implicaba migraciones invasivas sin beneficio funcional).

**Consecuencias**: Los datos históricos del despiece se pierden al aplicar la migración (confirmado por el usuario). Toda funcionalidad futura de fábrica se construye sobre `PedidoFabrica` + Órdenes de Fabricación (REQ-035). El único motor de fórmulas vigente en el sistema es el del cotizador (`pricing/services/formula_parser.py`); el motor con MIN/MAX/IF ya no existe.

---

## ADR-012: Confirmar presupuesto crea Venta y PedidoFabrica programáticamente en una transacción
**Fecha**: 2026-07-07
**Estado**: Activo

**Contexto**: REQ-034 pide que al confirmar un presupuesto se registre la seña cobrada y se generen automáticamente la venta (`comercial`) y el pedido de fábrica (`plantillas`). Existía la FK `Presupuesto.venta` (migración 0002) declarada pero nunca usada, y `PedidoFabrica` no tenía relación con presupuestos (su `cliente` es texto libre). Opciones: (a) redirigir al form de venta precargado y después al de pedido (dos pasos manuales), (b) crear ambos registros programáticamente en la view de cambio de estado, con un popup que capture la seña.

**Decisión**: Se eligió (b). `cambiar_estado` deriva a `_procesar_confirmacion()` cuando el estado destino es `confirmado`: valida la seña (obligatoria, > 0, ≤ total; en USD si el presupuesto es PVC usando su cotización de cabecera — ADR-010 —, en pesos si es aluminio) y dentro de `transaction.atomic()` crea la Venta replicando la conversión del `VentaForm` (`ARS = USD × cotización`, quantize 0.01), crea el `PedidoFabrica` como cabecera sin ítems (número `PF-XXXX` buscando el primer libre) y setea `Presupuesto.venta` + estado. La seña viaja como campo extra en el mismo POST del formulario de estado (popup SweetAlert2 intercepta el submit); sin URLs nuevas. Se agregó la FK nullable `PedidoFabrica.presupuesto` (SET_NULL) para trazabilidad y navegación.

**Consecuencias**: La confirmación es la única fuente de creación automática; la carga manual de ventas y pedidos sigue intacta. Los ítems del presupuesto NO se traducen al pedido de fábrica (las plantillas de despiece no mapean 1:1 con los ítems del cotizador): fábrica carga el despiece sobre la cabecera generada. La confirmación sigue siendo irreversible por UI: deshacerla implica borrar a mano la venta y el pedido en cada módulo. Si dos confirmaciones simultáneas chocaran en el número PF único, la transacción hace rollback completo (sin datos inconsistentes) y se reintenta.

---

## ADR-010: Cotización USD de presupuestos PVC a nivel de cabecera
**Fecha**: 2026-06-19
**Estado**: Activo

**Contexto**: Los presupuestos en PVC se cotizan siempre en dólares, pero el sistema necesita seguir calculando todo en pesos como base común (recargos, IVA, KPIs). Antes existía un checkbox "valor en dólares" opcional por ítem con su propia cotización, que solo se usaba para convertir a pesos al guardar — nunca se mostraba en PDF ni listado, y permitía cotizaciones distintas entre ítems del mismo presupuesto.

**Decisión**: Se agregó `Presupuesto.cotizacion_usd` como campo único de cabecera (obligatorio si `tipo_material = pvc`, validado en `PresupuestoForm.clean()`). El monto en pesos sigue siendo la fuente de verdad (`total`, `precio_unitario`, etc., sin cambios); el USD se deriva siempre en el momento de mostrarlo (`monto_ars / cotizacion_usd`) vía métodos `get_*_usd()` en `Presupuesto` e `ItemPresupuesto`, nunca se persiste un monto en USD por ítem. Se eliminó el checkbox por ítem y el alta de ítems PVC se bloquea si el presupuesto no tiene cotización configurada.

**Consecuencias**: Si se cambia la cotización de un presupuesto PVC después de cargar ítems, el USD mostrado de todos los ítems se recalcula automáticamente (es el comportamiento esperado, no un bug). Los presupuestos en Aluminio no se ven afectados. Cualquier nuevo lugar que muestre montos de un presupuesto PVC debe usar los getters `_usd` en lugar de leer `precio_unitario`/`total` directamente, para no mezclar monedas.

---

## ADR-005: Chart.js para gráficos en detalle de cliente
**Fecha**: 2026-03-06
**Estado**: Activo

**Contexto**: La página de detalle de cliente requiere gráficos (barras y donut). Las librerías disponibles en base.html no incluyen ninguna de gráficos.

**Decisión**: Usar Chart.js 4.4.0 via CDN, cargado únicamente en el bloque `extra_js` del template `clientes/detail.html`. No se agrega a `base.html` para no impactar el peso de todas las páginas.

**Consecuencias**: Si se necesitan gráficos en otras páginas, se puede reutilizar el mismo CDN en sus respectivos `extra_js`. Si el uso crece, evaluar agregar a `base.html` o instalar via npm.

---

## ADR-015: Three.js para el visor 3D de aberturas (sin build)
**Fecha**: 2026-07-24
**Estado**: Activo

**Contexto**: El cotizador de presupuestos necesita mostrar un diseño 3D de la abertura según los parámetros ingresados (REQ-038 / FEAT-030). El modal de ítem es React cargado por Babel-in-browser, **sin bundler**.

**Decisión**: Usar **Three.js puro** — no React Three Fiber, que exige bundler — como **módulo ESM estático autocontenido** (`static/js/viewer3d.js`), cargado vía **import map** desde CDN (jsdelivr) y de forma **perezosa** (solo al abrir/usar el modal). El modal lo invoca imperativamente (`window.__loadAkunViewer().then(v => v.mount(container, params))`). La geometría se genera **paramétricamente** (no se usan modelos glTF pre-hechos, que se deforman al escalar a medidas arbitrarias). El clasificador de tipología vive en el backend (`pricing/tipologia.py`) como fuente única de verdad, expuesto por el API de productos.

**Consecuencias**: Three.js queda disponible para 3D en el navegador sin introducir build ni npm, coherente con el patrón React/unpkg. Depende de un CDN (con `.catch` si falla). Si el uso de 3D crece, evaluar self-hostear los módulos de three o migrar a un bundler. **Importante**: los `style={{}}` de JSX no se pueden usar dentro de templates Django (chocan con `{{ }}` del motor de plantillas) → usar clases Tailwind.
