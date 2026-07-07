# Changelog — AkunCalcu

> Registro cronológico de todos los cambios implementados por el equipo.

## Formato de entrada

```
### [FECHA] Título del cambio
**Sprint**: Sprint N
**User Story**: Como [usuario]...
**Archivos modificados**: lista de archivos
**Descripción**: qué se hizo y por qué.
```

---

## 2026-07-07 — Cotizador para rellenar la abertura en la Orden de Fabricación (FEAT-023)

**Pedido:** "Llevar el pop up de cotización a órdenes."
**Archivos modificados:** `akuna_calc/plantillas/templates/plantillas/orden_form.html`, `plantillas/tests.py`.
**Descripción:** En la edición de la orden, botón "Cargar desde cotizador" que abre un modal con selectores en cascada (Extrusora→Línea→Producto→Marco→Hoja→Vidrio + Color) alimentados por las APIs de catálogo de `pricing`; al confirmar completa Tipo de abertura, Línea, Color, Tipo de vidrio, Modelo de hoja y Cantidad de hojas de la orden. Sin precios (la orden no lleva monto). Modal liviano en JS vanilla (no se reusó el React del cotizador de presupuestos por su acoplamiento a pricing/precios); selects `no-select2`. Sin cambios de modelo ni migraciones. Tests: 22 OK en plantillas.

## 2026-07-07 — Orden de Fabricación: PDF A4 corporativo + datos de contacto en Configuración — Etapa 2 (REQ-035 / FEAT-022)

**User Story:** Como responsable de fábrica, quiero imprimir cada orden de fabricación como PDF A4 con el diseño de Akun, para reemplazar la planilla papel.
**Archivos modificados:** `akuna_calc/plantillas/{views,urls,tests}.py` y templates (`orden_pdf.html` nuevo, botón PDF en `pedido_detail`/`orden_form`); `akuna_calc/configuracion/{models,forms,views,urls}.py` + `general.html` y `datos_empresa_form.html` (nuevo) + migración `0003_seed_datos_empresa.py`; `usuarios/access_control.py`.
**Descripción:** PDF A4 de la orden (xhtml2pdf, ADR-006) fiel a la maqueta: encabezado con logo/N°/fechas, datos del cliente, detalle de la abertura, sección Detalle completa + Estructura, panel de NOTA, tabla de medidas, croquis cuadriculado (Interior/Arriba/Exterior, para dibujar a mano) y pie con datos de contacto + firmas. Los datos de contacto salen de `ConfiguracionGeneral` (claves `empresa_*`, sembradas por data migration y editables en Configuración → Datos de contacto, solo staff), sin hardcodear. Cierra el REQ-035. Se resolvieron dos límites de xhtml2pdf (columnas más angostas que su padding y `height:100%`) con layouts de una sola columna. Migración `configuracion/0003` pendiente en Docker/Railway. Tests: 116 OK.

## 2026-07-07 — Órdenes de Fabricación dentro del pedido — Etapa 1 (REQ-035 / FEAT-021)

**User Story:** Como responsable de fábrica, quiero que cada pedido contenga una orden de fabricación por cada ítem del presupuesto confirmado y poder editar su detalle, para reemplazar la planilla papel.
**Archivos modificados:** `akuna_calc/plantillas/{models,forms,views,urls,admin,tests}.py`, migración `0015_ordenes_de_fabricacion.py`, `templates/plantillas/orden_form.html` (nuevo) y `pedido_detail.html`; `akuna_calc/presupuestos/{views,tests}.py`; `usuarios/access_control.py`.
**Descripción:** Modelos `OrdenFabricacion` (todos los campos de la planilla + nuevo `Estructura`) y `MedidaOrdenFabricacion` (tabla de medidas). Al confirmar un presupuesto (FEAT-019) se genera una orden por ítem precargada desde el snapshot del cotizador (tipo/línea/color/vidrio) + cliente + fecha comprometida + fila de medida. Alta manual de órdenes dentro de cualquier pedido; pantalla de edición con filas de medidas dinámicas; listado en el detalle del pedido. Es la **Etapa 1 de 2** del REQ-035 — la Etapa 2 (PDF A4 corporativo + datos de contacto desde `ConfiguracionGeneral`) queda pendiente. Migración `0015` pendiente en Docker/Railway (solo agrega 2 tablas). Tests: 114 OK (10 nuevos).

## 2026-07-07 — Eliminación del módulo de despiece; Pedidos de Fábrica queda solo (REQ-036 / FEAT-020)

