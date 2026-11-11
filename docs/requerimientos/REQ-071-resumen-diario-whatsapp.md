# REQ-071 — Resumen diario y semanal por WhatsApp para la dirección
**Estado**: Implementado
**Fecha**: 2026-11-10
**Solicitante**: Dirección

## Descripción de la idea
Dos personas de la dirección reciben por WhatsApp un resumen de lo que pasó en el negocio:
- **De lunes a viernes a las 19:00**: el resumen del día.
- **Los sábados a las 13:00**: el resumen de la semana (de lunes a sábado), con un ranking por vendedor.

El resumen cubre presupuestos, ventas, pedidos de fábrica, agenda, pedidos de presupuesto
asignados por mail y la actividad de cada usuario en el sistema.

Funcionamiento:
1. n8n se dispara por horario.
2. Le pide a Django los números del período por una API protegida con clave secreta.
3. GPT-4o-mini **solo redacta** un texto corto a partir de esos números; no calcula ni agrega datos.
4. Django guarda el texto generado.
5. n8n manda a las 2 personas una plantilla aprobada por Meta: «Tu resumen del día está listo»,
   con un botón «Ver resumen».
6. Cuando la persona toca el botón, se abre la ventana de 24 h de WhatsApp y n8n le manda el
   resumen completo como texto libre, con formato.

## Problema que resuelve
Hoy, para saber cómo fue el día, la dirección tiene que entrar al sistema y recorrer varias
pantallas: presupuestos, ventas, pedidos de fábrica, agenda y solicitudes. No hay una vista que junte
todo, y los presupuestos que quedaron sin respuesta o los pedidos atrasados se ven solo si alguien
los busca.

## Usuarios beneficiados
- 2 personas de la dirección, todos los días hábiles y los sábados.
- De forma indirecta, los vendedores: los presupuestos sin seguimiento salen a la luz.

## Valor para el negocio
- Saber todos los días, sin entrar al sistema, qué entró, qué se vendió y qué está trabado.
- Los presupuestos enviados hace 7 días o más sin respuesta aparecen todos los días: así se
  recuperan ventas que hoy se pierden.
- Si no se implementa, el seguimiento depende de que alguien se acuerde de mirar.

## Contenido del resumen

| Bloque | Dato | De dónde sale |
|---|---|---|
| Presupuestos | Creados en el período: cantidad y monto, por vendedor | `Presupuesto.created_at`, `total`, `created_by` |
| Presupuestos | Confirmados en el período | `Venta` / `PedidoFabrica` creados con `presupuesto` de origen (FEAT-019) |
| Presupuestos | Enviados hace 7 días o más sin respuesta | `estado='enviado'` y antigüedad ≥ 7 días (ver pregunta abierta 3) |
| Ventas | Total del período y comparación con el mismo período anterior | `Venta.created_at`, `valor_total` |
| Fábrica | Cambios de estado de los pedidos | `HistorialPedidoFabrica` (`desde`, `hasta`, `usuario`) |
| Fábrica | Pedidos atrasados | `PedidoFabrica.fecha_comprometida` (propiedad) < hoy y estado no cerrado |
| Agenda | Colocaciones y mediciones del día, por colocador o técnico | `EventoAgenda.fecha_evento`, `tipo`, `colocador`, `tecnico` |
| Solicitudes | Recibidas, asignadas y contestadas, por vendedor | `SolicitudPresupuesto.vendedor`, `fecha_asignacion`, `fecha_contestada` |
| Actividad | Acciones por usuario (altas, ediciones), agrupadas por módulo | `security.AuditLog` (`user`, `action`, `model_name`, `timestamp`) |
| Tareas | Cuando exista REQ-072: tareas cerradas, vencidas y pendientes por responsable | `tareas.Tarea` |

## Viabilidad técnica
Se puede con el stack actual. El patrón ya existe:
- **API para n8n con clave secreta** en header, como `/security/backups/api/create/` (FEAT-012) y
  `/security/salud/api/fallo-whatsapp/` (FIX-026).
- **Envío directo a la Graph API de Meta** desde n8n, como en los recordatorios de agenda.
- **GPT-4o-mini en n8n**, como en el bot de pedidos por voz.

