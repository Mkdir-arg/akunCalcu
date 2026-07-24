# REQ-040 — Horario del evento en la agenda

- **Estado:** En desarrollo
- **Fecha:** 2026-07-24
- **Solicitante:** Usuario (dueño del negocio)
- **Módulo:** `agenda`

## Contexto / Problema

Los eventos de agenda (`EventoAgenda`) tienen `fecha_evento` (fecha del evento) y `hora_envio`
(hora a la que se dispara el recordatorio de WhatsApp), pero **no existe un campo para el horario
real del evento**. Para colocaciones, mediciones o visitas, hoy el horario se escribe a mano en la
descripción y se pierde entre el texto: no se ve de forma destacada ni en el listado ni en el
mensaje de WhatsApp.

## User Story

> Como usuario de la agenda quiero registrar el horario en que ocurre el evento (colocación,
> visita, medición, etc.), separado de la hora de envío del recordatorio, para verlo de forma
> clara en la agenda y en el WhatsApp sin tener que escribirlo en la descripción.

## Criterios de Aceptación

- [ ] Al crear o editar un evento de agenda existe un campo **"Horario del evento"** (hora), opcional.
- [ ] El campo es independiente de la **"Hora de envío"** del recordatorio, que mantiene su comportamiento actual.
- [ ] Si el evento tiene horario cargado, se muestra en el listado/calendario de la agenda junto a la fecha.
- [ ] Si el evento tiene horario cargado, el mensaje de WhatsApp lo incluye junto a la fecha (ej. `📅 24/07/2026 🕐 14:30`).
- [ ] Los eventos existentes (sin horario) siguen funcionando igual: no se rompe nada y simplemente no muestran horario.

## Complejidad estimada

**Pequeño** — un campo nuevo en un model existente + form + template + mensaje. Requiere migración.

## Relación con backlog

No está relacionado con ítems pendientes del backlog. Extiende el módulo de Agenda (REQ-031).

## Derivó en

_Pendiente._