**User Story:** Como administrador del sistema, quiero eliminar los módulos obsoletos de despiece para sacar código muerto y dejar Pedidos de Fábrica como contenedor exclusivo de las futuras Órdenes de Fabricación (REQ-035).
**Archivos modificados:** `akuna_calc/plantillas/{models,views,urls,forms,admin,tests}.py`, migración `0014_eliminar_modelos_despiece.py`, templates de `plantillas` (8 eliminados; `pedido_detail.html` reescrito, `pedido_list.html` con columna Presupuesto), `usuarios/access_control.py`. Eliminados: `services/formula_engine.py`, `management/commands/seed_plantillas.py`, `templatetags/`.
**Descripción:** Se borraron los 5 modelos del despiece (`ProductoPlantilla`, `CampoPlantilla`, `CalculoEjecucion`, `PedidoFabricaItem`, `PedidoFabricaFila`) con sus datos, 16 views y sus URLs, el motor de fórmulas propio y los permisos de menú `despiece.calcular/plantillas/historial`. `/plantillas/` redirige a pedidos. Se conservaron intactos `PedidoFabrica` (con la FK a presupuesto de FEAT-019) y todo el mundo de Opcionales de Fábrica + ABMs del cotizador (frontera verificada: cero referencias cruzadas). Ver ADR-013. Migración `0014` pendiente en Docker/Railway — al aplicarla se pierden los datos históricos del despiece (confirmado por el usuario). Tests: 104 OK en plantillas+presupuestos; pricing solo con su baseline preexistente (verificado vía git stash).

## 2026-07-07 — Confirmar presupuesto pide seña y genera venta + pedido de fábrica (REQ-034 / FEAT-019)

**User Story:** Como vendedor, quiero que al confirmar un presupuesto el sistema me pida la seña cobrada y genere automáticamente la venta en Comercial y el pedido de fábrica en Plantillas, para no cargar los mismos datos tres veces y que todo quede vinculado desde el origen.
**Archivos modificados:** `akuna_calc/plantillas/models.py` (+ migración `0013_pedidofabrica_presupuesto.py`), `akuna_calc/presupuestos/models.py`, `views.py`, `templates/presupuestos/detalle.html`, `tests.py`.
**Descripción:** Al elegir "Confirmado" en el detalle del presupuesto, un popup SweetAlert2 pide la seña (precargada al 50% o 70% del total según `modalidad_sena`, editable; en USD si el presupuesto es PVC con su cotización de cabecera, en pesos si es aluminio; obligatoria > 0 y ≤ total). Al aceptar, en una transacción atómica se confirma el presupuesto, se crea la Venta en `comercial` (número de pedido = número del presupuesto, seña cargada, saldo autocalculado) y se crea la cabecera del Pedido de fábrica `PF-XXXX` en `plantillas` (sin ítems; el despiece lo carga fábrica). Se activó la FK `Presupuesto.venta` (inerte desde la migración 0002) y se agregó la FK nullable `PedidoFabrica.presupuesto`; el detalle confirmado muestra links a ambos registros. Sin URLs nuevas. Validación fuerte en servidor. Ver ADR-012. Migración `plantillas/0013` pendiente de correr en Docker/Railway. Tests: 98 OK (15 nuevos).

## 2026-06-29 — Plazo de entrega en presupuesto + segundo teléfono en el PDF

**Archivos modificados:** `akuna_calc/presupuestos/models.py`, `forms.py`, `templates/presupuestos/detalle.html`, `templates/presupuestos/pdf.html`, `tests.py`, migración `0010_presupuesto_plazo_entrega_dias.py`.
**Descripción:** Se agregó el campo `plazo_entrega_dias` (PositiveIntegerField, opcional) a `Presupuesto`, editable en el panel "Configuración de obra". En el PDF se muestra en la zona superior de descripciones como "Plazo de entrega: X días" (solo si está cargado). Además se sumó el segundo teléfono de Akun (11 2297-6877) al lado del existente (11 4448-2992) en los datos de la empresa del PDF. Migración `0010` pendiente de correr en Docker/Railway.

## 2026-06-29 — Flete y colocación como checkboxes que varían la observación del PDF (FEAT-017)

**User Story:** Como vendedor, quiero tildar si el presupuesto incluye flete y/o colocación desde "Configuración de obra", para que la observación del PDF refleje exactamente lo acordado en lugar de un texto fijo.
**Archivos modificados:** `akuna_calc/presupuestos/models.py`, `forms.py`, `templates/presupuestos/detalle.html`, `templates/presupuestos/pdf.html`, `tests.py`, migración `0008_presupuesto_incluye_flete_colocacion.py`.
**Descripción:** Se agregaron los campos booleanos `incluye_flete` e `incluye_colocacion` (default False) al modelo `Presupuesto`, expuestos como checkboxes en el panel "Configuración de obra". El método `get_observaciones_pdf()` arma el texto de Observaciones del PDF según las 4 combinaciones (antes era fijo: "incluye flete y colocación"). Sin impacto en precios. Migración `0008` pendiente de correr en Docker/Railway.

## 2026-06-27 — Productos terciarizados con precio manual (REQ-033 / FEAT-016)

