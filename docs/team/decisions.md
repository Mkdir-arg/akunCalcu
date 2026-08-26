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

## ADR-018: Los revestimientos viven en el catálogo de vidrios, no en un modelo aparte

**Fecha**: 2026-08-18 · **Estado**: Aceptada · **Reemplaza parcialmente**: ADR-016 (punto del catálogo de materiales ciegos)

**Contexto**: ADR-016 creó `MaterialCiego` como catálogo propio para el relleno de las secciones
ciegas. Nunca se puso en servicio: su ABM no tenía link desde ningún menú, el catálogo no se cargó y
la migración que crea la tabla quedó sin aplicar mucho tiempo, así que en producción el botón "Ciego
(chapa/panel)" ofrecía una lista vacía. Además obligaba a mantener dos ABMs y dos claves distintas
(`Vidrio.codigo` string vs `MaterialCiego.id` entero) para alimentar dos selectores del mismo editor.

**Decisión**: Los revestimientos pasan a ser registros del catálogo de vidrios, distinguidos por un
campo `Vidrio.tipo` (`vidrio` / `revestimiento`). Un solo catálogo, un solo ABM, una sola clase de
clave. `MaterialCiego` deja de tener consumidores.

**Alternativa descartada**: que ambos convivan (el selector de ciego uniendo revestimientos y
materiales ciegos). Se descartó porque el campo `tipo` quedaría redundante con el botón Vidrio/Ciego
que ya existía, y seguirían siendo dos ABMs.

**Consecuencias**:
- La sección sigue guardando `tipo: 'ciego'` como discriminador —de él dependen el visor 3D y el
  texto "VIDRIO Y REVESTIMIENTO" del PDF (FIX-023)— pero referencia `codigo` en vez de `id`.
- El calculador y el PDF conservan un **fallback** que resuelve por `id` contra `MaterialCiego` para
  los presupuestos guardados antes del cambio. Por eso **el modelo y la tabla no se borran**:
  eliminarlos exigiría otra migración y mataría el fallback. Se limpian cuando se confirme que no
  queda ningún registro con el formato viejo.
- Quedan sin consumidor `MaterialesCiegosListView`, `MaterialCiegoForm`, `materiales_ciegos_config`
  y sus dos templates. No hay nada visible que retirar de la UI porque nunca tuvieron link.
- Al agregar un campo a un modelo `managed = False`, Django no emite DDL: hay que separar estado y
  schema con `SeparateDatabaseAndState` y escribir el `ALTER TABLE` a mano.

---

## ADR-017: Monitoreo de integraciones — latido positivo en vez de interpretar el silencio
**Fecha**: 2026-08-01
**Estado**: Activo

**Contexto**: Tres incidentes seguidos estuvieron invisibles días (REQ-045 / FEAT-035): el OAuth de
Gmail expiró y el reparto no leyó la casilla **25 horas**; el backup a Drive falló **9 días**; y el
reparto procesaba 1 mail de cada 20 (FIX-020). El instinto era "avisar si un workflow lleva N horas
sin ejecutarse", pero eso no funciona parejo: el trigger del reparto **solo ejecuta cuando entra un
mail**, y un hueco de 24 h puede ser normal — pasó el 27/07 sin nada roto. Peor: cuando la
credencial cayó, n8n **no generó ninguna ejecución de error**, solo líneas en el log del servicio,
que la API REST no expone. Por la API, "no llegaron mails" y "no puedo leer la casilla" son
indistinguibles.

**Decisión**: separar los dos casos y no forzar una sola regla.

1. **Workflows con schedule** → el silencio ES señal: umbral = intervalo + margen (26 h para un cron
   diario). Vive en `WORKFLOWS_VIGILADOS` (`security/health.py`), en código y no en un modelo,
   porque el umbral se deduce del propio cron del workflow.
2. **Workflows con trigger por evento** → el silencio NO es señal, así que **no llevan umbral**. Su
   salud se mide con un **latido**: un workflow de n8n de 3 nodos que cada 15 min lee 1 mail y hace
   `POST /security/salud/api/heartbeat/`. Se exige una señal positiva en vez de interpretar una
   ausencia. El nodo de Gmail **no lleva `onError`**: si el OAuth cae tiene que fallar, porque un
   latido que se manda igual reportaría salud falsa.
3. **Los estados que dependen de un tercero se miden en el tercero.** El backup a Drive se evalúa
   por la última ejecución del workflow, no por el modelo `Backup`: Django lo marca *antes* de que
   n8n suba el archivo, y esa diferencia entre intención y realidad es la que ocultó 9 días de fallas.

