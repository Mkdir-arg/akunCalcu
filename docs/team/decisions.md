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

## ADR-030: Optimizador de corte: app propia, FFD determinístico y plan guardado como foto con firma
**Fecha**: 2026-11-10
**Estado**: Activo

**Contexto**: El taller corta los marcos a mano, pedido por pedido, y sobra aluminio. Los datos (medidas, despiece del marco, largo de barra) ya están en `plantillas` y `pricing`. Se pidió una primera etapa solo de marco.

**Decisión**:
- App nueva `optimizador` (modelo `PlanCorte`, migración `0001` que depende de `plantillas/0018`, permiso `fabrica.optimizador`). `ancho_alto` se extrajo a `plantillas/services/medidas.py` para compartirla.
- Algoritmo FFD (First Fit Decreasing): determinístico, rápido, mismo resultado cada vez.
- Se agrupa por perfil + color: marcos de colores distintos no comparten barra.
- El largo de un tramo a 45° es el de la fórmula, punta a punta, sin encastrar ingletes (conservador).
- El último corte de la barra no gasta disco para decidir si entra. El sobrante informado sí lo descuenta: es conservador y puede mostrar hasta 4 mm menos que el físico.
- El plan guarda un snapshot JSON del cálculo y una firma sha1 de las órdenes (medida y abertura). Si la firma actual difiere, el plan figura *Desactualizado*; si no, *Vigente*.
- Guardar es atómico y reintenta el número correlativo ante colisión. Opcionalmente pasa las órdenes de `por_fabricar` a `corte` con `circuito.cambiar_etapa`, que deja el historial.
- Disco y despunte son por plan y recuerdan el último guardado. Largo de barra y recorte mínimo son opcionales (vacío = catálogo).

**Consecuencias**: Una orden con alguna medida no interpretable queda afuera entera, y los pedidos `terminado` se excluyen. No hay stock de recortes, hoja, contravidrio, mosquitero ni travesaños, y no hay envío por WhatsApp. Sin permiso se responde 302 y no 403, porque `RouteAccessMiddleware` redirige en todo el sistema. Si disco y despunte resultan fijos, se pasan a Configuración sin tocar el cálculo.

---

## ADR-029: Novedades del sistema: la GitHub Action arma el borrador con el changelog y la publicación pasa siempre por revisión
**Fecha**: 2026-11-10
**Estado**: Activo

**Contexto**: Se quería una noticia por cada funcionalidad nueva. El repo casi no usa PRs (8 en total, el último en julio de 2026): casi todo entra a `main` por push directo, así que un disparador «se abrió un PR» casi nunca correría. El texto de los commits es técnico, y el contenedor de producción no tiene `docs/` (el Dockerfile copia solo `akuna_calc/`), así que Django no puede leer el changelog, que es donde está el texto para usuarios.

**Decisión**: Una GitHub Action en `push` a `main` corre `.github/scripts/novedad_borrador.py`. El script toma las entradas `## ` agregadas a `docs/team/changelog.md` en el diff del push (ignora un encabezado que reemplaza a otro, porque eso es una errata corregida) y las manda junto con los commits a `POST /novedades/api/borrador/`, con `X-Bot-Secret` = `NOVEDADES_BOT_SECRET`, que es el mismo patrón que backups y salud. Django crea la noticia en borrador, idempotente por SHA, y solo un usuario con acceso total la publica. Lo no leído se calcula con una fecha de última visita por usuario.

**Consecuencias**: El changelog pasa a ser también la fuente de las noticias: escribir bien su entrada ahorra trabajo en la bandeja. Sin los secrets en GitHub la Action no envía nada y no falla. Ante un force-push, cuando el `before` ya no existe, toma solo el último commit. La bandeja no usa `is_staff`, porque en este sistema lo tienen usuarios comunes con permisos heredados.

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

**Extensión (2026-09-04, FEAT-040 / REQ-050)**: la colocación y el recargo por unidad de un
presupuesto PVC se **cargan en US$** en el formulario de Configuración de obra, pero se **guardan en
pesos** (conversión con la cotización de cabecera al validar; al reabrir se muestra pesos ÷ cotización).
Se mantiene la regla: la base y los totales siguen en pesos, los USD se derivan. Los presupuestos
existentes no se migran: sus pesos quedan iguales y se ven como el US$ equivalente.

---

## ADR-005: Chart.js para gráficos en detalle de cliente
**Fecha**: 2026-03-06
**Estado**: Activo

