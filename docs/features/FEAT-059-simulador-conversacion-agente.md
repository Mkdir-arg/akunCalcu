# FEAT-059 — Simulador de conversación del agente

**Estado:** Implementado (falta probar contra OpenAI con la key cargada)
**Fecha:** 2026-11-11
**Requerimiento:** [REQ-076](../requerimientos/REQ-076-simulador-conversacion-agente.md) (relacionado con REQ-075)
**ADR:** [ADR-033](../team/decisions.md)

## Qué hace

Nueva opción **Agente → Simulador**: una persona de Akun le escribe al asistente **como si fuera un
cliente** y ve cómo responde con la configuración real del menú Agente (firma, tono, modelo,
horario y base de conocimiento). No envía nada a nadie.

- **Listado** de simulaciones (número, cliente, canal, quién la hizo, cantidad de mensajes, último
  movimiento), paginado, con el formulario **Nueva conversación**: canal (WhatsApp, email o
  Instagram), nombre del cliente de prueba y, opcionalmente, **fecha y hora simulada**.
- **Chat**: burbujas del cliente (derecha) y del asistente (izquierda) con hora, indicador
  «… está escribiendo», Enter para enviar y Shift+Enter para saltar de línea.
- **Detrás de escena** en cada respuesta: entradas de la base de conocimiento usadas, acción que el
  asistente habría tomado (ninguna, derivar a dirección, derivar a visita técnica) con su motivo,
  modelo y tokens consumidos.
- **Fuera de horario**: si el momento simulado cae fuera del horario o en un día cerrado, aparece una
  nota con cuándo saldría la respuesta en un canal real.
- **Errores**: sin API key o con OpenAI caído, el chat muestra el motivo y la conversación sigue.

## Criterios de aceptación

| Criterio | Estado |
|---|---|
| Opción Simulador en el menú Agente, con permiso `agente.simulador` | ✅ |
| Chat con burbujas, hora, Enter para enviar e indicador «escribiendo…» | ✅ |
| Responde con la configuración real (firma, tono, modelo, conocimiento activo) | ✅ |
| Canal simulado y nombre de cliente opcional | ✅ |
| Fecha y hora simulada para probar fuera de horario y días cerrados | ✅ |
| Nunca envía nada ni crea clientes, presupuestos ni visitas | ✅ |
| Simulaciones guardadas y reabribles desde un listado | ✅ |
| Panel «Detrás de escena» | ✅ |
| Mensaje claro sin API key o con error de OpenAI, sin perder la conversación | ✅ |
| Tests sin llamar a OpenAI de verdad | ✅ |

## Cómo funciona el motor (`agente/motor.py`)

1. Guarda el mensaje del cliente.
2. Calcula el estado del horario para el momento de la conversación (`agente/horario.py`); si está
   cerrado agrega la nota del sistema.
3. Arma el contexto: identidad y firma, estilo según el canal, indicaciones de tono, nombre del
   cliente, momento y horario, reglas (solo afirmar lo que está en la base, derivar lo que no sabe,
   no negar ser automático si se lo preguntan directamente) y las entradas activas de la base,
   numeradas. Suma los últimos 30 mensajes del historial.
4. Pide a OpenAI (`agente/openai_cliente.py`, Chat Completions con salida JSON estricta) una respuesta
   con `mensajes` (1 a 3), `entradas_usadas` y `accion` (`tipo` + `motivo`).
5. Guarda las burbujas; el detrás de escena queda en el `detalle` de la última. En simulación la
   acción solo se registra.

El mismo motor es el que van a usar los canales reales en la Etapa 1b de REQ-075.

## Archivos

**Nuevos — `akuna_calc/agente/`**
- `horario.py`: `estado_horario(momento)` → abierto, día cerrado y próxima apertura.
- `openai_cliente.py`: `pedir_json(modelo, mensajes, nombre_schema, schema)` con `urllib`, key en
  `OPENAI_API_KEY`, corte a los 25 s, `reasoning_effort: low` en modelos de razonamiento y errores
  como `OpenAIError`.
- `motor.py`: `responder(conversacion, texto)` y el armado del contexto.
- `migrations/0002_conversacion_mensaje.py`: modelos `Conversacion` (canal, contacto, `es_simulacion`,
  iniciada por, fecha y hora simulada) y `Mensaje` (rol, texto, `detalle` JSON).
- `templates/agente/simulador_list.html`, `templates/agente/simulacion.html`.
- `tests_simulador.py` (18 tests).

**Modificados**
- `agente/models.py`, `forms.py` (`SimulacionForm`, `MensajeSimuladoForm`), `views.py`, `urls.py`, `admin.py`.
- `usuarios/access_control.py`: opción «Simulador» y rutas del permiso `agente.simulador`.

## Decisiones técnicas

- **Motor de conversación en Django**, no en n8n (ADR-033): se testea, las herramientas son funciones de
  Django y simulación y canales reales comparten el mismo código. n8n queda como transporte.
- **Sin SDK de OpenAI**: `urllib` como en `core/whatsapp.py`, sin dependencias nuevas.
- **Salida JSON con schema estricto**: permite partir en burbujas y tener el detrás de escena sin
  interpretar texto libre. Si igual llega fuera de formato, se muestra como texto y se marca.
- **`Conversacion` y `Mensaje` genéricos** con `es_simulacion`: la Etapa 1b les agrega los datos del
  contacto real en lugar de crear otras tablas.
- **Llamada síncrona**: la vista espera a OpenAI (hasta 25 s, gunicorn corta a los 30 s). Aceptable para
  el simulador; para los canales reales se revisa.

## Puesta en marcha

1. Cargar `OPENAI_API_KEY` en las variables del servicio de Django en Railway.
2. `python manage.py migrate agente`
3. Asignar el permiso «Agente → Simulador» a quien lo vaya a usar (acceso total ya lo ve).
4. Cargar horario y base de conocimiento, y empezar una simulación.

## Pendiente

- Probar contra OpenAI con la key cargada (los tests simulan la respuesta del modelo).
- Comparar modelos y ajustar las indicaciones de tono con conversaciones reales anonimizadas.