**Consecuencias**: una caída se detecta en **45 minutos** en lugar de 25 horas, y como n8n caído
tampoco late, el latido quedó como canario de cualquier caída del servicio (probado el mismo día:
el panel destapó 11 horas de n8n abajo). El costo es un workflow más que mantener y una tabla
(`HeartbeatIntegracion`). Para vigilar una integración nueva por trigger hay que agregarle su
latido: no alcanza con sumarla a la lista de workflows. Queda pendiente el aviso proactivo (fase 2):
el panel hay que ir a mirarlo, y el endpoint JSON existe justamente para que un workflow lo consulte.

---

## ADR-016: Tirantes divisores — relleno por sección + catálogo de materiales ciegos
**Fecha**: 2026-07-27
**Estado**: Activo

**Contexto**: Una abertura puede dividirse con tirantes (travesaños horizontales) en varias secciones, cada una con un material distinto (ej. puerta con vidrio arriba y chapa abajo). El motor de `pricing` cotizaba **un único vidrio** para toda la abertura (`área × precio × cantidad_hojas`) y el único material con precio/m² era `Vidrio`; no había catálogo de chapa/panel (REQ-041 / FEAT-031).

**Decisión**:
1. **Nuevo modelo `MaterialCiego`** (chapa/panel/tablero) como tabla **administrada por Django** (no legacy `managed=False`) con su migración `pricing/0005` — es un catálogo nuevo, sin equivalente histórico.
2. **Relleno por sección**: con tirantes activos, el precio del relleno = Σ (área de cada sección × precio/m² de su material: vidrio o ciego). Cada tirante suma su perfil (longitud = ancho) como cualquier otro perfil, y su peso entra al tratamiento. Sin tirantes, el motor queda **idéntico** (rama de vidrio único).
3. ~~**Alcance v1**: solo divisiones **horizontales**.~~ **Revisado 2026-08-01 (REQ-044 / FEAT-034)**: la orientación es elegible por abertura, `horizontal` (bandas) o `vertical` (columnas) — ver punto 10. Sigue fuera de alcance la **grilla** (filas y columnas a la vez) y el rebaje por sección.
4. **Área bruta de abertura** (revisado 2026-07-29): cada sección cobra `ancho_total × alto_sección`, es decir las secciones suman el m² completo de la abertura **sin aplicar rebaje** (a diferencia del vidrio único, que sí aplica las fórmulas `Ancho-X`). Criterio comercial confirmado: con tirantes se cobra el m² de abertura repartido por material.
5. **Multi-hoja multiplica** (revisado 2026-07-29): las secciones **y** los tirantes se multiplican por `cantidad_hojas` del producto, igual que el vidrio único, asumiendo que cada hoja se divide igual. Antes no multiplicaban y eso subcobraba en correderas.
6. **La cantidad de hojas NO se inyecta en la variable `Cantidad` de las fórmulas** (revisado y **revertido** 2026-07-29): la variable `Cantidad` (alias `hojas`) que reciben las fórmulas de despiece sale del *payload* y ningún cotizador la manda → vale **1**. Se probó cambiarla a `Producto.cantidad_hojas` y se **descartó**: contra un presupuesto real de una **corredera de 2 hojas**, los perfiles de hoja (parante central, lateral, zócalo) salen con cantidad **2** —uno por hoja— evaluando `Cantidad = 1`. O sea que **el despiece ya tiene la cantidad de hojas incorporada** en sus propias fórmulas (cada producto tiene su marco/hoja con el conteo por producto). Inyectar la cantidad de hojas ahí **duplicaría** los perfiles de toda fórmula que use la variable. Las hojas sí multiplican el **relleno** (vidrio único y secciones de tirantes), que es lo que se repite por paño. Diagnóstico de las fórmulas reales: `akuna_calc/diagnostico_hojas.py`.
7. **El color NO entra en el precio del perfil** (evaluado y **descartado** 2026-07-29): el motor busca cada perfil por `(código + color)` y ningún cotizador manda `color_id`, así que toma la primera fila. Se probó derivar el color del **Tratamiento** (que es la terminación/color) y se **descartó**: en el sistema el perfil se cotiza **en crudo** (su `precio_kg`) y el color se cobra en el **Tratamiento**, como `precio_kg × peso total de los perfiles` (verificado en un presupuesto real: tratamiento NEGRO $1.875/kg sobre 9,87 kg). Si además se eligiera la fila del perfil por color, el color se cobraría **dos veces**. El precio del perfil lo define el usuario y ya contempla lo que tiene que contemplar. `Perfil.COD_COLOR` queda como dato informativo del legado.
8. **`Contravidrio` / `Cruce` / `VidrioRepartido` / `Mosquitero` (despiece) son LEGADO, no un faltante de precio** (analizado 2026-07-30): el motor sabe cotizarlos y acepta sus ids (`contravidrio_id`, `cruces_id`, `vidrio_repartido_id`, `mosquitero_id`), pero **ningún cotizador los manda**, así que parecen "componentes sin cobrar". **No lo son**: en este sistema esos ítems se cargan como **Accesorios o Fórmulas de Perfiles del Marco y de la Hoja** (ABM de Marcos / Hojas), y desde ahí ya entran al precio. Verificado en un presupuesto real: el **cruce** aparece como accesorio de hoja (`t93 - CRUCE DE HOJA MODENA`) y el **contravidrio/felpa** como accesorio (`FELPA CON FEAL SEAL`, calculado con las medidas de la hoja 576×1420). Además el **mosquitero** es un **Opcional de Fábrica** (por m²) y el **vidrio repartido** quedó reemplazado por los tirantes (REQ-041). Los despieces `DespiecePerfilesVidrio`, `DespieceInterior` y `DespieceInteriorMosquitero` tienen **0 referencias** en el motor. ⇒ Es **código muerto del legado**, candidato a limpieza (como REQ-036 con el despiece); **no** hay que agregarle selectores al cotizador. Diagnóstico: `akuna_calc/diagnostico_componentes.py`.
9. **Validación y materiales faltantes en el calculador, no sólo en el serializer** (revisado 2026-07-29): `_validar_secciones` (suma de secciones == alto) vive en `PriceCalculator` porque el precio que se cobra se recalcula desde el guardado del ítem, que **no** pasa por el serializer del API. Y un material inexistente o dado de baja lanza `PricingError` en vez de saltearse: saltear la sección la borraba del precio y cobraba de menos (se midió −37 % en un caso real).
4. **Persistencia sin migración en `presupuestos`**: la estructura de tirantes va en `ItemPresupuesto.resultado_json` (`desglose.secciones`) y en el `snapshot_item` (`tirantes`), aditiva y compatible con ítems previos.
10. **Orientación de los tirantes y campo `medida_mm`** (agregado 2026-08-01, REQ-044 / FEAT-034): `tirantes.orientacion` (`horizontal` \| `vertical`) define **los dos ejes a la vez**: qué dimensión reparten las secciones y cuánto mide el perfil del tirante, que son **opuestos** (bandas → reparten el alto, tirante = ancho; columnas → reparten el ancho, tirante = alto). Por eso la orientación **no es una preferencia visual**: cambia el área cotizada. En cada sección, `alto_mm` fue reemplazado por **`medida_mm`** (la medida sobre el eje que se divide): en vertical el nombre viejo mentía, y estos datos quedan guardados para siempre en `resultado_json` / `snapshot_item` y se le muestran al taller en la orden de fabricación. Se descartó reinterpretar `alto_mm` para ahorrar código. **Lectura retrocompatible** en un solo lugar: `medida_seccion()` cae a `alto_mm` y `orientacion_tirantes()` asume `horizontal` cuando falta el dato, así que los ítems anteriores conservan precio y dibujo sin migrar nada. La elección de ejes vive en `ejes_tirantes()` + `PriceCalculator._cotizar_tirantes()` (kwargs obligatorios) porque un ancho/alto cruzado ahí cotiza mal en silencio.