**User Story:** Como administrador de pricing, quiero marcar ciertos productos como terciarizados (no fabricados, ej. cortinas roller) sin cargarles precio, e ingresar el precio por m² al cotizarlos, para que el cotizador use ese precio en lugar de calcularlo por fórmula.
**Archivos modificados:** `akuna_calc/pricing/models.py`, `forms.py`, `serializers.py`, `catalog_views.py`, `services/calculator.py`, `templates/pricing/config/producto_form.html`, `templates/pricing/cotizador.html`, `tests.py`, `presupuestos/templates/presupuestos/detalle.html`, migración `0003_producto_terciarizado.py`.
**Descripción:** Se agregó el flag `terciarizado` a `Producto` (tabla legacy, migración RunSQL — ADR-011). El producto se da de alta sin precio; el precio por m² se ingresa al cotizar (input en el cotizador cuando el producto elegido es terciarizado, viaja en el payload). El calculator, si el producto es terciarizado, calcula `área × precio_manual_m2` (con margen) y saltea el despiece; error si falta el precio. Branch aislado (productos fabricados sin cambios). La migración queda pendiente de verificación en Docker/prod.

## 2026-06-27 — Fixes RF-006/013/016/018 y verificación RF-005/RF-008-seguridad

**Descripción:** FIX-009 (reporte de proveedores ya no oculta proveedores inactivos con movimientos), FIX-010 (filtro por dirección en ventas), FIX-011 (se quitó línea de fecha repetida en detalle de proveedores), FIX-012 (editar código/PK de un vidrio repuntando sus referencias). Se verificó por tests que RF-005 (cobranzas USD) y RF-008-seguridad (auditoría/backups/control de eliminación) ya estaban cubiertos. Ver `docs/fixes/_LOG.md`.

## 2026-06-19 — Presupuestos PVC siempre en dólares (REQ-032 / FEAT-015)

**User Story:** Como vendedor, quiero que un presupuesto de PVC se cotice y se muestre siempre en dólares (con su propia cotización), para que el cliente vea el presupuesto en la moneda real en la que se vende el PVC, igual que ocurre con las ventas en dólares en `comercial/ventas`.
**Archivos modificados:** `akuna_calc/presupuestos/models.py`, `forms.py`, `views.py`, `templates/presupuestos/form.html`, `detalle.html`, `pdf.html`, `lista.html`, `tests.py`, migración `0007_presupuesto_cotizacion_usd_presupuesto_tipo_material.py`.
**Descripción:** Se agregó `cotizacion_usd` a nivel de cabecera del presupuesto (obligatoria para PVC) y se eliminó el checkbox de USD por ítem. El cálculo interno sigue en pesos como base común; detalle, PDF y listado muestran los montos convertidos a USD cuando el presupuesto es PVC. Aluminio no cambia. Durante el deploy se detectó y corrigió un hueco de migración preexistente del campo `tipo_material` (commit previo sin migración), y un problema similar no relacionado en la app `productos` (migración de borrado de `Cotizacion`/`CotizacionItem` con tablas ya inexistentes); ambos se resolvieron con `migrate --fake` tras confirmar el estado real de las tablas en Railway.

---

## 2026-05-26 — Confirmación antes de reemplazar accesorio en hoja configurator (REQ-030 / FEAT-014)

**User Story:** Como configurador de hojas, quiero que el sistema me pida confirmación antes de reemplazar un accesorio ya cargado, para no perder configuraciones por un cambio accidental.
**Archivos modificados:** `akuna_calc/pricing/templates/pricing/config/hoja_form.html`
**Descripción:** Se agregó lógica JS en el listener `change` de `accesoriosBody` para detectar cuándo el usuario cambia un selector que ya tenía valor. En ese caso se muestra un modal SweetAlert2 con el nombre del accesorio anterior y el nuevo; al cancelar, el selector revierte usando `.trigger('change.select2')` sin re-disparar el autosave.

---

## 2026-05-24 — Backup automatizado de BD con n8n + Google Drive (REQ-028 / FEAT-012)

**User Story:** Como administrador de AkunCalcu, quiero que los backups de la base de datos se generen automáticamente todos los días y se guarden en Google Drive, para tener un respaldo externo confiable que sobreviva a reinicios de Railway.

**Archivos creados:**
- `akuna_calc/security/migrations/0003_backup_storage_location.py`
- `docs/n8n/n8n-backups-workflow.json`
- `docs/n8n/n8n-backups-workflow.md`
- `docs/features/FEAT-012-backup-automatizado-n8n-drive.md`
- `docs/requerimientos/REQ-028-backup-automatizado-n8n-drive.md`