**Contexto**: La página de detalle de cliente requiere gráficos (barras y donut). Las librerías disponibles en base.html no incluyen ninguna de gráficos.

**Decisión**: Usar Chart.js 4.4.0 via CDN, cargado únicamente en el bloque `extra_js` del template `clientes/detail.html`. No se agrega a `base.html` para no impactar el peso de todas las páginas.

**Consecuencias**: Si se necesitan gráficos en otras páginas, se puede reutilizar el mismo CDN en sus respectivos `extra_js`. Si el uso crece, evaluar agregar a `base.html` o instalar via npm.

---

## ADR-028: Croquis de la orden dibujado en el servidor, espejo en Python del dibujo del cotizador
**Fecha**: 2026-11-10
**Estado**: Activo

**Contexto**: El PDF de la Orden de Fabricación lo arma xhtml2pdf en el servidor, que no ejecuta JavaScript. El dibujo de las aberturas (`static/js/abertura-layout.js` + `elevacion.js`) solo corre en el navegador. Las opciones eran generar el PDF en el navegador como el presupuesto (ADR-006), lo que rompe el PDF del pedido completo y el flujo actual; ejecutar el JS en el servidor con Node o un navegador headless, una dependencia pesada en Railway; o portar el dibujo a Python.

**Decisión**: `pricing/elevacion.py` porta `computarLayout` y `svgElevacion` a Python con los mismos nombres y la misma lógica, y devuelve un SVG. El PDF lo embebe como `data:image/svg+xml;base64`, y xhtml2pdf lo rasteriza con svglib, que ya viene con xhtml2pdf 0.2.17. El tamaño del `<img>` se pasa como texto con punto decimal: Django localizado escribe «36,3mm» y xhtml2pdf ignora ese CSS.

**Consecuencias**: El dibujo existe dos veces. Un cambio de símbolos, colores o layout en el JS hay que replicarlo en `pricing/elevacion.py`, y al revés; los docstrings de los dos lados lo avisan, como ya pasaba con el catálogo `APERTURAS` (`pricing/aperturas.py` ↔ JS). svglib no soporta `dominant-baseline` ni `<pattern>`: el texto se centra a mano y el mosquitero va con rayas sueltas.

---

## ADR-027: La orden de fabricación guarda textos para imprimir e IDs del catálogo solo para editar
**Fecha**: 2026-11-10
**Estado**: Activo

**Contexto**: REQ-067 pide elegir la abertura de la orden del catálogo de pricing, con la cascada del cotizador. La orden guarda textos (los imprime el PDF y los copia la precarga) y el catálogo legacy cambia o se bloquea con el tiempo.

**Decisión**:
1. Los textos siguen siendo la fuente de verdad de lo que se fabrica. Se agrega `OrdenFabricacion.seleccion_catalogo` (JSON sin FK) solo para volver a preseleccionar los desplegables.
2. El navegador manda IDs y el servidor (`plantillas/services/abertura_catalogo.py`) valida la cadena con las mismas reglas que `pricing/catalog_views.py` y escribe los textos.
3. Solo se reemplaza lo que el usuario tocó (`cat_cambios`): una orden escrita a mano no se pisa por abrirla y guardar.

**Alternativas descartadas**:
- *FKs al catálogo*: las tablas legacy son `managed=False`, sin integridad, y un ítem bloqueado o borrado dejaría la orden rota o la impresión cambiada.
- *Solo los IDs del presupuesto de origen*: una corrección en la orden se perdería al volver a entrar, y en una estructura el ítem no es el módulo.

**Consecuencias**: Si el catálogo cambia, la orden sigue imprimiendo lo que se eligió; los desplegables avisan que el valor ya no está. Las reglas de cascada están en dos lugares (API de pricing y servicio de la orden): si cambia una, hay que cambiar la otra.

---

## ADR-026: PDF internos A4 sobre una base común y envío de documentos por WhatsApp directo a Meta desde Django
**Fecha**: 2026-11-09
**Estado**: Activo

**Contexto**: RF-02 pide la planilla de Colocación y RF-03 la de Medición, las dos con la identidad de la Orden de Fabricación. El logo estaba copiado en tres lugares y cada PDF repetía el render con xhtml2pdf. Además, el usuario pidió mandar la planilla por WhatsApp a los números autorizados. Meta solo entrega texto libre dentro de las 24 h en que la persona escribió; fuera de esa ventana exige una plantilla aprobada.

