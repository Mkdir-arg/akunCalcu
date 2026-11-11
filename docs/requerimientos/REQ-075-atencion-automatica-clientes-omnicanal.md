# REQ-075 — Atención automática de clientes por WhatsApp, email e Instagram
**Estado**: En análisis
**Fecha**: 2026-11-11
**Solicitante**: Dirección

## Descripción de la idea
Un asistente que atiende los mensajes de clientes que llegan por WhatsApp, email e Instagram.
Contesta en el tono de Akuna, junta los datos para cotizar (tipo de abertura, medidas,
material, localidad, obra nueva o renovación), arma el presupuesto con el cotizador de
AkunCalcu y lo manda por el mismo canal. También responde consultas de pedidos en curso.
Cuando hace falta, pasa la conversación a un vendedor sin que el cliente note el cambio.

## Problema que resuelve
- Hoy cada mensaje lo lee y lo contesta una persona. La primera respuesta tarda horas y
  fuera de horario no hay respuesta.
- Los datos para cotizar llegan incompletos y el vendedor tiene que pedirlos uno por uno
  («¿qué medida?», «¿aluminio o PVC?», «¿con vidrio DVH?»).
- Solo el email está integrado (REQ-037): se clasifica con IA y se reparte entre vendedores,
  pero nadie le contesta al cliente automáticamente. WhatsApp e Instagram no pasan por el sistema.
- No queda registro de las conversaciones en AkunCalcu. La consulta no está vinculada a la
  solicitud, al cliente ni al presupuesto.

## Usuarios beneficiados
- **Clientes**: reciben respuesta en minutos, a cualquier hora, por el canal que eligieron.
- **Vendedores**: reciben la solicitud con los datos completos y un presupuesto borrador ya
  calculado. Solo intervienen para aprobar o en los casos que no son estándar.
- **Dirección**: ve en un solo lugar todas las consultas, los tiempos de respuesta y la
  conversión por canal.
- Frecuencia: todos los días, en cada consulta que entra.

## Valor para el negocio
- **Si se implementa**: se responde rápido (el que contesta primero suele quedarse con la
  obra), los vendedores pasan menos tiempo en tareas repetitivas y quedan registradas todas
  las conversaciones.
- **Si no se implementa**: se siguen perdiendo consultas que llegan fuera de horario o en
  momentos de mucha demanda, y no se puede medir cuánto entra por cada canal.

## Viabilidad técnica
Es viable con lo que ya tenemos (Django, n8n en Railway, OpenAI, Meta Cloud API y Gmail).
Hay varias piezas que se pueden reutilizar:

| Pieza existente | Qué aporta |
|---|---|
| `solicitudes` + workflow n8n «Solicitudes Presupuesto - Reparto» | Clasificación de mails con IA, reparto por turnos, detección de spam, API `/solicitudes/api/crear/` con `X-Bot-Secret` |
| Workflow «WhatsApp Gastos Diarios v2 (Meta Cloud API)» | Webhook de Meta ya verificado, normalización de eventos, transcripción de audios con Whisper, envío de texto libre dentro de la ventana de 24 h, detección de envíos fallidos |
| `pricing.services.calculator.calcular_precio()` | Precio a partir de `marco_id` + `ancho_mm` + `alto_mm` (más hoja, vidrio, color, tratamiento y opcionales) |
| `presupuestos.Presupuesto` (FK opcional a `SolicitudPresupuesto`) + PDF | El presupuesto ya puede quedar vinculado a la solicitud y generar su PDF |
| `core/whatsapp.py` (`subir_pdf`, `enviar_plantilla_documento`) | Envío de PDF por WhatsApp (ya se usa en FEAT-049) |

**Arquitectura propuesta**: Django guarda el estado y n8n conecta los canales.

