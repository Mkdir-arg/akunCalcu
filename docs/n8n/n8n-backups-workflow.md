# Workflow n8n — Backup automatizado a Google Drive

> **Versión**: 1.0
> **Estado**: Listo para importar
> **Relacionado**: REQ-028 — Backup automatizado de BD con n8n + Google Drive

---

## Qué hace este workflow

1. Todos los días a las **00:00 hora Argentina (UTC-3)**, n8n dispara el flujo.
2. Hace una llamada **HTTP POST** al endpoint protegido de Django:
   `POST /security/backups/api/create/` con el header `X-Bot-Secret`.
3. Django ejecuta `mysqldump` y devuelve el **archivo SQL como stream binario**.
4. n8n toma esa respuesta y la **sube a Google Drive** en la carpeta `Backups AkunCalcu/`.
5. El registro queda guardado en AkunCalcu con `storage_location='drive'` y aparece en `/security/backups/list/` con la badge **"Auto - Drive"**.

---

## Antes de importar: configurá las credenciales en n8n

1. **Google Drive OAuth2** → conectar la cuenta de Google donde se van a guardar los backups.
   - Crear (o elegir) una carpeta llamada `Backups AkunCalcu` en Drive.
   - Copiar el **ID de la carpeta** (lo ves en la URL al abrirla: `drive.google.com/drive/folders/<ID>`).
2. **Header Auth credential** (o usar header directo en el nodo HTTP):
   - Name: `X-Bot-Secret`
   - Value: el mismo valor que la variable de entorno `BACKUP_BOT_SECRET` en Railway / `.env`.
3. **URL de Django**:
   - Local (docker-compose): `http://web:8000/security/backups/api/create/`
   - **Producción Railway (recomendado, red interna)**: `http://web.railway.internal/security/backups/api/create/` — n8n y `web` están en el mismo proyecto Railway, así que se pueden hablar por DNS privado sin salir a internet. Ahorra ancho de banda y es más rápido.
   - Producción Railway (URL pública, fallback): `https://web-production-3be54.up.railway.app/security/backups/api/create/`

---

## Diagrama del flujo

```
[Schedule Trigger 00:00 ARG]
            |
[HTTP Request POST /security/backups/api/create/]
   (Header X-Bot-Secret, Response: File)
            |
[Set: nombre de archivo backup_YYYYMMDD_HHMMSS.sql]
            |
[Google Drive: Upload File a "Backups AkunCalcu/"]
            |
        (FIN)
```

---

## Variables a reemplazar antes de importar

| Placeholder en el JSON | Reemplazar por |
|------------------------|----------------|
| `REEMPLAZAR_URL_DJANGO` | URL del endpoint — usar `http://web.railway.internal/security/backups/api/create/` en producción (red interna Railway) |
| `REEMPLAZAR_BACKUP_BOT_SECRET` | Valor del env `BACKUP_BOT_SECRET` |
| `REEMPLAZAR_DRIVE_FOLDER_ID` | ID de la carpeta "Backups AkunCalcu" en Drive |

---

## Configuración del Schedule Trigger

- **Trigger Interval**: Cron
- **Cron Expression**: `0 0 * * *` (todos los días a las 00:00)
- **Timezone**: `America/Argentina/Buenos_Aires` (configurar a nivel workflow → Settings → Timezone)

> Importante: si la instancia de n8n corre en UTC, igual va a respetar el timezone que se configure en Settings del workflow.

---

## Configuración del nodo HTTP Request

- **Method**: `POST`
- **URL**: `REEMPLAZAR_URL_DJANGO`
- **Authentication**: None (usamos header custom)
- **Headers**:
  - `X-Bot-Secret`: `REEMPLAZAR_BACKUP_BOT_SECRET`
- **Response Format**: `File` (importante — n8n recibe el binario)
- **Property Name For Binary Data**: `data`
- **Timeout**: 600000 ms (10 min, por si el dump es grande)

La respuesta incluye también el header `Content-Disposition: attachment; filename="backup_YYYYMMDD_HHMMSS.sql"` con el nombre sugerido del archivo.

---

## Configuración del nodo Google Drive

- **Operation**: `Upload File`
- **Binary Data**: `true`
- **Binary Property**: `data`
- **File Name**: `={{ $binary.data.fileName }}` (usa el nombre que mandó Django) o `=backup_{{$now.format('yyyyMMdd_HHmmss')}}.sql`
- **Parent Folder**: `REEMPLAZAR_DRIVE_FOLDER_ID`

---

## JSON del Workflow — Copiar y pegar en n8n

> **Cómo importar**: n8n → menú (☰) → Import from File → seleccionar `n8n-backups-workflow.json`

El JSON está en el archivo gemelo: [`n8n-backups-workflow.json`](./n8n-backups-workflow.json)

---

## Cómo probar manualmente

1. Importar el workflow en n8n y completar los 3 placeholders.
2. Activar el workflow.
3. En n8n, hacer click en **Execute Workflow** (corrida manual sin esperar al cron).
4. Verificar:
   - El nodo HTTP Request devuelve 200 y un binario.
   - El nodo Google Drive sube el archivo correctamente.
   - En AkunCalcu `/security/backups/list/` aparece una nueva fila con badge **"Auto - Drive"** y estado **Completado**.
5. Si el HTTP Request devuelve **403** → revisar que el header `X-Bot-Secret` coincida con la env var del servidor.
6. Si devuelve **500** → revisar `error_message` del Backup en la lista (probablemente un problema con `mysqldump` en el contenedor).

---

## Notas operativas

- **Retención en Drive**: el endpoint de Django no borra backups viejos en Drive. La política de retención se maneja desde Google Drive o con un workflow extra de limpieza.
- **Tamaño**: el endpoint usa streaming (`StreamingHttpResponse`), así que aguanta dumps grandes sin cargarlos en memoria.
- **Seguridad**: el middleware `/security/backups/api/` está exento de auditoría para no llenar la tabla `AuditLog` con cada corrida diaria.
- **Falla silenciosa**: si `mysqldump` falla, el Backup queda con `status='failed'` y `error_message` con el detalle. Conviene monitorear desde n8n (agregar un nodo de notificación por Telegram si interesa).
