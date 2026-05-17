# REQ-027 — Desplegar AkunCalcu en Railway

**Estado:** En desarrollo
**Fecha:** 2026-05-17
**Complejidad:** Grande
**Derivó en:** —

---

## User Story

> **Como** dueño/operador de Akuna Aberturas
> **Quiero** que AkunCalcu esté desplegado en Railway con acceso vía URL pública y HTTPS
> **Para** poder usar el sistema desde cualquier dispositivo sin depender de tener mi máquina local prendida, y para que la integración con n8n + Telegram + Evolution API funcione de forma estable.

---

## Contexto

Hoy AkunCalcu corre solo en local vía `docker-compose up`. Esto implica:

- La máquina del usuario tiene que estar prendida para acceder al sistema.
- El bot de Telegram + Evolution API dependen de **ngrok** como túnel temporal, lo que es frágil.
- No hay backup automático ni alta disponibilidad.

Hubo un intento previo de deploy a PythonAnywhere (existen `settings_prod.py` y `wsgi_prod.py` apuntando a `/home/AKUN/...`), pero quedó abandonado. Las credenciales del intento están hardcodeadas en `settings_prod.py` y deben rotarse.

Railway es la plataforma elegida por su soporte nativo de Docker, MySQL managed y precio razonable.

---

## Criterios de Aceptación

### Funcionales
- [ ] La app Django responde en una URL pública de Railway con HTTPS
- [ ] El login funciona con superusuario creado automáticamente en el primer deploy
- [ ] Todas las apps funcionan: comercial, productos, presupuestos, pricing, pedidos, gastos_diarios, plantillas, security, configuracion, facturacion, usuarios, core
- [ ] Los archivos estáticos (CSS, JS, imágenes, Tailwind, Select2) se sirven correctamente
- [ ] Las migraciones se aplican automáticamente en cada deploy
- [ ] El servicio n8n está desplegado en el mismo proyecto Railway y puede hablarle al Django de Railway
- [ ] Evolution API + Postgres + Redis desplegados en el mismo proyecto Railway
- [ ] El bot de Telegram + Evolution API siguen funcionando con webhooks apuntando a Railway (no a ngrok)

### Seguridad
- [ ] `DEBUG=False` en producción
- [ ] `ALLOWED_HOSTS` configurado con el dominio real de Railway (no `*`)
- [ ] `SECRET_KEY` viene de variable de entorno
- [ ] Credenciales de DB vienen de Railway (env vars), nunca hardcodeadas
- [ ] El `settings_prod.py` con credenciales hardcodeadas se reescribe para Railway
- [ ] Se usa `gunicorn` como servidor WSGI, no `runserver`
- [ ] HTTPS forzado, HSTS activo

### Técnicos
- [ ] Funciona con la DB MySQL managed que provee Railway
- [ ] El Dockerfile sirve para Railway (no requiere docker-compose)
- [ ] Logs van a stdout/stderr (Railway los captura)
- [ ] El proceso de deploy queda documentado en `docs/features/FEAT-XXX-deploy-railway.md`

---

## Decisiones tomadas en el análisis

| # | Decisión | Motivo |
|---|----------|--------|
| 1 | DB arranca vacía en producción | El usuario crea superusuario y carga datos desde cero. No migramos datos locales. |
| 2 | n8n + Evolution API + Postgres + Redis van al mismo proyecto Railway | Mantener todo unificado. Más simple de operar. |
| 3 | `settings_prod.py` se reescribe para Railway (no se crea archivo paralelo) | Menos archivos, más limpio. Las credenciales hardcodeadas desaparecen del repo. |
| 4 | Logs solo a stdout (no a archivo) | Railway captura stdout. El filesystem en Railway es efímero, los archivos no persisten. |
| 5 | Despliegue de los 6 servicios en una tirada | El usuario aceptó el riesgo a cambio de avanzar más rápido. |

---

## Riesgos identificados

1. **Costo de infraestructura** — 6 servicios en Railway (Django + MySQL + n8n + Postgres + Redis + Evolution) acumulan consumo. Hay que monitorear el plan.
2. **Migración de webhooks** — Telegram + Evolution apuntan a ngrok hoy. Hay que reapuntarlos a la URL Railway sin perder mensajes en el proceso.
3. **`settings_prod.py` con credenciales versionadas** — ya están en el historial de git. Se reescribe el archivo, pero las credenciales viejas siguen siendo accesibles en el historial. Hay que rotar password del usuario `AKUN` en PythonAnywhere si esa cuenta sigue existiendo.
4. **Filesystem efímero en Railway** — el `LOGS_DIR` actual escribe a `BASE_DIR/logs/security.log`. Hay que sacar ese handler para no llenar disco efímero ni romper en el primer arranque.
5. **Bot de Telegram secret** — `TELEGRAM_BOT_SECRET` actualmente es `akuna-bot-secret-2024` (visible en docker-compose). Se rota al pasar a Railway.

---

## Archivos del proyecto que se ven afectados

Detalle completo en el diseño técnico del Paso 2 (Arquitecto). A grandes rasgos:

- `requirements.txt` — agregar `gunicorn`, `whitenoise`, `dj-database-url`
- `akuna_calc/akuna_calc/settings.py` — leer `ALLOWED_HOSTS` y `CSRF_TRUSTED_ORIGINS` de env, agregar WhiteNoise middleware, sacar logging a archivo
- `akuna_calc/akuna_calc/settings_prod.py` — reescribir completo para Railway
- `Dockerfile` — agregar `collectstatic`, usar gunicorn en el CMD
- `entrypoint.sh` — reemplazar `runserver` por `gunicorn`
- Nuevo: `railway.toml` o configuración del servicio en Railway
- `.env.example` — actualizar con las variables nuevas
- `docs/team/decisions.md` — agregar ADR del deploy a Railway
- `docs/team/changelog.md` — entrada del cambio
- `memory/MEMORY.md` — actualizar contexto

---

## Próximos pasos del flujo

- **Paso 2** (Arquitecto) — Diseño técnico detallado + análisis de impacto completo
- **Paso 3** (Desarrollador) — Implementación de cambios en el código
- **Paso 4** (Reviewer) — Verificación contra criterios y checklist
- **Paso 5** (Documentador) — FEAT-XXX, changelog, ADR, MEMORY
- **Post-Paso 5** — Creación de infraestructura en Railway vía MCP