```
WhatsApp (Meta) ─┐                                ┌─ buscar_cliente / estado_pedido
Instagram (Meta) ┼─► n8n: normaliza ─► Django ────┼─ catálogo de tipologías
Gmail ───────────┘     (1 webhook     /conversaciones/api/entrante/
                        por canal)         │      └─ cotizar → Presupuesto borrador
                                           ▼
                              ¿responde el bot o un humano?
                                           │ bot
                                           ▼
                         n8n Agent (LLM + tools que llaman a Django)
                                           │
                                           ▼
                        respuesta por el mismo canal y el mismo hilo
```

- **App nueva `conversaciones`**: `Conversacion` (canal, id externo del contacto, FK opcional
  a `Cliente` y a `SolicitudPresupuesto`, modo `bot`/`humano`/`cerrada`, vendedor asignado) y
  `Mensaje` (dirección, autor bot/humano/cliente, texto, adjuntos, id externo para idempotencia).
- **Bandeja en AkunCalcu**: el vendedor ve la conversación, toma el control con un botón
  («Atiendo yo») y contesta desde el sistema por el mismo canal.
- **Cotización en dos niveles**: el bot nunca inventa precios. Llama a Django, que calcula con
  el cotizador usando una *tipología estándar* (línea, vidrio y color por defecto para cada
  tipo de abertura) y crea un `Presupuesto` en `borrador`. Según lo que se decida, sale
  automáticamente o espera la aprobación del vendedor con un clic.
- **Comportamiento natural**: espera de 20 a 40 s antes de responder, para juntar los mensajes
  que el cliente manda seguidos. Respuestas cortas, en el registro rioplatense de los
  vendedores. Lee audios (Whisper) y fotos o planos (visión).

## Apps / módulos afectados
- **Nueva**: `conversaciones` (models, APIs para n8n, bandeja, tests).
- `solicitudes`: valores nuevos en `origen` (`whatsapp`, `instagram`); vincular la conversación.
- `presupuestos`: crear el borrador desde la API; envío del PDF por el canal de origen.
- `pricing`: servicio de «tipología estándar» → `configuracion` del cotizador.
- `comercial.Cliente`: búsqueda por teléfono, email o usuario de Instagram (posible campo nuevo).
- `pedidos`: consulta de solo lectura del estado del pedido para el cliente.
- **n8n**: router común para el webhook de Meta (hoy lo usa únicamente Gastos Diarios),
  workflow de Instagram, extensión del workflow de Gmail para contestar en el hilo, y un
  Agent de n8n con tools.
- `security` / panel de salud (FEAT-035): sumar el latido de los canales nuevos.

## Complejidad estimada
**Grande**. Se propone dividirlo en etapas, cada una con su propio `/feature`:

1. **Etapa 1 — Bandeja omnicanal + primera respuesta**: WhatsApp e Instagram entran como
   `Solicitud`. El bot saluda, pide los datos que faltan y responde preguntas frecuentes
   (horarios, zona, formas de pago, plazos). Sin precios. Derivación a un humano.
2. **Etapa 2 — Cotización asistida**: el bot arma el presupuesto borrador con el cotizador, el
   vendedor lo aprueba con un clic y el bot manda el PDF por el canal de origen.
3. **Etapa 3 — Cotización automática y seguimiento**: las tipologías estándar dentro de ciertos
   límites salen sin aprobación. Seguimiento a los 3 y 7 días (plantilla de Meta) y consulta
   del estado del pedido.

## Dependencias o riesgos
- **Número de WhatsApp**: el número de la Cloud API ya se usa para tareas internas (gastos,
  agenda, resumen). Hoy un número no habilitado que escribe recibe un 403 de
  `/gastos-diarios/api/responder/` y nadie le contesta. Hace falta un router previo que separe
  personal interno de clientes. Si los clientes escriben a otro número que hoy se atiende con
  la app WhatsApp Business del celular, hay que migrarlo a la Cloud API. Con el modo
  *coexistencia* de Meta se puede seguir usando la app, y los mensajes que mande el vendedor
  llegan como *echo*, lo que permite pausar al bot.