**Consecuencias**: El cotizador cubre aberturas mixtas con precio correcto por área. El catálogo de materiales ciegos se administra desde Fábrica (permiso `fabrica.materiales_ciegos`). El precio de secciones en multi-hoja quedaría subestimado si se forzara ahí — por eso el UI habilita tirantes recién con marco elegido y la doc aclara el alcance. La migración `pricing/0005` debe correrse en todos los entornos.

## ADR-015: Three.js para el visor 3D de aberturas (sin build)
**Fecha**: 2026-07-24
**Estado**: Activo

**Contexto**: El cotizador de presupuestos necesita mostrar un diseño 3D de la abertura según los parámetros ingresados (REQ-038 / FEAT-030). El modal de ítem es React cargado por Babel-in-browser, **sin bundler**.

**Decisión**: Usar **Three.js puro** — no React Three Fiber, que exige bundler — como **módulo ESM estático autocontenido** (`static/js/viewer3d.js`), cargado vía **import map** desde CDN (jsdelivr) y de forma **perezosa** (solo al abrir/usar el modal). El modal lo invoca imperativamente (`window.__loadAkunViewer().then(v => v.mount(container, params))`). La geometría se genera **paramétricamente** (no se usan modelos glTF pre-hechos, que se deforman al escalar a medidas arbitrarias). El clasificador de tipología vive en el backend (`pricing/tipologia.py`) como fuente única de verdad, expuesto por el API de productos.

**Consecuencias**: Three.js queda disponible para 3D en el navegador sin introducir build ni npm, coherente con el patrón React/unpkg. Depende de un CDN (con `.catch` si falla). Si el uso de 3D crece, evaluar self-hostear los módulos de three o migrar a un bundler. **Importante**: los `style={{}}` de JSX no se pueden usar dentro de templates Django (chocan con `{{ }}` del motor de plantillas) → usar clases Tailwind.
