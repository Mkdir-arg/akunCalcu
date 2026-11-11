# REQ-075 — Atención autónoma de clientes por WhatsApp, email e Instagram
**Estado**: En desarrollo
**Fecha**: 2026-11-11
**Solicitante**: Dirección

## Descripción de la idea
Un asistente **autónomo** que atiende a los clientes que escriben por WhatsApp, email o
Instagram. Debe sonar y sentirse como una persona del equipo de Akuna, y no hace falta un
vendedor para cerrar el circuito de cotización:

1. Responde la consulta y releva lo que necesita para cotizar.
2. **Aluminio**: arma el presupuesto con el cotizador de AkunCalcu y lo envía en PDF por el
   mismo canal.
3. **PVC**: le avisa al cliente que el presupuesto va a estar listo en 24 horas y asigna la
   gestión a una persona de Akuna. Cuando esa persona lo termina, el bot lo envía en la misma
   conversación.
4. Si el cliente avanza, **confirma la visita técnica** (medición) en la agenda.
5. Lo que no puede resolver lo deriva a **visita técnica** o a **dirección**.

Se usa un LLM (GPT o Claude) para la conversación. Los precios los calcula siempre el cotizador.

## Decisiones tomadas (2026-11-11)
| Tema | Decisión |
|---|---|
| Materiales | Aluminio: cotiza el bot solo. PVC: «en 24 horas» + asignación a una persona de Akuna |
| Alcance del bot | Envía el presupuesto y confirma la visita técnica. **El cobro queda para una etapa posterior** |
| Descuentos | **No** por ahora |
| Lo que el bot no resuelve | Visita técnica o dirección |
| Límite de monto | **Sin límite**: el bot envía presupuestos de cualquier monto |
| Tono | Humano y natural, que no se perciba como un robot |
| Configuración por defecto de cada abertura | Sale de la **base de datos** (catálogo `pricing` + historial de presupuestos), no de una carga manual |
| Asignación de PVC | A las **vendedoras** (rotación por turnos existente de `solicitudes`) |
| Visita técnica | Se asigna al **técnico** (`EventoAgenda.tecnico`) |
| Firma | **Matías Fariña** |
| Horario | Fuera de horario no responde: **espera a las 8 de la mañana** |
| WhatsApp | El número **oficial de Akun registrado en Meta** (el mismo de la Cloud API) |
| Email | El email de Akun |
| Horario de atención | Configurable desde un **módulo nuevo en AkunCalcu** |
| Visita técnica (días, franjas, zonas, costo) | Configurable en el mismo módulo |
| Plazo de PVC | **24 horas hábiles** (según el horario configurado) |
| Base de conocimiento | Se escribe en el mismo módulo |
| Email | El mismo Gmail que ya lee el workflow de reparto |
| Volumen | **15 a 20 consultas por día** que se convierten en conversación |
| Instagram | La cuenta **no es profesional**: hay que convertirla y vincularla a una página de Facebook antes de integrarla |

## Problema que resuelve
- Hoy cada mensaje lo lee y lo contesta una persona. La primera respuesta tarda horas y
  fuera de horario no hay respuesta.
- Los datos para cotizar llegan incompletos y hay ida y vuelta para conseguirlos.
- Solo el email está integrado (REQ-037), y solo para repartir: nadie le contesta al cliente.
  WhatsApp e Instagram no pasan por el sistema.
- Las conversaciones no quedan registradas ni vinculadas al cliente, la solicitud o el presupuesto.

## Usuarios beneficiados
- **Clientes**: respuesta y presupuesto en minutos, a cualquier hora, en su canal.
- **Equipo de Akuna**: deja de cotizar aluminio estándar a mano y solo interviene en PVC,
  visitas técnicas y casos derivados.
- **Dirección**: supervisa conversaciones y métricas (consultas, presupuestos enviados,
  visitas agendadas y conversión por canal).

## Valor para el negocio
- **Si se implementa**: respuesta inmediata (quien responde primero suele quedarse con la
  obra), cotización de aluminio sin intervención humana y registro completo por canal.
- **Si no se implementa**: se siguen perdiendo consultas fuera de horario o en picos de demanda,
  y el tiempo del equipo se va en tareas repetitivas.

## Diseño funcional de la conversación

