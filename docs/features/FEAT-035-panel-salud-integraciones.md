# FEAT-035 — Panel de salud de las integraciones

- **Estado:** Implementado
- **Fecha:** 2026-08-01
- **Requerimiento:** [REQ-045](../requerimientos/REQ-045-panel-salud-integraciones.md)
- **App principal:** `security` · toca `usuarios` (menú y rutas públicas)

## Qué hace

Una pantalla en **Seguridad → Salud del sistema** (`/security/salud/`) con un semáforo por
integración: **OK** / **Atención** / **Falla** / **Sin datos**. Vigila los workflows de n8n, el
backup a Google Drive, las migraciones pendientes en producción y —lo más importante— si n8n
todavía **puede leer** la casilla del reparto.

Nació de tres incidentes que estuvieron invisibles días:

| Qué pasó | Tardó en verse | Por qué nadie lo vio |
|---|---|---|
| La credencial OAuth de Gmail expiró y el reparto dejó de leer | 25 horas | un trigger que no puede leer **no genera ejecución**: en n8n no hay nada rojo |
| El backup dejó de subir a Drive | 9 días | la ejecución sí queda en rojo, pero nadie la abre |
| El reparto procesaba 1 mail de cada 20 (FIX-020) | desde su creación | `onError: continueRegularOutput` deja la ejecución en "success" |

## El problema de fondo: el silencio no significa lo mismo en todos lados

La distinción que organiza todo el diseño:

- **Workflows con schedule** (recordatorios 08:00, backup 00:00): corren solos, así que **no haber
  corrido en N horas ES una falla**. Umbral = intervalo + margen (26 h para un cron diario).
- **Workflows con trigger por evento** (el reparto, que dispara cuando entra un mail): un hueco de
  24 h puede ser perfectamente normal — pasó el 27/07 sin nada roto. El silencio **no es
  concluyente**, y poner un umbral produciría falsos positivos.

Para el segundo caso no hay señal por la API: cuando la credencial de Gmail expiró, n8n **no dejó
ni una ejecución de error**, solo líneas en el log del servicio que la API REST no expone. De ahí
el **latido**: en vez de interpretar una ausencia, se exige una señal positiva.

## Criterios de aceptación (todos cumplidos)

- [x] Vista `/security/salud/` con semáforo por integración.
- [x] Por cada workflow vigilado: si está activo, cuándo fue su última ejecución, y si terminó en error.
- [x] **Regla de silencio** con umbral configurable **por workflow** (y sin umbral para los triggers).
- [x] **Estado real del backup en Drive**: se mide por la última ejecución del workflow, no por el
      registro local, porque Django marca el `Backup` antes de que n8n suba el archivo.
- [x] **Migraciones pendientes** listadas por app, detectadas sin aplicarlas.
- [x] Si n8n no responde o falta la API key: esa integración queda "sin datos" y **el resto del
      panel sigue funcionando**.
- [x] Acceso restringido a usuarios con acceso total.
- [x] **Endpoint JSON** con el mismo estado, para que un workflow lo consuma y avise.

## Arquitectura

```
/security/salud/          panel (renderiza los chequeos LOCALES, instantáneos)
      └── AJAX ─────────► /security/salud/api/        JSON con todo, incluido n8n
                          /security/salud/api/heartbeat/   ← n8n cada 15 min

n8n: "Salud - Latido de Gmail AkunCalcu" (iDrsq7vyGPHG7qAb)
     Cada 15 min → Probar lectura de Gmail (1 mail) → POST heartbeat
```

**El panel no consulta n8n en el render**: pinta lo local al instante y pide el bloque de n8n por
AJAX. Así un n8n lento nunca cuelga la página, y el endpoint JSON —que además es criterio de
aceptación— se ejercita desde el primer día en vez de quedar sin probar.

## Archivos

**Nuevos:**
- `security/health.py` — los chequeos, el cliente n8n (`urllib` + timeout 4 s) y el recolector.
  `WORKFLOWS_VIGILADOS` y `HEARTBEATS_VIGILADOS` con sus umbrales.
- `security/migrations/0004_heartbeatintegracion.py` — tabla nueva, no toca nada existente.
- `security/templates/security/salud.html` + `_salud_fila.html` — panel y parcial de fila.
- `security/test_salud.py` — 44 tests.
- `docs/n8n/n8n-salud-heartbeat.json` + `.md` — el workflow de latido y su puesta en marcha.

**Modificados:**
- `security/models.py` — `HeartbeatIntegracion` (`clave` única, `ultimo_ok`, `detalle`) con
  `minutos_desde_ultimo_ok`.