**Archivos modificados:**
- `akuna_calc/security/models.py` — campo `storage_location` (`local` / `drive`).
- `akuna_calc/security/views.py` — endpoint `backup_api_create` (StreamingHttpResponse + subprocess + header `X-Bot-Secret`).
- `akuna_calc/security/urls.py` — ruta `backups/api/create/`.
- `akuna_calc/security/middleware.py` — exenciones para `/security/backups/api/` en `SECURITY_EXEMPT_PREFIXES` y `AuditMiddleware.EXCLUDED_PATHS`.
- `akuna_calc/security/tests.py` — `BackupApiCreateTest` (4 tests).
- `akuna_calc/security/templates/security/backup_list.html` — badge "Auto - Drive".
- `.env.example` — variable `BACKUP_BOT_SECRET`.

**Descripción:** Se incorpora un endpoint API protegido por header secret que ejecuta `mysqldump` y devuelve el SQL como respuesta binaria streameada. n8n lo invoca cada día a las 00:00 ARG y sube el archivo a la carpeta `Backups AkunCalcu/` de Google Drive. Los backups quedan registrados en `/security/backups/list/` con badge **"Auto - Drive"**. Reemplaza la dependencia del filesystem efímero del contenedor (Railway).

---

## 2026-05-26 — Modalidad de seña en presupuestos (REQ-029 / FEAT-013)

**User Story:** Como vendedor, quiero seleccionar una modalidad de seña al generar un presupuesto para definir claramente el porcentaje de adelanto y saldo a cobrar.

**Archivos creados:**
- `akuna_calc/presupuestos/migrations/0006_presupuesto_modalidad_sena.py`
- `docs/features/FEAT-013-modalidad-sena-presupuestos.md`

**Archivos modificados:**
- `akuna_calc/presupuestos/models.py` — nuevo campo `modalidad_sena` con choices cerrados y default `50_50`.
- `akuna_calc/presupuestos/forms.py` — `PresupuestoConfiguracionObraForm` incorpora selector de modalidad.
- `akuna_calc/presupuestos/templates/presupuestos/detalle.html` — selector ubicado debajo de "Tipo" en "Configuración de obra", más visualización en panel bloqueado y resumen.
- `akuna_calc/presupuestos/tests.py` — cobertura de default, render de opciones y persistencia.
- `docs/requerimientos/REQ-029-modalidad-sena-presupuestos.md` — requerimiento marcado como implementado.
- `docs/requerimientos/_INDEX.md` — índice de requerimientos actualizado.
- `docs/features/_INDEX.md` — índice de features actualizado.
- `docs/team/current-sprint.md` — registro de cierre documental fuera de sprint activo.
- `memory/MEMORY.md` — memoria técnica del proyecto actualizada.

**Descripción:** Se agregó la modalidad de seña al flujo de configuración de presupuestos, con dos combinaciones fijas (50/50 y 70/30), preservando el diseño existente del panel lateral. El dato queda persistido en `Presupuesto`, con valor por defecto para compatibilidad histórica, sin introducir nuevas rutas ni cambios de permisos.

---



**Tipo:** Hotfix urgente en producción.

**Síntoma:** Crear backup desde `/security/backups/list/` fallaba con `TLS/SSL error: self-signed certificate in certificate chain` y, tras un primer intento, con `unknown variable 'ssl-mode=DISABLED'`.

**Causa:** `default-mysql-client` en Debian slim es mariadb-client, que no soporta `--ssl-mode=DISABLED`.

**Solución:** Reemplazo del flag por `--skip-ssl`, portable entre clientes. Conexión va por red privada interna de Railway.

**Archivos modificados:**
- `akuna_calc/security/management/commands/create_backup.py`

**Commit:** `37c2858`. Ver `docs/hotfix/_LOG.md` (HFX-001) para detalle completo.

---

## 2026-05-17 — Buscador de accesorios en configurador de hojas (REQ-025 / FEAT-010)

## 2026-05-17 — Estandarización de selectores buscables en todo el sistema (REQ-026 / FEAT-011)

**User Story:** Como usuario de AkunCalcu, quiero que todos los selectores del sistema se vean y funcionen como el buscador de Tipo de Factura para tener una experiencia consistente y encontrar opciones más rápido en cualquier pantalla.

**Archivos creados:**
- `docs/features/FEAT-011-estandarizacion-selectores-buscables-sistema.md` — documentación final de la feature

