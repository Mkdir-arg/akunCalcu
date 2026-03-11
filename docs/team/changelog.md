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