**Decisión**:
1. **Base común en `core`:** `core/pdf.py` (logo, datos de empresa, `render_pdf_bytes`, `pdf_response`) y `core/templates/core/pdf/base_a4.html` con bloques `titulo`, `contenido` y `pie_derecha`. Los PDF internos nuevos extienden esa base.
2. **Reglas de xhtml2pdf** para las plantillas nuevas: solo tablas con ancho en % por celda; altos en px/mm, nunca en %; nada de flex, grid ni colspan; las filas de una tabla con el mismo número de celdas (si cambia, otra tabla); `repeat="1"` en tablas largas. Se verifica el render pasando el PDF a PNG con pypdfium2.
3. **WhatsApp: Django habla directo con la Graph API de Meta** (`core/whatsapp.py`, con `urllib`, sin dependencias nuevas): sube el PDF a `/media` una vez y manda la plantilla con encabezado DOCUMENT a cada número. Las credenciales son las mismas del servicio de n8n, cargadas en `web` como referencia de Railway.

**Alternativas descartadas**:
- *Mandar por un webhook de n8n*: suma un salto que ya se colgó sin avisar («Database is not ready»), y el resultado no vuelve en el momento a quien envía.
- *Texto libre con link al PDF*: Meta no lo entrega fuera de la ventana de 24 h, y un link público expondría datos del cliente.
- *Migrar la Orden de Fabricación a la base*: opcional; su plantilla quedó igual para no arriesgar un documento que el taller usa todos los días.

**Consecuencias**: Medición, Recibo unificado y los PDF que vengan reutilizan la base. Cada documento que se mande por WhatsApp necesita su propia plantilla aprobada por Meta. Si faltan las variables `META_*`, el envío avisa que no está configurado y el PDF sale igual. El «aceptado» de Meta no garantiza la entrega: los rechazos posteriores llegan por el webhook de n8n a `FalloEnvioWhatsApp`.

---

## ADR-025: El pedido de fábrica tiene estado de cabecera con transiciones en un servicio; la orden tiene su propia etapa y revisiones
**Fecha**: 2026-10-30
**Estado**: Activo

**Contexto**: `PedidoFabrica.estado` existía pero ninguna pantalla lo cambiaba y las órdenes no tenían estado: el taller no podía marcar avance, nadie «liberaba» el pedido y se podía editar una orden ya impresa sin rastro (REQ-063).

**Decisión**:
1. **Dos niveles.** El pedido tiene un estado de cabecera (`recibido · en_fabrica · en_produccion · terminado · entregado · cancelado`) y cada orden su etapa de taller (`por_fabricar · corte · armado · vidriado · lista · anulada`). «En producción» y «Terminado» se **calculan** desde las etapas (`recalcular_estado()`), nunca se eligen a mano; recibido, entregado y cancelado no se recalculan.
2. **Las transiciones viven en `plantillas/services/circuito.py`** (liberar, cambiar etapa, revisar, entregar, cancelar), cada una en `transaction.atomic()` con `select_for_update()` y una fila en `HistorialPedidoFabrica` (un solo historial para pedido y órdenes). Las vistas y `presupuestos` llaman al servicio; no escriben estados directo.
3. **Revisión de orden liberada:** al liberar, `revision = 1`. Modificar una orden liberada exige permiso `fabrica.pedidos_gestion` y motivo, incrementa `revision`, prende `reimpresion_pendiente` y avisa a los responsables. El aviso se apaga **solo con confirmación explícita**: POST «Ya la reimprimí» con la revisión que se vio, y solo si coincide con la vigente.
4. `Venta.estado` se escribe desde el pedido al entregar, pero no hay sincronización de vuelta: cambiar la venta a mano no mueve el pedido.

**Alternativas descartadas**:
- *Estado único por pedido, sin etapas por orden*: el taller no puede registrar avance parcial y el estado del pedido quedaría a mano, pudiendo contradecir a las órdenes.
- *Apagar el aviso al abrir el PDF*: abrir el PDF no garantiza que se imprimió ni que el taller retiró el papel viejo, y un GET no debería mutar estado. Además una revisión nueva mientras tanto quedaría tapada; por eso se confirma por POST con la revisión vigente.

**Consecuencias**: Una sola fuente de verdad para el circuito y su historial; el taller puede avanzar sin tocar la cabecera. Las etapas son fijas en código (sumar una requiere migración, decisión P1 del REQ). Las escrituras con `QuerySet.update()` deben pasar `updated_at` a mano para que el tiempo real las detecte. Cancelar el presupuesto cancela también un pedido ya en producción (con advertencia y rastro en el historial). Los usuarios existentes necesitan que un admin les asigne `fabrica.pedidos_gestion` o `fabrica.tablero`.