**Archivos modificados:**
- `akuna_calc/core/templates/core/base.html` — helper global `window.AkunSelect2` y estilo Select2 compartido
- `akuna_calc/core/templates/core/includes/table_filters.html` — filtro de estado integrado al patrón global
- `akuna_calc/core/tests.py` — test del helper compartido
- `akuna_calc/comercial/forms.py` — widgets de filtros en cobranzas
- `akuna_calc/comercial/templates/comercial/reportes/reportes_cobranzas.html` — remoción de CSS local duplicado
- `akuna_calc/comercial/templates/comercial/ventas/form.html` — modal de cliente con helper global
- `akuna_calc/comercial/templates/comercial/compras/form.html` — modal de cuenta con helper global
- `akuna_calc/comercial/templates/comercial/ventas/list.html` — filtros integrados al patrón común
- `akuna_calc/comercial/tests.py` — regresión del render inicial de cobranzas
- `akuna_calc/pricing/forms.py` — selects dependientes integrados al patrón común
- `akuna_calc/pricing/templates/pricing/config/hoja_form.html` — helper compartido para perfiles y accesorios dinámicos
- `akuna_calc/pricing/templates/pricing/config/marco_form.html` — helper compartido para perfiles, accesorios y refresh de selects dependientes
- `akuna_calc/pricing/templates/pricing/config/perfiles.html` — filtros integrados al patrón común
- `akuna_calc/pricing/tests.py` — regresiones de `hoja_form` y `marco_form`
- `akuna_calc/facturacion/templates/facturacion/crear_factura.html` — reinicialización común de selects en formsets dinámicos
- `akuna_calc/presupuestos/forms.py` — selector de tipo de obra integrado al patrón común
- `akuna_calc/presupuestos/templates/presupuestos/lista.html` — filtro de estado integrado al patrón común
- `akuna_calc/presupuestos/templates/presupuestos/detalle.html` — selector de cambio de estado integrado al patrón común
- `akuna_calc/security/templates/security/audit_list.html` — filtros integrados al patrón común
- `akuna_calc/pedidos/templates/pedidos/pedidos_list.html` — filtro de estado integrado al patrón común
- `akuna_calc/gastos_diarios/templates/gastos_diarios/gasto_list.html` — filtro de estado integrado al patrón común
- `docs/requerimientos/REQ-026-estandarizar-selectores-buscables-sistema.md` — requerimiento marcado como implementado
- `docs/requerimientos/_INDEX.md` — índice actualizado
- `docs/features/_INDEX.md` — índice actualizado
- `docs/team/current-sprint.md` — cierre documental fuera de sprint activo
- `docs/team/changelog.md` — entrada de changelog de la feature
- `docs/team/design-system.md` — reglas del helper global, modales y excepciones `no-select2`
- `memory/MEMORY.md` — memoria del proyecto actualizada con el patrón común

**Descripción:** Se consolidó el patrón de Select2 del reporte de cobranzas como estándar visual y técnico del sistema. La configuración ahora vive en `core/base.html` mediante `window.AkunSelect2`, que también cubre selects dinámicos y modales. Solo quedaron excluidos los micro-selects inline donde el buscador empeora una interfaz compacta.

## 2026-05-17 — Buscador de accesorios en configurador de hojas (REQ-025 / FEAT-010)

**User Story:** Como usuario del módulo Fábrica, quiero buscar accesorios escribiendo dentro del campo Accesorio al editar una hoja para encontrar y seleccionar más rápido el accesorio correcto.

**Archivos creados:**
- `docs/features/FEAT-010-buscador-accesorios-config-hojas.md` — documentación final de la feature

**Archivos modificados:**
- `akuna_calc/pricing/templates/pricing/config/hoja_form.html` — buscador Select2 para accesorios dinámicos en edición de hojas
- `akuna_calc/pricing/tests.py` — test de renderizado del buscador de accesorios
- `docs/requerimientos/REQ-025-buscador-accesorios-config-hojas.md` — requerimiento marcado como implementado
- `docs/requerimientos/_INDEX.md` — índice actualizado
- `docs/features/_INDEX.md` — índice actualizado
- `docs/team/current-sprint.md` — cierre documental fuera de sprint activo
- `docs/team/changelog.md` — entrada de changelog de la feature
- `docs/team/design-system.md` — patrón para Select2 en selects dinámicos
- `memory/MEMORY.md` — memoria del proyecto actualizada

**Descripción:** Se mejoró la experiencia de configuración de hojas para que el campo Accesorio use búsqueda sobre Select2 también en filas agregadas dinámicamente. La persistencia no cambió: el sistema sigue enviando el código del accesorio y el autosave existente continúa funcionando sobre la misma estructura de nombres.

## 2026-05-09 — Roles y permisos por módulo y opción (REQ-019 / FEAT-009)

**User Story:** Como administrador, quiero definir al crear o editar un usuario qué módulos del sistema y qué opciones o subsecciones internas de cada módulo puede ver y usar, para controlar el acceso operativo según el rol de cada persona sin mostrar menús no autorizados.

**Archivos creados:**
- `akuna_calc/usuarios/access_control.py` — catálogo central de permisos y mapeo de rutas
- `akuna_calc/usuarios/context_processors.py` — menú lateral basado en permisos
- `akuna_calc/usuarios/middleware.py` — bloqueo por URL según permisos efectivos
- `akuna_calc/usuarios/migrations/0001_initial.py` — nuevos modelos de rol y perfil de acceso
- `akuna_calc/usuarios/migrations/0002_seed_admin_role.py` — siembra del rol Admin y perfiles iniciales
- `akuna_calc/usuarios/tests.py` — cobertura del flujo de permisos
- `docs/features/FEAT-009-roles-permisos-por-modulo-y-opcion.md` — documentación final de la feature

