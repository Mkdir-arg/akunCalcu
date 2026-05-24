# FEAT-012 — Backup automatizado de BD con n8n + Google Drive

**Estado:** Implementado
**Fecha:** 2026-05-24
**Requerimiento origen:** [REQ-028](../requerimientos/REQ-028-backup-automatizado-n8n-drive.md)
**Sprint:** —

## Descripción funcional

Se incorpora una integración con n8n que dispara todos los días a las 00:00 hora Argentina (UTC-3) un backup de la base de datos y lo sube a una carpeta de Google Drive (`Backups AkunCalcu/`). Django expone un endpoint protegido por header secret que ejecuta `mysqldump` y devuelve el archivo SQL como respuesta binaria streameada. El registro del backup queda persistido en AkunCalcu con `storage_location='drive'` y se muestra en `/security/backups/list/` con badge **"Auto - Drive"**, distinguiéndolo de los backups manuales (`storage_location='local'`).

Esto reemplaza la dependencia anterior del filesystem local del contenedor (efímero en Railway) por un respaldo externo confiable.

## Criterios de aceptación cumplidos

- [x] Endpoint Django `POST /security/backups/api/create/` protegido con header `X-Bot-Secret`.
- [x] El endpoint ejecuta `mysqldump` (reutiliza lógica de `create_backup.py`) y devuelve el archivo SQL como respuesta binaria.
- [x] El endpoint registra un objeto `Backup` con estado `completed` y campo nuevo `storage_location` (`drive` / `local`).
- [x] Workflow n8n con Schedule Trigger diario que llama al endpoint y sube el SQL a `Backups AkunCalcu/` en Google Drive.
- [x] El workflow se ejecuta automáticamente a las 00:00 hora Argentina (UTC-3) todos los días.
- [ ] Notificación por Telegram al admin si el workflow falla (opcional — pospuesto, se documenta como mejora futura).
- [x] Documentación del workflow en `docs/n8n/n8n-backups-workflow.md` (+ JSON gemelo).
- [x] Variable de entorno `BACKUP_BOT_SECRET` separada de `TELEGRAM_BOT_SECRET`, registrada en `.env.example`.
- [x] Test: endpoint rechaza request sin secret (403) y acepta con secret correcto (200 + SQL + Backup creado).
- [x] `/security/backups/list/` muestra los backups creados por el bot con badge **"Auto - Drive"**.

## Archivos modificados / creados

**Backend Django:**
- `akuna_calc/security/models.py` — campo `storage_location` (`local` / `drive`) en modelo `Backup`.
- `akuna_calc/security/migrations/0003_backup_storage_location.py` — migración.
- `akuna_calc/security/views.py` — endpoint `backup_api_create` (StreamingHttpResponse + subprocess.Popen + validación header secret).
- `akuna_calc/security/urls.py` — ruta `backups/api/create/`.
- `akuna_calc/security/middleware.py` — `/security/backups/api/` agregado a `SECURITY_EXEMPT_PREFIXES` (bypass SecurityMiddleware) y a `AuditMiddleware.EXCLUDED_PATHS` (no llenar `AuditLog` con la cron diaria).
- `akuna_calc/security/tests.py` — clase `BackupApiCreateTest` con 4 tests (sin header, secret incorrecto, secret válido, GET no permitido).

**Frontend:**
- `akuna_calc/security/templates/security/backup_list.html` — badge **"Auto - Drive"** cuando `storage_location == 'drive'`.

**Configuración / docs:**
- `.env.example` — variable `BACKUP_BOT_SECRET`.
- `docs/n8n/n8n-backups-workflow.json` — workflow listo para importar (Schedule Trigger v1.2 → HTTP Request v4.2 → Google Drive Upload v3).
- `docs/n8n/n8n-backups-workflow.md` — instructivo con placeholders, diagrama, configuración de nodos y testing.

## Decisiones técnicas

1. **Streaming en lugar de cargar el dump en memoria.** El endpoint usa `StreamingHttpResponse` envolviendo el stdout del `subprocess.Popen` de `mysqldump`, así soporta dumps grandes sin consumir RAM del contenedor.
2. **Autenticación por header secret, no por OAuth ni IP allowlist.** Más simple para n8n y suficiente para un endpoint con un único consumidor automatizado. Secret separado del de Telegram (`BACKUP_BOT_SECRET`) para poder rotarlo independientemente.
3. **Cron en n8n, no en Django.** Evita meter `django-crontab` / Celery solo para este caso. n8n ya está en la infraestructura del proyecto y maneja timezone, retries y errores visualmente.
4. **Exención explícita en ambos middlewares de `security`.** El path `/security/backups/api/` se exime tanto del `SecurityMiddleware` (no aplica chequeo de IP/sesión) como del `AuditMiddleware` (no genera `AuditLog` por cada corrida diaria). Si en el futuro se quiere trazabilidad de las corridas, conviene loguearlas explícitamente desde la view, no via middleware.
5. **`storage_location` como string corto en lugar de FK a una tabla nueva.** Solo dos valores hoy (`local`, `drive`); si crece a más destinos (S3, Dropbox, etc.) se promoverá a `choices` formal o tabla.

## Cómo activar en producción

1. Configurar env var `BACKUP_BOT_SECRET` en Railway (mínimo 32 caracteres, distinto al de Telegram).
2. En n8n: importar `docs/n8n/n8n-backups-workflow.json`, reemplazar los 3 placeholders (`REEMPLAZAR_URL_DJANGO`, `REEMPLAZAR_BACKUP_BOT_SECRET`, `REEMPLAZAR_DRIVE_FOLDER_ID`) y conectar la credencial OAuth de Google Drive.
3. Ejecutar manualmente el workflow una vez para validar; debe aparecer un backup nuevo en `/security/backups/list/` con badge "Auto - Drive".
4. Activar el workflow para que el Schedule Trigger arranque a las 00:00 ARG.

## Mejoras futuras (fuera de alcance)

- Notificación por Telegram si el workflow n8n falla.
- Programar la frecuencia desde `/security/backups/settings/`.
- Retención automática de backups antiguos en Drive.
- Restore directo desde Drive a la base activa.
