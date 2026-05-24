# REQ-028 — Backup automatizado de BD con n8n + Google Drive

**Estado:** Implementado
**Fecha:** 2026-05-24
**Origen:** Necesidad operativa detectada tras HFX-001 (backups en `/app/backups/` son efímeros en Railway).

## User Story

Como administrador de AkunCalcu, quiero que los backups de la base de datos se generen automáticamente todos los días y se guarden en Google Drive, para tener un respaldo externo confiable que sobreviva a reinicios de Railway y me evite la tarea manual.

## Criterios de Aceptación

- [x] Endpoint Django `POST /security/backups/api/create/` protegido con header `X-Bot-Secret`.
- [x] El endpoint ejecuta `mysqldump` (reutiliza lógica de `create_backup.py`) y devuelve el archivo SQL como respuesta binaria.
- [x] El endpoint registra un objeto `Backup` con estado `completed` y campo nuevo `storage_location` (`drive` / `local`).
- [x] Workflow n8n con Schedule Trigger diario que llama al endpoint y sube el SQL a `Backups AkunCalcu/` en Google Drive.
- [x] El workflow se ejecuta automáticamente a las 00:00 hora Argentina (UTC-3) todos los días.
- [ ] Notificación por Telegram al admin si el workflow falla (opcional — pospuesto).
- [x] Documentación del workflow en `docs/n8n/n8n-backups-workflow.md`.
- [x] Variable de entorno `BACKUP_BOT_SECRET` separada de `TELEGRAM_BOT_SECRET`, registrada en `.env.example`.
- [x] Test: endpoint rechaza request sin secret (403) y acepta con secret correcto (200 + SQL).
- [x] `/security/backups/list/` muestra los backups creados por el bot con badge "Auto - Drive".

## Fuera de alcance

- Programar el cron desde la UI de `/security/backups/settings/`.
- Restore automático desde Drive.
- Retención automática de backups antiguos en Drive.

## Estimación

Mediano.

## Riesgos identificados

- El archivo SQL puede ser grande y consumir RAM si se carga entero en memoria → usar `StreamingHttpResponse`.
- Si el endpoint API queda expuesto sin proteger correctamente, alguien podría exfiltrar el dump completo → secret debe ser largo (>= 32 chars), por header, y no loguearse.

## Derivó en

[FEAT-012](../features/FEAT-012-backup-automatizado-n8n-drive.md).