**Archivos modificados:**
- `akuna_calc/usuarios/models.py` — modelos `RolSistema` y `PerfilAccesoUsuario`
- `akuna_calc/usuarios/forms.py` — alta/edición con rol y permisos por módulo
- `akuna_calc/usuarios/views.py` — listados con resumen de acceso y toggle protegido por POST
- `akuna_calc/usuarios/templates/usuarios/user_form.html` — UI de permisos granulares
- `akuna_calc/usuarios/templates/usuarios/user_list.html` — resumen de rol/accesos y activación segura
- `akuna_calc/core/views.py` — login con redirección según primer módulo habilitado
- `akuna_calc/core/urls.py` — login personalizado
- `akuna_calc/core/templates/core/base.html` — sidebar filtrado por permisos
- `akuna_calc/core/templates/core/login.html` — mensajes de acceso y redirección
- `akuna_calc/akuna_calc/settings.py` — middleware y context processor de permisos
- `akuna_calc/security/views.py` — endurecimiento con `@login_required` en backups
- `akuna_calc/pricing/tests.py` — ajuste de redirect esperado al login actual
- `docs/requerimientos/REQ-019-roles-permisos-por-modulo-y-opcion.md` — requerimiento marcado como implementado
- `docs/requerimientos/_INDEX.md` — índice actualizado
- `docs/features/_INDEX.md` — índice actualizado
- `docs/team/current-sprint.md` — cierre documental fuera de sprint activo
- `docs/team/decisions.md` — ADR del registro central por nombre de ruta

**Descripción:** Se implementó un sistema de autorización transversal que separa rol y permisos operativos del `auth_user`, filtra el menú lateral según acceso efectivo, bloquea navegación manual por URL y crea un rol `Admin` con acceso total. La solución centraliza la autorización en un registro por `namespace:url_name`, manteniendo compatibilidad temporal con vistas legacy que todavía dependen de `is_staff`.

## 2026-05-04 — Rediseño del PDF de presupuestos con descripción narrativa por ítem (REQ-016 / FEAT-008)

**User Story:** Como vendedor, quiero que el PDF del presupuesto describa cada ítem con una redacción comercial y técnica armada a partir de la configuración seleccionada, para enviarle al cliente un documento más claro, profesional y fácil de entender.

**Archivos creados:**
- `akuna_calc/presupuestos/pdf_descriptions.py` — helper para snapshot descriptivo, narrativa, resumen técnico y fallback legacy
- `docs/features/FEAT-008-rediseno-pdf-presupuestos-descripcion-narrativa.md` — documentación final de la feature

**Archivos modificados:**
- `akuna_calc/presupuestos/views.py` — persistencia de `snapshot_item` y contexto `items_pdf`
- `akuna_calc/presupuestos/templates/presupuestos/pdf.html` — nuevo diseño comercial del PDF
- `akuna_calc/presupuestos/tests.py` — cobertura del helper narrativo y render del PDF
- `docs/requerimientos/REQ-016-rediseno-pdf-presupuestos-descripcion-narrativa.md` — estado final del requerimiento
- `docs/requerimientos/_INDEX.md` — índice actualizado
- `docs/features/_INDEX.md` — índice actualizado
- `docs/team/current-sprint.md` — cierre documental de la implementación
- `docs/team/decisions.md` — ADR del snapshot descriptivo

**Descripción:** Se rediseñó el PDF de presupuestos para mostrar cada ítem como un bloque comercial con descripción narrativa, resumen técnico y precios. La metadata necesaria se congela al momento de crear el ítem dentro de `resultado_json.snapshot_item`, evitando migraciones y preservando estabilidad histórica aunque cambien los catálogos legacy.

---

## 2026-03-30 — Mejora Presupuestos: Paridad con Cotizador + UI (REQ-008 / FEAT-007)

**User Story:** Como vendedor, quiero que el cotizador embebido en presupuestos tenga las mismas funcionalidades que el cotizador principal (opcionales, desglose completo, mano de obra) y una UI mejorada, para poder armar presupuestos completos sin tener que ir al cotizador aparte.

**Archivos modificados:**
- `presupuestos/views.py` — KPIs con aggregate, filtro Q(), soporte opcionales_json
- `presupuestos/templates/presupuestos/lista.html` — tarjetas KPI, UI mejorada
- `presupuestos/templates/presupuestos/detalle.html` — cotizador React con opcionales + desglose completo + modal desglose

**Archivos eliminados:**
- `presupuestos/templates/presupuestos/item_form.html` — unificado en detalle.html

**Descripción:** Se llevó el cotizador embebido en presupuestos a paridad con el cotizador principal de pricing. Se agregó soporte de opcionales, desglose expandible completo, mano de obra, modal de desglose para ítems guardados, KPIs de resumen en la lista, y se unificó el código eliminando la duplicación entre item_form.html y detalle.html.