Componentes:
1. **Django — app nueva `resumenes`**:
   - `GET /resumenes/api/datos/?periodo=dia|semana&fecha=AAAA-MM-DD` → JSON con los números.
     Los cálculos viven en un servicio (`resumenes/services.py`) y se testean.
   - `POST /resumenes/api/guardar/` → guarda el texto redactado por GPT.
   - `GET /resumenes/api/ultimo/?telefono=...` → devuelve el último resumen para mandarlo cuando
     la persona responde.
   - Modelo `Resumen` (período, fecha, datos JSON, texto, enviado a, abierto en). Sirve también
     como historial.
   - Header `X-Bot-Secret` con una variable nueva `RESUMEN_BOT_SECRET`. Ruta exenta en
     `SECURITY_EXEMPT_PREFIXES` y `AuditMiddleware.EXCLUDED_PATHS`.
2. **n8n — workflow nuevo «Resumen dirección»**: cron → datos → GPT → guardar → plantilla a los 2
   números. Los recolectados para marcar «enviado» se toman **de la respuesta del envío**, no del paso
   anterior (lección de la caída de Evolution).
3. **n8n — rama nueva en el webhook entrante de Meta**: si llega el botón «Ver resumen» de uno de
   los 2 números → pedir el último resumen a Django → mandarlo como texto libre.
4. **Meta**: plantilla nueva `resumen_listo` (categoría Utility, `es_AR`) con botón de respuesta rápida.

## Apps / módulos afectados
- Nueva: `resumenes` (modelo, API, servicio de cálculo, tests). Migración `resumenes/0001`.
- Solo lectura: `presupuestos`, `comercial`, `plantillas`, `agenda`, `solicitudes`, `security`.
- `akuna_calc/settings.py` y `akuna_calc/urls.py`: registrar la app y la ruta.
- n8n: workflow nuevo + cambio en el workflow que recibe el webhook de Meta
  (hoy `VfdJhVTZmKj7HoES`, gastos diarios).
- Meta: plantilla nueva.

## Complejidad estimada
**Mediano**: 2 a 3 días de trabajo, más 1 a 3 días hábiles para que Meta apruebe la plantilla.

## Dependencias y riesgos
1. **Webhook entrante de Meta (bloqueante).** El botón «Ver resumen» llega por el webhook de Meta,
   que hoy sigue apuntando al Evolution muerto. Primero hay que terminar el paso (2) de FIX-026:
   apuntarlo a n8n.
2. **Un solo webhook por app de Meta.** El mismo webhook recibe los gastos por voz. La rama del
   resumen tiene que filtrarse **antes** del parseo de gastos; si no, el bot de gastos contesta
   «No te entendí». Por eso se usa un botón con un identificador fijo en lugar de pedir que escriban «OK».
3. **Facturación de Meta.** Las plantillas son pagas. Si la cuenta sigue con el error 131042, el
   aviso no se entrega. Hay que verificarlo antes de pedir la plantilla.
4. **«Aceptado» no es «entregado».** Meta devuelve `accepted` y el rechazo llega después por el
   webhook. El nodo «Fallo de Envío» de FIX-026 ya registra los `failed`; el resumen debe usarlo.
5. **Datos sensibles por WhatsApp.** El resumen lleva montos de ventas. Solo se manda a los 2 números
   configurados, y la rama de respuesta valida el número que escribe.
6. **Sin pedidos atrasados reales si no se carga la fecha comprometida.** El dato depende de que las
   órdenes tengan `fecha_comprometida`.

## Alternativas técnicas consideradas
- **Plantilla con números en una línea + link a una página del sistema**: no necesita webhook
  entrante, pero el resumen no llega completo al WhatsApp. Descartada por el usuario.
- **Telegram**: sin plantillas ni costo, pero el usuario prefiere WhatsApp. Descartada.
- **Que GPT calcule a partir de datos crudos**: descartada; inventa números. Django calcula y GPT
  solo redacta.

## Preguntas abiertas
1. **Los 2 números** que reciben el resumen.
2. **Agenda «hechas / pendientes»**: `EventoAgenda.estado` es `programado` / `enviado` / `cancelado`,
   y `enviado` significa «se mandó el recordatorio», no «se hizo el trabajo». Sin un estado «realizado»,
   el resumen solo puede mostrar lo **programado**. ¿Se agrega ese estado (migración chica) o se espera
   a REQ-072?
3. **Presupuestos sin respuesta**: no hay fecha de envío guardada; se mediría desde `created_at`
   (o `updated_at`). ¿Alcanza esa aproximación?
4. **Feriados**: ¿se manda igual el resumen un día sin actividad, o se salta?
5. **Ranking del sábado**: ¿por monto vendido, por cantidad de presupuestos, o por ambos?

## Derivó en
[FEAT-055](../features/FEAT-055-resumen-diario-whatsapp.md) — Django listo; la puesta en marcha (plantilla de Meta, webhook, variables y activación de n8n) está pendiente.
