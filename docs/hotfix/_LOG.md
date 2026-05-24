# Log de Hotfixes — AkunCalcu

> Registro de parches urgentes aplicados directamente sobre producción, fuera del ciclo de sprint normal.

## Formato de entrada

```
### HFX-XXX — Título del hotfix
**Fecha**: YYYY-MM-DD
**Urgencia**: Por qué no podía esperar al próximo sprint
**Feature afectada**: FEAT-XXX o módulo

**Síntoma en producción**: Qué estaba roto.
**Causa raíz**: Por qué ocurría.
**Solución aplicada**: Qué se cambió.
**Archivos modificados**: lista
**Seguimiento**: ¿Requiere fix más profundo en el próximo sprint? Sí/No
```

---

## Hotfixes registrados

### HFX-001 — Fix TLS/SSL en mysqldump para backups en Railway
**Fecha**: 2026-05-22
**Urgencia**: Los backups manuales desde `/security/backups/list/` fallaban en producción, dejando al sistema sin posibilidad de respaldar la BD.
**Feature afectada**: Módulo `security` — backups manuales

**Síntoma en producción**:
- Primer error: `mysqldump: Got error: 2026: "TLS/SSL error: self-signed certificate in certificate chain"` (Railway usa cert auto-firmado para MySQL).
- Segundo error tras intento con `--ssl-mode=DISABLED`: `mysqldump: unknown variable 'ssl-mode=DISABLED'`.

**Causa raíz**: El contenedor instala `default-mysql-client` (Debian slim), que en realidad es **mariadb-client**, no mysql-client. El flag `--ssl-mode=DISABLED` es sintaxis exclusiva de MySQL 5.7+ y no es reconocido por mariadb-client.

**Solución aplicada**: Reemplazar `--ssl-mode=DISABLED` por `--skip-ssl`, que es portable entre ambos clientes y deshabilita la negociación TLS. La conexión va por red privada interna de Railway, por lo que no se pierde seguridad.

**Archivos modificados**:
- `akuna_calc/security/management/commands/create_backup.py` (línea 59 + comentario explicativo)

**Commit**: `37c2858` — "fix: update mysqldump command to use --skip-ssl for compatibility with Railway"

**Seguimiento**: Sí — refactor sugerido en próximo sprint: extraer `_build_mysqldump_command()` para poder testear el armado del comando sin dependencia de DB real. Además, los backups quedan en `/app/backups/` (filesystem efímero del contenedor) — se evaluará feature de automatización con n8n + Google Drive como respaldo externo.