---

## 2026-03-28 — Pagos Parciales en Compras (REQ-007 / FEAT-006)

**User Story:** Como administrador, quiero registrar compras con monto total, seña y pagos parciales, y ver el detalle de cada compra con el saldo pendiente, para llevar el mismo control de deuda que tengo en ventas pero del lado de proveedores.

**Archivos modificados:**
- `comercial/models.py` — Compra refactorizado (`importe_abonado`→`valor_total`, +`sena`, `saldo`, `estado`, `notas_internas`), nuevo modelo `PagoCompra`
- `comercial/views.py` — 5 views nuevas + renombre en reportes/dashboard
- `comercial/forms.py` — CompraForm actualizado
- `comercial/urls.py` — 6 rutas nuevas
- `comercial/admin.py` — CompraAdmin actualizado + PagoCompraAdmin
- `comercial/templates/comercial/compras/form.html` — campos valor_total + seña
- `comercial/templates/comercial/compras/list.html` — columna saldo + botón Ver
- `core/views.py` — renombre en dashboard home

**Archivos creados:**
- `comercial/templates/comercial/compras/detail.html` — vista detalle completa
- `comercial/migrations/0014_rename_importe_abonado_compra_valor_total_and_more.py`

**Descripción:** Se replicó la lógica de seña + pagos parciales + saldo dinámico de Ventas al módulo de Compras. La vista de detalle incluye KPIs, barra de progreso, formulario de pago, timeline, notas internas y historial de pagos con edición/eliminación AJAX.

---

## 2026-03-11 — Módulo de Presupuestos — Paso 1 de Fábrica (REQ-006 / FEAT-005)

**User Story:** Como vendedor, quiero armar un presupuesto vinculado a un cliente, agregar múltiples ítems usando la lógica del cotizador, dejar comentarios de seguimiento y generar un PDF para entregar al cliente.

**App nueva:** `presupuestos` — 3 modelos, 9 views, 9 URLs, 5 templates, 12 tests.

**Archivos creados:**
- `presupuestos/` — app completa (models, forms, views, urls, tests, migrations, templates)

**Archivos modificados:**
- `akuna_calc/settings.py` — agrega `presupuestos` a `INSTALLED_APPS`
- `akuna_calc/urls.py` — agrega `path('presupuestos/', ...)`
- `core/templates/core/base.html` — link "Presupuestos" en el sidebar

**Decisiones técnicas:**
- PDF generado como HTML con `@media print` (sin librerías externas) — ver ADR-006
- Cotizador embebido en React en `item_form.html`, delega cálculo a `/pricing/api/pricing/calculate/`
- Presupuestos en estado `confirmado` o `cancelado` quedan bloqueados para edición
- Número autogenerado: `PRES-AAAA-NNN`

**Pendiente Fase 2:** Al confirmar un presupuesto → generar orden de producción en fábrica.

---

## 2026-03-06 — Página de detalle de cliente (REQ-005 / FEAT-004)

**User Story:** Como usuario del sistema, quiero ver una página de detalle de cada cliente que consolide toda su información y actividad comercial.
**Archivos modificados:** `comercial/views.py`, `comercial/urls.py`, `clientes/list.html`, `clientes/detail.html` (nuevo), `comercial/tests.py` (nuevo)
**Descripción:** Se creó la vista `/comercial/clientes/ver/<id>/` con KPIs, gráficos (Chart.js), historial de ventas, pagos y facturas electrónicas por cliente. Se agregó botón "Ver" en el listado.

---

## 2026-03-06 — Sistema de Fórmulas para Marcos (REQ-004 / FEAT-003)

**User Story:** Como administrador, quiero agregar fórmulas de perfiles al configurar un Marco para definir automáticamente las dimensiones de los perfiles necesarios para fabricar ese marco.

**Archivos modificados:**
- `akuna_calc/pricing/config_views.py` — nueva vista `api_get_perfiles`
- `akuna_calc/pricing/urls.py` — nueva URL `/pricing/api/perfiles-simple/`
- `akuna_calc/pricing/templates/pricing/config/marco_form.html` — fix de índices, nueva API de perfiles, carga de fórmulas existentes, JS en `extra_js`
- `akuna_calc/pricing/tests.py` — creado con 6 tests de status code

**Bugs corregidos:**
1. Fórmulas no se guardaban: re-numeración de índices en el submit
2. Selector de perfiles vacío: nueva vista simple sin DRF
3. Fórmulas en edición con timing frágil: datos inyectados server-side, cargados en el `.then()` del fetch

---

## 2026-03-06 — Popup para avanzar estado al completar pago (US-004)

**User Story:** Como vendedor, quiero que al registrar el último pago de una venta (saldo = $0) me aparezca un popup preguntando si deseo cambiar el estado a "Colocado".

