# REQ-061 — Alerta de ventas en blanco sin facturar al cierre del mes (sistema + WhatsApp)

- **Estado:** Aprobado
- **Fecha:** 2026-10-20
- **Complejidad:** Mediano
- **Origen:** RF-012 (prioridad Media). Canales definidos por el usuario: **aviso en el sistema y WhatsApp**
- **Plan:** [Plan RF Akun — octubre 2026](../team/plan-rf-akun-2026-10.md) · Sprint 3
- **Apps afectadas:** `comercial`, `core`, `usuarios`, `security` + workflow n8n

## User Story

Como **administración** quiero **que el sistema me avise al cierre del mes qué ventas en blanco
siguen sin facturar**, en pantalla y por WhatsApp, para **facturarlas antes de que cierre el período**.

## Decisiones tomadas

| Tema | Decisión |
|---|---|
| "Sin facturar" | Venta activa, en blanco (`con_factura=True`), sin `numero_factura`, que no sea NC, sin factura electrónica autorizada **y sin ningún pago con número de factura**. Lo último es imprescindible: las ventas creadas al confirmar un presupuesto (FEAT-019) se facturan a nivel de pago y si no, aparecerían siempre |
| Período | Ventas del mes en curso (fecha local Argentina) + arrastre de meses anteriores **solo desde una fecha de corte** (`ConfiguracionGeneral['alerta_facturacion_desde']`, por defecto la fecha del deploy), para no traer de golpe el histórico ni ventas viejas que quedaron "en blanco" por defecto |
| Aviso en el sistema | Banner en `/home/` para administración (acceso total o rol administrativo), **desde 2 días antes del cierre hasta el último día** (`alerta_facturacion_dias_antes`, configurable). Da tiempo para facturar y cubre el caso de que n8n no corra (no recupera crones perdidos) |
| WhatsApp | El **último día del mes**, a los usuarios de administración que tengan número de WhatsApp activo en su perfil (override opcional `alerta_facturacion_numeros`). Mensaje por template aprobado de Meta |
| Quién decide el día | **Django**: n8n corre todos los días y Django responde si hoy corresponde enviar (el cron de n8n no tiene "último día del mes") |
| Cobros en blanco sin factura (variante a nivel pago) | Fuera de alcance; se puede sumar después |

## Criterios de Aceptación

- [ ] Una única función calcula las ventas sin facturar y la usan el banner, el listado y el WhatsApp
- [ ] En la ventana de cierre, administración ve en `/home/` un banner ámbar con cantidad, total y un enlace al listado de ventas filtrado
- [ ] Los vendedores no ven el banner; fuera de la ventana no aparece; sin ventas pendientes no aparece
- [ ] El listado de ventas acepta `?facturacion=pendiente` y muestra exactamente esas ventas
- [ ] El último día del mes (hora Argentina) llega un WhatsApp a cada destinatario con período, cantidad, total y números de pedido
- [ ] El endpoint para n8n rechaza pedidos sin el secreto (401) y permite forzar el envío para probar
- [ ] El workflow nuevo aparece en el panel de salud (FEAT-035) con umbral de 26 h
- [ ] Una venta creada el 31/10 a las 23:30 hora Argentina cuenta en octubre

## Diseño técnico

**Lógica (nuevo `comercial/alertas.py`)**
```
Venta.objects.filter(deleted_at__isnull=True, con_factura=True, numero_factura='')
  .exclude(tipo_factura='NC')
  .exclude(factura_electronica__estado='autorizada')
  .exclude(Exists(PagoVenta.objects.filter(venta=OuterRef('pk')).exclude(numero_factura='')))
```
Fecha: `hoy = timezone.localdate()`, `ultimo = calendar.monthrange(...)[1]`, ventana `hoy.day >= ultimo - dias_antes`. **No usar `django.utils.timezone.utc`** (no existe en Django 6 del venv local); si hace falta, `datetime.timezone.utc`. `Venta.ESTADO_CHOICES` no tiene "anulada": la anulación es el borrado lógico.

