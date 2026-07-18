# REQ-037 — Reparto automático de solicitudes de presupuesto por email

- **Estado:** Implementado
- **Fecha:** 2026-07-18
- **Complejidad:** Grande
- **Derivó en:** FEAT-025

## Contexto

Hoy los pedidos de presupuesto llegan por email a la casilla de la empresa (Gmail /
Google Workspace) y una persona los reparte **a mano** entre los vendedores. Se busca
automatizar ese reparto con **n8n + AkunCalcu**, repartiendo por turnos (round-robin) y
dejando trazabilidad dentro del sistema.

## User Story

```
Como responsable comercial de Akuna
quiero que los pedidos de presupuesto que llegan por email a la casilla de la empresa
se repartan automáticamente y por turnos entre los vendedores
para que ningún pedido quede sin atender y no tenga que distribuirlos a mano.
```

## Criterios de aceptación

- [ ] Existe un endpoint API que recibe una solicitud (nombre, email, teléfono, mensaje)
  autenticado con header `X-Bot-Secret`, y crea un registro `SolicitudPresupuesto`.
- [ ] Al crearse, la solicitud se asigna automáticamente al próximo vendedor por turnos
  (round-robin), con el puntero de "último asignado" persistido en la base de datos.
- [ ] Solo entran en la rotación los usuarios con Rol de sistema "vendedor" que tengan
  Email cargado.
- [ ] El endpoint devuelve los datos del vendedor asignado (nombre, email, teléfono) para
  que n8n reenvíe el mail y avise por WhatsApp.
- [ ] Existe un panel `/solicitudes/` que lista las solicitudes con estado, vendedor
  asignado y fechas, con filtros y paginación.
- [ ] Cada solicitud puede marcarse como "contestada" de forma manual (desde el panel) y
  automática (vía lógica/endpoint cuando el vendedor responde).
- [ ] Se puede reasignar una solicitud a otro vendedor manualmente desde el panel.
- [ ] Mientras una solicitud siga sin contestar, se dispara un recordatorio cada 1 hora al
  vendedor asignado.
- [ ] El workflow de n8n (Gmail Trigger → IA clasifica/extrae → POST a AkunCalcu →
  reenvío + WhatsApp) queda documentado en `docs/n8n/`.

## Decisiones tomadas con el usuario

- **Criterio de reparto:** round-robin (por turnos, equitativo). La decisión de a quién le
  toca la lleva Django (puntero en DB), no n8n.
- **Pool de rotación:** todos los usuarios con Rol de sistema "vendedor" y Email cargado.
- **Aviso al vendedor:** WhatsApp + reenvío de Gmail (ambos).
- **Marcar "contestada":** manual y automático.
- **Recordatorio:** cada 1 hora mientras la solicitud siga sin contestar.
- **Casilla:** Gmail / Google Workspace (nodo Gmail Trigger en n8n).

## Notas

- Se apoya en infra existente: roles de sistema (FEAT-009), patrón `X-Bot-Secret`
  (pedidos/backups), WhatsApp Evolution y n8n.