### Flujo principal
```
Cliente escribe
  └─ Bot: saludo + entiende qué necesita (texto, audio, foto o plano)
       ├─ Consulta general (horarios, zona, plazos, formas de pago) → responde con datos de Akuna
       ├─ Estado de una obra/pedido → consulta el pedido y responde
       ├─ Cotización
       │    ├─ Releva: tipo de abertura, medidas, cantidad, color, vidrio, mosquitero,
       │    │          obra nueva o renovación, localidad, nombre (y teléfono/email si falta)
       │    ├─ Aluminio → cotizador → Presupuesto → PDF por el canal
       │    └─ PVC      → «te lo paso en 24 h» → asignación a persona de Akuna
       │                   → la persona lo carga → el bot lo envía en la misma charla
       ├─ Cliente avanza → confirma visita técnica (fecha y franja) en la agenda
       └─ Fuera de alcance (reclamo, estructura especial, obra grande, enojo, pedido explícito
          de hablar con alguien) → visita técnica o dirección, sin cortar la conversación
```

### Cómo «suena humano»
- **Ritmo**: espera de 20 a 40 s antes de contestar, para juntar los mensajes que el cliente
  manda seguidos. Muestra «escribiendo…» y parte las respuestas largas en 2 o 3 mensajes cortos.
- **Registro**: rioplatense, con voseo, sin listas largas ni exceso de emojis. Se adapta al
  tono del cliente (formal o informal).
- **Memoria**: reconoce a los clientes que vuelven («¡Hola de nuevo, Juan! ¿Seguimos con lo de
  la ventana del living?») y recuerda lo que ya se habló, por cualquier canal.
- **Multimedia**: entiende audios (transcripción) y fotos o croquis con medidas (visión).
- **Continuidad**: cuando interviene una persona (PVC, dirección), lo hace en el mismo hilo y
  con el historial completo, así que para el cliente es la misma conversación.
- **Firma**: Matías Fariña. Si el cliente pregunta directamente si es un bot, no lo niega
  (ver Riesgos).
- **Horario**: los mensajes que llegan fuera de horario se contestan a las 8 de la mañana,
  como lo haría una persona.

### Mensajes clave (por definir con Akuna)
- Presupuesto aluminio: PDF + resumen corto + invitación a coordinar la medición.
- PVC: «Perfecto, el de PVC lo armamos a medida con el proveedor. Mañana a esta hora lo tenés».
- Visita: propuesta de 2 o 3 franjas disponibles y confirmación.
- Seguimiento: a los 3 y 7 días sin respuesta (plantilla de Meta si pasaron 24 h).

## Viabilidad técnica
Es viable con el stack actual: Django, n8n en Railway, Meta Cloud API, Gmail y un LLM.

**Piezas que ya existen y se reutilizan:**

| Pieza | Qué aporta |
|---|---|
| `solicitudes` + workflow n8n «Solicitudes Presupuesto - Reparto» | Clasificación de mails con IA, reparto por turnos (sirve para asignar PVC), anti-spam, API con `X-Bot-Secret` |
| Workflow n8n «Solicitudes Presupuesto - Recordatorios» | Base para controlar que el PVC salga dentro de las 24 h |
| Workflow «WhatsApp Gastos Diarios v2 (Meta Cloud API)» | Webhook de Meta verificado, normalización de eventos, transcripción de audios, envío dentro de la ventana de 24 h, detección de envíos fallidos |
| `pricing.services.calculator.calcular_precio()` | Precio con `marco_id` + `ancho_mm` + `alto_mm` (+ hoja, vidrio, color, tratamiento, opcionales) |
| `presupuestos.Presupuesto` (FK a `SolicitudPresupuesto`) + PDF | Presupuesto vinculado a la solicitud, con PDF |
| `presupuestos.importar_rehau` (FEAT-039) | Carga del PVC por la persona asignada |
| `core/whatsapp.py` (`subir_pdf`, `enviar_plantilla_documento`) | Envío del PDF por WhatsApp, también fuera de las 24 h con plantilla |
| `agenda` (REQ-031) | Base para agendar la visita técnica |
| `pedidos` | Estado de la obra para responder «¿cómo va lo mío?» |

**Arquitectura propuesta**: Django guarda el estado y la lógica de negocio. n8n conecta canales
y LLM.

```
WhatsApp (Meta) ─┐                               ┌─ buscar_cliente / historial
Instagram (Meta) ┼─► n8n: normaliza + espera ────┼─ catalogo_tipologias
Gmail ───────────┘   (junta mensajes seguidos)   ├─ cotizar_aluminio → Presupuesto + PDF
                              │                  ├─ derivar_pvc → asignación + plazo 24 h
                              ▼                  ├─ franjas_visita / confirmar_visita
                   Agent n8n (LLM) ── tools ─────┼─ estado_pedido
                              │                  └─ derivar (visita técnica | dirección)
                              ▼                        (todas son APIs de Django)
              respuesta por el mismo canal y el mismo hilo
```