**Archivos modificados:**
- `akuna_calc/comercial/views.py` — `venta_detail` + `registrar_pago` + nueva view `cambiar_estado_venta`
- `akuna_calc/comercial/urls.py` — nueva URL `api/venta/<pk>/cambiar-estado/`
- `akuna_calc/comercial/templates/comercial/ventas/detail.html` — popup SweetAlert2 condicional

**Descripción:** Al registrar un pago que deja el saldo en $0 y el estado es `pendiente`, se redirige con `?avanzar_estado=1`. El template detecta el flag y dispara un SweetAlert2. Si el usuario confirma, un fetch POST cambia el estado a `colocado` y recarga la página.

---

## 2026-03-05 — CRUD Fábrica ABM (US-003)

**User Story:** Como administrador, quiero agregar, editar y eliminar de forma lógica los registros de los ABMs de Fábrica para gestionar la configuración desde la interfaz web.

**Archivos creados:**
- `akuna_calc/pricing/forms.py` — 10 ModelForms (Create/Edit separados para Perfil, Accesorio, Vidrio por PK de texto)
- `akuna_calc/pricing/migrations/0003_add_bloqueado_to_legacy_tables.py` — RunSQL para agregar columna Bloqueado a tablas `productos`, `marco`, `hoja`, `interior`
- 10 templates de formulario: `extrusora_form.html`, `linea_form.html`, `producto_form.html`, `marco_form.html`, `hoja_form.html`, `interior_form.html`, `perfil_form.html`, `accesorio_form.html`, `vidrio_form.html`, `tratamiento_form.html`

**Archivos modificados:**
- `akuna_calc/pricing/models.py` — campo `bloqueado` agregado a Producto, Marco, Hoja, Interior
- `akuna_calc/pricing/config_views.py` — 30 vistas nuevas (create/edit/delete × 10 entidades)
- `akuna_calc/pricing/urls.py` — 30 nuevas URLs
- 10 templates de lista reescritos con design system, botón Agregar, columna Estado y acciones (editar/desactivar)

**Decisiones técnicas:**
- Modelos con `managed = False`: IDs generados manualmente via `max(id) + 1` para entidades con PK IntegerField
- Soft delete via campo `bloqueado = 'Si'` (convención existente en la DB legacy)
- Perfil/Accesorio/Vidrio tienen PK de texto (codigo) definido por el usuario → formularios Create/Edit separados

**Bugs corregidos:**
- Templates referenciaban `producto.nombre`, `perfil.nombre`, `perfil.id` — campos inexistentes. Corregido a `descripcion` y `codigo`.

---

## 2026-03-04 — Módulo de Pedidos Telegram (Bot de Voz)

**User Story:** Como vendedor de Akuna Aberturas, quiero enviar un audio de voz por Telegram con los ítems de un pedido, para que el sistema lo interprete automáticamente y lo registre como pedido en AkunCalcu.

**Archivos creados:**
- `akuna_calc/pedidos/__init__.py`
- `akuna_calc/pedidos/apps.py`
- `akuna_calc/pedidos/models.py` — modelos `PedidoTelegram` + `ItemPedidoTelegram`
- `akuna_calc/pedidos/views.py` — endpoints API + vista lista
- `akuna_calc/pedidos/urls.py`
- `akuna_calc/pedidos/migrations/0001_initial.py`
- `akuna_calc/pedidos/templates/pedidos/pedidos_list.html`
- `docs/n8n-pedidos-workflow.md` — JSON del workflow n8n listo para importar

**Archivos modificados:**
- `akuna_calc/akuna_calc/settings.py` — agregado `pedidos` a `INSTALLED_APPS`
- `akuna_calc/akuna_calc/urls.py` — agregado `path('pedidos/', ...)`
- `docker-compose.yml` — agregada variable `TELEGRAM_BOT_SECRET`

**Descripción:** Implementación completa del flujo de pedidos por voz vía Telegram. El bot transcribe el audio (Whisper), extrae ítems con GPT-4o-mini, crea un borrador en Django, pide confirmación al usuario y según la respuesta confirma o cancela el pedido. Ver en `http://localhost:8080/pedidos/`.

---

## 2026-03-04 — Documento V1 del sistema

**User Story:** Como equipo de desarrollo, quiero un documento V1 del sistema.
**Archivos creados:** `docs/V1-sistema.md`
**Descripción:** Análisis completo del sistema. Se documentaron 8 módulos, sus procesos, cálculos internos, arquitectura técnica, flujos de trabajo, integraciones y glosario del negocio.

---

## 2026-03-04 — Setup del equipo de agentes

**Descripción**: Se configuró la estructura del equipo de desarrollo con metodología Scrum guiado.
- Creado `CLAUDE.md` con roles, workflow y convenciones
- Creado `docs/team/` con backlog, sprint, decisions, changelog
- Creados comandos personalizados en `.claude/commands/`
- Inicializada memoria del proyecto en `memory/MEMORY.md`