---

## ADR-024: Tiempo real por polling de 20 s en lugar de WebSockets o SSE
**Fecha**: 2026-10-29
**Estado**: Activo

**Contexto**: Se quiere que listados, avisos, Dólar BNA, KPIs y la edición simultánea se actualicen sin recargar (REQ-065). Producción corre gunicorn **sync con 3 workers**, sin ASGI y sin Redis. WebSockets (Channels) o SSE exigen un servidor asíncrono y un broker, y un stream abierto por pestaña ocuparía un worker sync entero.

**Decisión**:
1. **Polling cada 20 s** a un único endpoint liviano `GET /core/api/live/` (`static/js/live.js`), pausado con la pestaña oculta y con backoff ante errores.
2. **Una consulta agregada por fuente** (`Max(fecha)` + `Count`); las fuentes se registran por app en `<app>/live.py` con `core.live.register`, filtradas por usuario y permiso. Si la fuente cambió, se avisa («Hay cambios · Actualizar») o se refresca el fragmento (`?partial=1`).
3. **Avisos y presencia en la base** (`core.Aviso`, `core.EdicionActiva`, caducidad de 60 s), no en memoria: el caché local no se comparte entre los 3 workers.
4. **El polling no cuenta como actividad:** no renueva `last_activity`, no se audita y no renueva la sesión (`PassiveSessionMiddleware` para `/core/api/`, porque `SESSION_SAVE_EVERY_REQUEST=True`).

**Consecuencias**: Sin infraestructura nueva. Latencia de hasta 20 s y carga constante (un request chico por pestaña cada 20 s). Los modelos sin fecha de modificación (Cliente, tablas legacy de `pricing`) solo detectan altas y bajas. Las tablas grandes pueden necesitar índices en `updated_at`. Si algún día hace falta inmediatez, el contrato de `live.py` permite cambiar el transporte sin tocar las apps.

---

## ADR-023: Paleta «Taller» reemplaza el degradé azul-violeta; Tailwind CDN con tokens inline y `taller.css`
**Fecha**: 2026-10-29
**Estado**: Activo (reemplaza la paleta de botones y tablas de `design-system.md` anterior)

**Contexto**: Cada módulo tenía su propio estilo (degradé azul-violeta en primarios, cabeceras de tabla oscuras, botones de editar/eliminar de colores variados). Se aprobaron 67 mockups con el sistema «Taller» (REQ-064).

**Decisión**:
1. Paleta neutra (tinta `#101828`, línea `#E4E7EC`, fondo `#F4F5F7`) con **un solo color de acción**, azul `#1F4FD8`; verde, ámbar, rojo y violeta **solo como estados** y siempre con texto. Se elimina el degradé azul-violeta y las cabeceras de tabla oscuras.
2. **Se mantiene Tailwind por CDN** (sin build, ver ADR-001): los tokens van inline en el `tailwind.config` de `base.html` (`bg-ground`, `text-ink`, `border-line`, `bg-accent`, etc.) y los componentes repetidos en `static/css/taller.css` con variables CSS `--t-*` (`.btn`, `.card`, `.badge`, `.tbl`, `.kebab`, `.toast`…), más includes en `core/templates/core/ui/`.
3. Tipografía Inter (Google Fonts). Se conservan SweetAlert2, Select2 y FontAwesome.
4. **Los PDF quedan fuera del sistema** (HTML, CSS y vistas intactos).

**Consecuencias**: Un solo lenguaje visual y menos clases ad hoc por template. `design-system.md` se reescribe. Hay que seguir cargando Tailwind desde el CDN. Los templates nuevos deben usar los includes y `taller.css`, no colores inventados.

---

## ADR-022: Estructuras como ítem con JSON (sin modelo nuevo) y geometría duplicada Python/JS con fixtures compartidos

**Fecha**: 2026-10-22 · **Estado**: Aceptada · **Feature**: FEAT-045 / REQ-062

**Contexto**: una estructura son varias aberturas ubicadas sobre una pared, cotizadas como conjunto,
con plano, PDF y una orden de fabricación por abertura. El presupuesto es una lista plana de
`ItemPresupuesto` y el cotizador calcula una abertura por llamada. El editor necesita validar y
dibujar en vivo (arrastre, imán, juntas), pero el precio no puede depender del navegador.