- **App nueva `conversaciones`**: `Conversacion` (canal, id externo del contacto, FK opcional a
  `Cliente`, `SolicitudPresupuesto` y `Presupuesto`, estado `bot` / `esperando_pvc` /
  `derivada` / `cerrada`) y `Mensaje` (dirección, autor bot/persona/cliente, texto, adjuntos,
  id externo para no duplicar).
- **Configuración por defecto desde la base** (pieza central): el bot ofrece los productos
  activos del catálogo `pricing` (los inactivos ya quedan fuera, FEAT-041). Para cada tipo de
  abertura toma como configuración por defecto (marco, hoja, vidrio, color, margen) **la más
  usada en los presupuestos de aluminio del último período**, que sale de
  `ItemPresupuesto.resultado_json`. Lo que el cliente especifica (color, DVH, mosquitero)
  reemplaza al valor por defecto. Dirección puede fijar a mano un valor para pisar el inferido.
- **Usuario de sistema «bot»**: `Presupuesto.created_by` es obligatorio, así que los
  presupuestos del bot quedan a nombre de ese usuario.
- **Supervisión**: panel para dirección con las conversaciones en vivo, la posibilidad de
  intervenir en cualquier momento y métricas. Es para supervisar, no para operar.

**Modelo de IA**: hoy n8n usa OpenAI `gpt-4o-mini` para clasificar mails y extraer gastos.
Para la conversación conviene un modelo más capaz, porque el tono humano y el uso correcto de
las herramientas son lo crítico. Opciones: Claude (`claude-opus-5-5`, o `claude-sonnet-5-5` si
se prioriza el costo) o un modelo actual de OpenAI. El Agent de n8n permite cambiar de modelo
sin rehacer el flujo, así que la recomendación es probar ambos con conversaciones reales
anonimizadas y elegir por calidad y costo. La clasificación simple puede quedar en el modelo
barato que ya funciona.

## Apps / módulos afectados
- **Nueva**: `conversaciones` (models, APIs para n8n, panel de supervisión, tests).
- `pricing`: modelo y ABM del catálogo de tipologías del bot, y servicio tipología → configuración.
- `presupuestos`: creación desde la API, envío del PDF por el canal de origen, aviso al bot
  cuando un PVC queda listo.
- `solicitudes`: valores nuevos en `origen` (`whatsapp`, `instagram`) y asignación del PVC con
  plazo de 24 h.
- `agenda`: franjas disponibles para visita técnica y confirmación desde el bot.
- `comercial.Cliente`: búsqueda y alta por teléfono, email o usuario de Instagram.
- `pedidos`: consulta de estado (solo lectura).
- **n8n**: router común para el webhook de Meta (separa personal interno de clientes),
  workflow de Instagram, respuesta en el hilo de Gmail y Agent conversacional.
- Panel de salud (FEAT-035): latido de los canales nuevos.

## Complejidad estimada
**Grande**. Etapas propuestas, cada una con su `/feature`:

1. **Base + WhatsApp**: módulo «Configuración del asistente», `conversaciones`, router de Meta, Agent con tono humano, relevamiento,
   consultas generales, derivación y panel de supervisión.
2. **Cotización aluminio**: catálogo de tipologías, cotización con el cotizador y envío del PDF.
3. **PVC + visita técnica**: asignación con plazo de 24 h, envío del PDF cuando está listo y
   agenda de visitas.
4. **Email**: respuesta en el hilo de Gmail sobre la misma base.
5. **Instagram**: cuando la cuenta sea profesional y Meta apruebe el permiso de mensajes.
6. **Posterior (fuera de este REQ)**: cobro de la seña, descuentos y seguimientos automáticos.

## Dependencias o riesgos
- **Número de WhatsApp**: el número de la Cloud API ya se usa para gastos, agenda y resumen, y
  hoy un número no habilitado recibe un 403 y no se le responde. Hace falta un router que separe
  personal de clientes. Si los clientes escriben a otro número que se atiende desde la app
  WhatsApp Business, hay que sumarlo a la Cloud API (el modo coexistencia permite seguir usando
  la app).
- **Evolution API**: el aviso al vendedor sale por Evolution, que no es oficial. Con clientes
  hay que usar solo la API oficial de Meta, por riesgo de bloqueo del número.
- **Ventana de 24 h**: el PVC se entrega cerca del límite de las 24 h. En WhatsApp, fuera de la
  ventana solo se puede escribir con plantilla aprobada (ya existe `enviar_plantilla_documento`).
  Instagram es más restrictivo, así que conviene que el bot pida un WhatsApp o un email al
  cotizar PVC.
- **Instagram**: cuenta profesional vinculada a una página de Facebook y permiso
  `instagram_manage_messages` aprobado por Meta.
