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

## ADR-005: Chart.js para gráficos en detalle de cliente
**Fecha**: 2026-03-06
**Estado**: Activo

**Contexto**: La página de detalle de cliente requiere gráficos (barras y donut). Las librerías disponibles en base.html no incluyen ninguna de gráficos.

**Decisión**: Usar Chart.js 4.4.0 via CDN, cargado únicamente en el bloque `extra_js` del template `clientes/detail.html`. No se agrega a `base.html` para no impactar el peso de todas las páginas.

**Consecuencias**: Si se necesitan gráficos en otras páginas, se puede reutilizar el mismo CDN en sus respectivos `extra_js`. Si el uso crece, evaluar agregar a `base.html` o instalar via npm.