**Decisión**:
1. **La estructura es un `ItemPresupuesto`** con `resultado_json['tipo'] = 'estructura'` + `version`;
   módulos, juntas y snapshots viajan en el JSON. Sin modelo y sin migración. `ancho_mm/alto_mm` del
   ítem = envolvente del conjunto y `precio_unitario_base` queda en el primer nivel, así que lo que ya
   lee el ítem (recargo de renovación, totales, reordenar) sigue funcionando.
2. **El precio se recalcula siempre en el servidor** (`pricing/services/estructura.py`): lista blanca
   de config por módulo, medidas/tratamiento/margen inyectados por el servidor y cada módulo validado
   con el mismo `PricingCalculateSerializer` del cotizador suelto.
3. **La geometría (etiquetas, juntas, solapes, envolvente) existe en Python y en JS**, porque el
   editor la necesita en vivo y el servidor la necesita para validar. Un archivo de fixtures
   (`fixtures_estructura_geometria.json`, 13 casos) lo corren los tests de Python y
   `audit_estructura.mjs` con node: si una versión se desvía, falla.
4. **Se reutiliza el cotizador existente en "modo módulo"** (campos comunes bloqueados) en vez de
   duplicarlo, y el dibujo de una abertura se extrajo a `dibujarAbertura` en `elevacion.js`.
5. **Al confirmar, una orden por módulo** con numeración corrida; el `descripcion_manual` de cada
   módulo nunca lleva la palabra "estructura" (`tipologia.py` la clasificaría `no_dibujo`).

**Alternativas descartadas**:
- Modelos `Estructura` + `ModuloEstructura` con FK: obliga a migración y a que totales, renovación,
  PDF y reordenar lean otra tabla; el cambio de esquema pesa más que el beneficio en la Etapa 1.
- Calcular la geometría solo en el servidor: cada arrastre sería un viaje y no habría imán ni
  validación inmediata. Un solo cálculo en JS sin validar en el servidor deja pasar payloads armados
  a mano.

**Consecuencias**: no se puede consultar por SQL "qué módulos tiene" ni hacer reportes sobre
módulos sin parsear JSON. Cualquier regla geométrica nueva (Etapa 2: antepechos, separaciones menores a
5 mm) hay que escribirla en las dos versiones y sumarle un caso al fixture. El JSON lleva `version`
para poder migrar el formato. Si más adelante hacen falta reportes por módulo, se puede promover a
modelo leyendo el JSON.

---

## ADR-021: Las cotizaciones REHAU se importan con un parser determinista sobre el texto del PDF, con vista previa sin estado

**Fecha**: 2026-09-04 · **Estado**: Aceptada · **Feature**: FEAT-039 / REQ-049

**Contexto**: los presupuestos PVC se cotizan en el software de REHAU, que entrega un PDF; en
AkunCalcu cada ítem se tipeaba a mano. Tres muestras reales confirmaron que el PDF tiene siempre la
misma estructura (cabecera, "Tipología: Vn", descripción, fila `UNITARIO · UNIDADES · TOTAL`, pie).
Las medidas están solo en el dibujo, que es una imagen.

**Decisión**:
1. **Leer el texto con `pypdf`**, que ya estaba instalado como dependencia de xhtml2pdf; se declara
   explícito en `requirements.txt`. Sin OCR: un PDF escaneado da "no tiene texto" y no se importa.
2. **Parser determinista con regex**, separado de la extracción (`parsear_cotizacion(texto)`), anclado
   en la fila de precio y con las tipologías asociadas por conteo para no depender del orden del
   texto. Sin IA: el formato es fijo y un cambio de REHAU debe fallar en voz alta, no adivinar.
3. **Vista previa editable y sin estado en el servidor**: el archivo se lee en memoria y se descarta;
   los ítems detectados viajan en un formset hasta la confirmación. Sin sesión, sin archivo temporal,
   sin tabla de importaciones.
4. **El ítem importado es un `pvc_simple` idéntico al manual**, creado con la misma función
   (`_fields_item_pvc`) y con un bloque `origen` en `resultado_json`. Ningún consumidor del ítem cambia.
5. **Los PDF reales de clientes no entran al repo** (`test_data/*.pdf` ignorado): traen datos
   personales. El pipeline se testea con un PDF generado con reportlab y el texto de las muestras.

**Alternativas descartadas**: Excel/CSV (REHAU no lo exporta); leer las medidas del dibujo (imagen,
exigiría OCR y sería frágil); guardar el PDF adjunto al presupuesto (no se pidió y agrega storage).

