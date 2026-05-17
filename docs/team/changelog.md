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