- **Evolution API**: el aviso «WhatsApp al Vendedor» todavía sale por Evolution
  (`evolution-api-production-874e`). Para clientes conviene usar solo la API oficial de Meta,
  porque las APIs no oficiales tienen riesgo de bloqueo del número.
- **Instagram**: requiere una cuenta profesional vinculada a una página de Facebook y el permiso
  `instagram_manage_messages` aprobado en la app de Meta (App Review). Rige la misma ventana de
  24 h que en WhatsApp.
- **Políticas de Meta**: está permitido un bot de atención propio del negocio. No se permite un
  asistente de propósito general. El bot tiene que mantenerse en temas de Akuna.
- **«Que no se note que es un robot»**: se puede lograr con buen tono, tiempos y continuidad, y
  haciendo que el traspaso a un humano sea invisible (mismo canal, mismo hilo, mismo historial).
  Recomendación: firmar como «el equipo de Akuna» en vez de inventar el nombre de una persona, y
  **no negar ser automático si el cliente lo pregunta directamente**. Hay regulaciones de
  transparencia de IA que van en esa dirección, y si un cliente descubre que le mintieron
  después de confirmar una obra, el daño comercial es grande.
- **Precios equivocados**: el riesgo principal. Para mitigarlo, el precio siempre lo calcula el
  cotizador (nunca el LLM), el presupuesto tiene vencimiento y queda la aprobación humana
  hasta tener confianza (etapas 2 y 3).
- **Alucinaciones** en plazos, stock o condiciones: el bot responde solo con datos que devuelve
  Django o una base de conocimiento cargada por Akuna. Si no sabe, deriva.
- **Hallazgos al revisar n8n**:
  - La versión publicada de «WhatsApp Gastos Diarios v2» todavía tiene un valor por
    defecto hardcodeado para `X-Bot-Secret`. El borrador ya no lo tiene, pero no se
    publicó.
  - Ese workflow tuvo 3 ejecuciones fallidas recientes y el backup diario falló en su última
    corrida.
  - Los webhooks apuntan a `n8n-production-9a1a.up.railway.app`, no a la URL de `n8n-2el`.

## Alternativas técnicas
- **A) n8n Agent + tools en Django (recomendada)**: se reutiliza lo que ya funciona. La lógica de
  negocio y los precios quedan en Django, con tests. n8n queda como integración y prompt.
- **B) Todo en Django** (webhooks de Meta y Gmail directos + SDK de LLM): más control y tests,
  pero se reescribe lo que ya está andando en n8n.
- **C) Plataforma omnicanal de terceros** (por ejemplo, un CRM con bandeja unificada): rápido
  de arrancar, pero tiene costo mensual por agente y queda desconectado del cotizador y de los
  presupuestos de AkunCalcu.

## Preguntas abiertas
1. ¿Los clientes escriben al **mismo número** de WhatsApp que usa la Cloud API (gastos, agenda) o
   a otro? Si es otro, ¿hoy se usa con la app WhatsApp Business en un celular?
2. ¿El email de clientes es el mismo Gmail que ya lee el workflow de reparto?
3. ¿La cuenta de Instagram es profesional y está vinculada a una página de Facebook?
4. ¿El bot puede **dar precios sin aprobación** de un vendedor? ¿Para qué tipologías y hasta qué
   monto? ¿Cuál es la tipología estándar por defecto de cada tipo de abertura (línea, vidrio, color)?
5. Si el cliente pregunta «¿sos un bot?», ¿qué responde? (Recomendación: no negarlo.)
6. ¿El bot responde 24/7 o en horario comercial? ¿Y fuera de horario?
7. Cuando dicen «pedidos», ¿se refieren a consultas de estado de una obra ya vendida o a pedidos
   nuevos? ¿Qué puede ver el cliente de su pedido?
8. Volumen aproximado de mensajes por día en cada canal, para dimensionar el costo de OpenAI y
   la prioridad de cada canal.

## Derivó en
_Pendiente — responder las preguntas abiertas y usar /feature REQ-075 (Etapa 1) para iniciar el desarrollo_