**Consecuencias**: la importación depende del formato de REHAU; si cambia, el parser avisa y hay que
ajustar regex (con test sobre el nuevo texto). El unitario se asume **costo** al que se aplica el
margen; si es precio final, margen 0.

---

## ADR-019: Apertura ≠ familia — catálogo en código, tabla propia para lo admitido, dato en el snapshot

**Fecha**: 2026-09-03 · **Estado**: Aceptada · **Feature**: FEAT-037 / REQ-047

**Contexto**: el sistema conocía la *familia* de una abertura (`Producto.tipo_dibujo` + heurística
en `pricing/tipologia.py`, que define la malla 3D) pero no *cómo abre* cada ítem: lado de bisagra,
sentido y carril de cada hoja. Los planos de referencia mostraban que eso varía por ítem. Una
especificación externa proponía un catálogo de tipos fijos (`SLIDING_2`, `CASEMENT_SINGLE`…), un
componente React `<OpeningDiagram>` y un campo `cantidadGuias`.

**Decisión**:
1. **Separar apertura de familia.** La familia sigue en `tipo_dibujo` y no se parte: banderola,
   brazo de empuje y proyectante con tijera comparten malla; la *apertura* carga el símbolo.
2. **El catálogo de 11 aperturas vive en código** (`pricing/aperturas.py`, espejo en
   `static/js/abertura-layout.js`): son símbolos fijos de carpintería, no un ABM.
3. **Lo que admite cada producto va en una tabla gestionada** (`ProductoApertura`, FK sin
   constraint a la legacy `productos`, patrón `VidrioHoja`), no en una columna de la tabla legacy.
4. **La apertura elegida por ítem va en el snapshot** (`snapshot_item.apertura`), sin migración,
   como los tirantes. No afecta el precio: el serializer la deja pasar.
5. **Convención única**: izquierda/derecha = abertura vista de frente. "Int./Ext." = carril.

**Descartado de la especificación externa**: el componente React (acá React vive solo en el modal
del cotizador vía Babel sin build, ADR-015; la unidad reutilizable es una función JS que devuelve
SVG y sirve también en templates Django y el PDF), el catálogo de nombres fijos (reemplazado por
tipología + propiedades), `cantidadGuias` (no cambia el símbolo de frente) y `width/height` en el
símbolo (los mm reales viven en la elevación).

**Consecuencias**: cero cambios en `tipologia.py`; un producto sin aperturas cargadas ofrece todas
las compatibles con su tipología (nada cambia hasta configurarlo); los ítems viejos se dibujan sin
símbolo. Combinaciones (fijo + abrir) entran después por propiedades, sin rehacer el catálogo.

---

## ADR-020: El plano técnico es un SVG puro compartido, y en el PDF va en un anexo

**Fecha**: 2026-09-03 · **Estado**: Aceptada · **Feature**: FEAT-038 / REQ-048

**Contexto**: se pidió agregar cotas "más profesionales" al diseño 3D del cotizador. Los planos de
referencia eran elevaciones 2D. Poner cotas en una perspectiva 3D que rota deforma las medidas
(dos paños iguales se proyectan con largos distintos). El visor 3D es interno; el PDF es lo que
ve el cliente y no tenía ningún dibujo.

**Decisión**:
1. **Un módulo de layout puro** (`abertura-layout.js`) es la única fuente de la aritmética de
   cotas; lo consumen la elevación 2D y el overlay del 3D. No se portó a Python para no tener dos
   fuentes de verdad: el PDF imprime por `window.print()` (ADR-006), así que el mismo módulo JS
   corre en la página del PDF y devuelve SVG inline.
2. **El overlay 3D se desvanece** pasados ~57° del frente, en vez de mostrar cotas que mienten.
3. **En el PDF el plano va en un anexo "Planos"** después de los totales, no en la celda de la
   tabla: la primera versión en la celda estiraba la fila y las cotas no se leían. Los ítems se
   numeran ("Ítem N") para enlazar renglón y plano.
4. **Las cotas de paño parten el ancho total** (borde exterior → eje del travesaño), como en los
   planos de la fábrica, y el último segmento absorbe el redondeo.

**Consecuencias**: el dibujo corre en el navegador del que imprime (si el JS no carga, el recuadro
queda vacío, no rompe el PDF); una consulta a `Producto` por ítem para resolver la tipología
(acotado, pocos ítems por presupuesto); y el dibujo **destapa datos mal cargados** (una sección
ciega guardada donde el texto decía vidrio simple), lo cual es una virtud aunque incomode.

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