**Aviso en el sistema**
- `usuarios/access_control.py`: helper `es_rol_administracion(user)`. `presupuestos/views.py` ~l.82 (`_puede_ver_creador`) tiene la misma lógica y puede pasar a usarlo
- `core/views.py` (`home` ~l.47-79) y `core/templates/core/home.html`: banner
- `comercial/views.py` (`ventas_list` ~l.274-300): filtro `facturacion=pendiente` + chip en la plantilla. Misma ruta, sin cambios de permisos

**WhatsApp** (mismo patrón que el recordatorio de las 08:00: endpoint Django con secreto + cron n8n + template de Meta; el token de Meta vive solo en n8n)
- Endpoint `POST /comercial/api/alertas/ventas-sin-facturar/` (`@csrf_exempt`, `@require_POST`, header `X-Bot-Secret` = env nueva **`ALERTAS_BOT_SECRET`**, un secreto por integración). Responde `{ok, enviar, periodo, cantidad, total, destinatarios:[{numero, nombre}], parametros:[p1..p4]}`. `enviar` es verdadero solo el último día del mes, o con `{"forzar": true}`
- `usuarios/access_control.py`: agregar la ruta a `PUBLIC_ROUTE_KEYS` (si no, el middleware manda a n8n al login)
- `security/middleware.py`: **`/comercial/api/alertas/`** en `SECURITY_EXEMPT_PREFIXES` y `AuditMiddleware.EXCLUDED_PATHS`. **No eximir `/comercial/api/`** entero: ahí hay endpoints con sesión que modifican datos (editar/eliminar pagos) y quedarían sin seguridad ni auditoría
- Workflow n8n: Schedule diario 10:00 (`timezone America/Argentina/Buenos_Aires`) → HTTP a Django → IF (`enviar` y hay destinatarios) → Code (un ítem por destinatario) → HTTP a `graph.facebook.com/v21.0/{{$env.META_PHONE_NUMBER_ID}}/messages` con `type:'template'`. Nodo de envío **sin `onError` permisivo**. Docs: `docs/n8n/n8n-alertas-facturacion.{json,md}`
- **Template de Meta** `alerta_ventas_sin_facturar` (Utility, es_AR, 4 parámetros): "Cierre de {{1}}: hay {{2}} ventas en blanco sin facturar por {{3}}. Pedidos: {{4}}. Revisalas en AkunCalcu." Los parámetros no admiten saltos de línea; {{4}} en una línea separada por " · ", truncada a ~500 caracteres con "y N más"
- `security/health.py` (`WORKFLOWS_VIGILADOS` ~l.42-64): sumar el workflow (tipo schedule, 26 h). **Rompe `security/test_salud.py`** (asume 3 workflows: `ACTIVOS`, `len == 3`, `side_effect` con 3 ejecuciones): actualizar a 4
- Railway: `ALERTAS_BOT_SECRET` en `web` y en n8n

## Prerrequisito con plazo

**Pedir la aprobación del template a Meta el primer día del plan** (tarda) y confirmar que el billing de la cuenta de WhatsApp Business esté OK (error 131042 visto antes). La parte de WhatsApp se activa cuando el template esté aprobado; el banner no depende de eso.

## Tests

- Unitarios: último día en 31/10, 30/10, 28/02/2027 y 29/02/2028; ventana con `dias_antes`; el queryset excluye borradas, en negro, con número, con pago facturado, con factura electrónica autorizada y NC; borde de huso horario
- API: 401 sin secreto; `enviar=false` un día común (patch de `timezone.localdate`); destinatarios desde el perfil; parámetros sin `\n` y truncados
- Home: admin ve el banner en la ventana; vendedor no; fuera de ventana no
- Middleware: el path es público y está exento
- `security/test_salud.py` actualizado a 4 workflows

**Migración:** No.