- `security/views.py` — `salud`, `api_salud`, `api_heartbeat`.
- `security/urls.py`, `security/middleware.py` (`/security/salud/api/` exento).
- `usuarios/access_control.py` — ítem `seguridad.salud` + las dos rutas API en `PUBLIC_ROUTE_KEYS`.
- `.env.example` — `HEALTH_BOT_SECRET`, y `N8N_BASE_URL` / `N8N_API_KEY` que ya existían en Railway
  sin estar documentadas ni usadas por el código.

## Decisiones técnicas

- **El latido es lo que hace útil al panel.** Sin él, la caída de Gmail solo se detectaría con un
  umbral de ~24 h, o sea igual de tarde que descubrirla a mano. Con él, en 45 minutos (tolera 3
  latidos perdidos). Efecto lateral valioso: **si n8n está caído, no late**, así que el latido
  terminó siendo el canario de cualquier caída del servicio, no solo de la credencial.
- **El nodo de Gmail del workflow no tiene `onError`, a propósito.** Si el OAuth caduca, ese nodo
  falla, el POST no se manda y el panel lo detecta. Ponerle `continueRegularOutput` mandaría el
  latido igual y reportaría salud falsa.
- **Umbrales en código, no en un modelo.** Son tres workflows y su umbral se deduce de su propio
  cron; un ABM para tres filas sería sobre-ingeniería. Si crecen, se promueve a modelo.
- **Sin librerías nuevas**: `urllib.request`, el mismo patrón de `backup_trigger_n8n`.
- **Doble autenticación en el endpoint JSON**: sesión con acceso total (para el AJAX del panel) o
  `X-Bot-Secret` con `HEALTH_BOT_SECRET` (para n8n). El payload nunca incluye la API key ni valores
  de entorno, solo estados y mensajes.
- **Cada chequeo corre aislado** (`_correr`): si uno explota, queda "sin datos" y los demás se
  siguen mostrando. Un panel de monitoreo que se cae por lo mismo que vigila no sirve de nada.

## Tests

`security/test_salud.py` — **44 tests**, suite de `security usuarios core solicitudes`: **118 OK**.

Varios reproducen incidentes reales: `test_latido_viejo_es_falla` (la caída de 25 h),
`test_ultima_ejecucion_con_error_es_falla` (los 9 días del backup),
`test_trigger_en_silencio_no_es_falla` (40 h sin mails **no** es falso positivo) y
`test_schedule_en_silencio_es_falla` (en un cron diario sí lo es). Además:
`test_panel_no_consulta_n8n`, `test_api_no_expone_secretos`, `test_no_aplica_migraciones` y los 4
del menú de Seguridad.

**Bug encontrado en la revisión**: `_horas_desde` usaba `django.utils.timezone.utc`, deprecado en
4.2 y **ya inexistente en Django 6**. Los 36 tests originales pasaban porque la rama solo corre con
fechas sin zona horaria y n8n siempre manda ISO con zona. Se cambió a `datetime.timezone.utc` y se
agregó `AntiguedadTest` para cubrirla. Nota: `requirements.txt` fija Django 4.2.7 (producción) pero
el venv local tiene 6.0.4 — conviene alinearlos en su propia entrega.

## Estado en producción (2026-08-01)

Deployado 14:41 (migración `security/0004` aplicada), variables `HEALTH_BOT_SECRET` en `web` y
`n8n`, workflow de latido creado y activo. Verificado por API: `400` con secret válido y clave
inválida, `401` con secret inválido, y el primer latido registrado ("última lectura hace 0 min").

**En su primer uso real el panel detectó una caída que no sabíamos**: n8n estuvo **11 horas** abajo
(01/08 02:16 → 13:25 UTC), y en esa ventana no corrió el backup de las 00:00 ni el recordatorio de
las 08:00 — los vendedores no recibieron su listado de pendientes ese día. También dejó a la vista
que la `N8N_API_KEY` que estaba en Railway era inválida (devolvía HTTP 401): el panel mostró los
tres workflows en "sin datos" hasta corregirla.

## Pendiente (fase 2)

El **aviso automático**: un workflow que consulte `/security/salud/api/` y mande WhatsApp cuando
`estado_general` sea `falla`. El endpoint ya está listo para eso. Sigue en pie el riesgo declarado
en el REQ: un panel hay que ir a mirarlo, y el backup a Drive falló 9 días con el registro visible
en n8n sin que nadie lo abriera.
