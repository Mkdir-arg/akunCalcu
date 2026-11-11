# REQ-076 — Simulador de conversación del agente
**Estado**: Implementado
**Fecha**: 2026-11-11
**Solicitante**: Dirección
**Relacionado con**: [REQ-075](./REQ-075-atencion-automatica-clientes-omnicanal.md)

## Descripción de la idea
Una pantalla tipo chat dentro de la sección «Agente» donde una persona de Akun le escribe al
asistente **como si fuera un cliente** y ve cómo responde, con la configuración real (firma,
tono, modelo, horario, técnicos y base de conocimiento). Sirve para probar y ajustar el
asistente antes de prenderlo en WhatsApp, email o Instagram, sin que ningún cliente real
reciba nada.

## User Story
> **US-076** — Como dirección, quiero simular una conversación con el asistente desde AkunCalcu,
> escribiendo como si fuera un cliente, para ver cómo responde con la configuración actual y
> ajustarla antes de que atienda a clientes reales.

## Criterios de aceptación
- [x] En el menú **Agente** aparece **Simulador**, con su propio permiso (`agente.simulador`).
- [x] Pantalla de chat: los mensajes del «cliente» y los del asistente se ven en burbujas
      distintas, con hora; hay una caja para escribir, botón Enviar (y Enter) y un indicador
      «escribiendo…» mientras el asistente responde.
- [x] El asistente responde con la **configuración real** del menú Agente: firma, indicaciones
      de tono, modelo de IA y base de conocimiento (solo entradas activas).
- [x] Al empezar se elige el **canal simulado** (WhatsApp, email o Instagram) y, opcionalmente,
      un **nombre de cliente** de prueba.
- [x] Se puede simular **fecha y hora** para probar qué responde fuera del horario de atención o
      en un día cerrado.
- [x] El simulador funciona **aunque los canales estén apagados y con modo prueba activo**: nunca
      envía nada por WhatsApp, email ni Instagram, y no crea clientes, solicitudes, presupuestos
      ni visitas reales.
- [x] Botón **Nueva conversación** para empezar de cero. Las conversaciones simuladas se guardan y
      se pueden volver a abrir desde un listado (quién la hizo, cuándo, canal, cantidad de mensajes).
- [x] Panel **«Detrás de escena»** en cada respuesta: qué entradas de la base de conocimiento usó y
      qué acciones habría hecho (por ejemplo, «derivar a dirección»), para entender por qué
      respondió eso.
- [x] Si falta la API key de OpenAI o el servicio falla, se muestra un mensaje claro en el chat y
      la conversación no se pierde.
- [x] Tests: modelos, vistas (status, login, permiso) y el armado del pedido al modelo **sin
      llamar a OpenAI de verdad** (respuesta simulada en los tests).

## Fuera de este requerimiento
- Cotizar, derivar PVC y agendar visitas de verdad: el simulador las va a mostrar como «acción
  que habría hecho» a medida que se implementen en las etapas siguientes de REQ-075.
- Conectar los canales reales (Etapa 1b de REQ-075 en adelante).

## Valor
- Probar el tono «Matías» y la base de conocimiento sin riesgo, antes de salir en vivo.
- El mismo motor de conversación que usa el simulador es el que después van a usar los canales
  reales: se construye y se prueba una sola vez.
- Las conversaciones simuladas sirven de casos de prueba para comparar modelos o cambios de tono.

## Complejidad estimada
**Grande**: es el primer uso del motor de conversación (armado del contexto, llamada al modelo,
historial), más la pantalla de chat y el listado.

## Preguntas abiertas
- ¿Dónde vive el motor de conversación: en Django (llamando a OpenAI) o en n8n? Lo define el
  Arquitecto en el Paso 2.

## Derivó en
[FEAT-059](../features/FEAT-059-simulador-conversacion-agente.md) — implementado 2026-11-11 (falta probar contra OpenAI con la key cargada).