- **Precios**: sin aprobación humana ni tope de monto, un error en el catálogo o en una
  tipología sale directo al cliente. Para mitigarlo:
  - el precio lo calcula siempre el cotizador;
  - el presupuesto aclara «sujeto a medición» y tiene vencimiento;
  - la etapa 2 arranca con un período de prueba en el que el bot cotiza y dirección revisa
    antes de habilitar el envío automático;
  - los precios del catálogo se mantienen al día.
- **Promesa de 24 h en PVC**: si nadie la cumple, el cliente lo nota. Alerta a la persona
  asignada y a dirección antes del vencimiento.
- **Alucinaciones**: el bot solo afirma lo que devuelve Django o la base de conocimiento de
  Akuna (horarios, zonas, plazos, garantías). Si no sabe, deriva.
- **Transparencia**: sonar humano es posible y está bien. El límite recomendado es **no negar
  ser automático si el cliente lo pregunta directamente**, por las regulaciones de
  transparencia de IA y por el daño de confianza si se descubre. Meta permite bots de atención
  propios del negocio, siempre que se mantengan en los temas de la empresa.

## Módulo «Configuración del asistente» (nuevo)
Pantalla en AkunCalcu, con permiso propio (REQ-019), donde dirección define cómo trabaja el bot
sin tocar n8n ni código. El bot lee esta configuración en cada conversación.

| Sección | Qué se configura |
|---|---|
| **Horario de atención** | Días y franjas por día (por ejemplo, lun-vie 8-18, sáb 9-13) y feriados. Fuera de horario el bot espera a la apertura siguiente. Con este horario se calculan las 24 h hábiles de PVC |
| **Técnico y visitas** | Técnico o técnicos que hacen la visita (usuarios), días y franjas disponibles, duración de cada visita, zonas o localidades que cubre, costo de la visita (o sin costo) y cuántas visitas por franja |
| **Base de conocimiento** | Entradas de tema + texto: zonas de cobertura, plazos de fabricación, garantía, formas de pago, qué incluye la colocación, etc. El bot solo afirma lo que está acá o lo que devuelve el sistema |
| **Identidad y tono** | Nombre con el que firma (Matías Fariña), saludo y cierre habituales, indicaciones de tono |
| **Cotización** | Productos de aluminio que el bot puede ofrecer y valores por defecto fijados a mano (si no hay, se usa el más cotizado del historial) |
| **Derivaciones** | Quién recibe lo que se deriva a dirección y qué temas siempre se derivan (reclamos, obras especiales) |
| **Encendido** | Activar o pausar el bot por canal, para cortar rápido si algo sale mal |

## Consecuencias de las decisiones
- **Mismo número para personal y clientes**: el router de Meta es obligatorio en la Etapa 1.
  Los números habilitados (`NumeroWhatsApp` activos) siguen a Gastos, Resumen y Agenda.
  Cualquier otro número va al bot de clientes. Hoy esos mensajes reciben un 403 y quedan sin
  respuesta.
- **Horario y ventana de 24 h**: si entre el último mensaje del cliente y la apertura siguiente
  pasan más de 24 h (por ejemplo, de sábado a la tarde a lunes), WhatsApp solo deja escribir
  con plantilla aprobada por Meta. Hace falta una plantilla de «retomo tu consulta».
- **Firma con nombre real**: el cliente puede llamar o escribir preguntando por Matías. Las
  vendedoras y el técnico tienen que saber que las conversaciones salen con ese nombre y
  tener acceso al historial.
- **Instagram pasa a la última etapa** hasta que la cuenta sea profesional y esté vinculada a
  una página de Facebook. Después, Meta tiene que aprobar el permiso de mensajes.
- **Configuración inferida del historial**: si el historial de un tipo de abertura es chico o
  muy variado, el valor más usado puede no ser representativo. El módulo muestra qué valor
  usa el bot y permite fijarlo.
- **Volumen bajo (15-20 conversaciones por día)**: el costo del LLM es acotado incluso con un
  modelo de primera línea. Se puede usar el modelo más capaz para la conversación sin que el
  costo pese.

## Preguntas abiertas
_Ninguna que bloquee el inicio. Se definen durante el desarrollo: los textos de la base de
conocimiento, la plantilla de Meta de «retomo tu consulta» y la elección final del modelo de
IA (prueba comparativa en la Etapa 1)._

## Derivó en
- Etapa 1a: [FEAT-058](../features/FEAT-058-seccion-agente-configuracion.md) — sección «Agente» (configuración, horario, visitas técnicas y base de conocimiento). Implementado 2026-11-11.
- Etapa 1b (conversaciones, APIs para n8n, router de Meta, asistente en modo prueba): pendiente.
