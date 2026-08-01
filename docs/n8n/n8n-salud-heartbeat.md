# Workflow n8n — Latido de Gmail (panel de salud, REQ-045)

Workflow de 3 nodos que corre **cada 15 minutos** y confirma a Django que n8n todavía puede
leer la casilla del reparto.

```
Cada 15 min  →  Probar lectura de Gmail (1 mail)  →  POST /security/salud/api/heartbeat/
```

## Por qué existe

El trigger del reparto (`PlXLIyyN2wyFYICD`) **solo genera ejecución cuando entra un mail**, así
que "sin ejecuciones" puede significar dos cosas muy distintas: que no llegaron mails, o que no
se puede leer la casilla. Cuando la credencial OAuth de Gmail expiró el 30/07, n8n **no dejó ni
una ejecución de error** — solo líneas en el log del servicio, que la API REST no expone. El
reparto estuvo **25 horas** caído y nadie se enteró; en ese lapso entraron 7 formularios web,
uno de ellos un pedido real que quedó sin atender.

Este workflow convierte esa ausencia de señal en una señal positiva: si el latido deja de llegar,
algo se rompió.

## Detalles que importan

- **El nodo de Gmail no tiene `onError`, a propósito.** Si el OAuth caduca, ese nodo falla, el
  POST nunca se ejecuta y el panel lo detecta. Ponerle `continueRegularOutput` rompería todo el
  propósito del workflow: mandaría el latido igual y diría que está sano.
- **`alwaysOutputData: true`** en el nodo de Gmail: si la casilla estuviera vacía, sin esto el
  flujo se cortaría sin error y daría un falso positivo.
- El panel marca **Falla a los 45 minutos** (`HEARTBEATS_VIGILADOS` en `security/health.py`), o
  sea que tolera 3 latidos perdidos antes de alarmar.

## Variables de entorno que necesita

| Variable | Dónde | Para qué |
|---|---|---|
| `AKUNACALCU_WEB_URL` | servicio `n8n` | ya existe |
| `HEALTH_BOT_SECRET` | servicios `n8n` **y** `web` | debe tener **el mismo valor en los dos** |

## Puesta en marcha (en este orden)

1. Deployar Django con la migración `security/0004_heartbeatintegracion`.
2. Setear `HEALTH_BOT_SECRET` con el mismo valor en el servicio `web` y en el servicio `n8n`.
3. Importar este JSON en n8n y **activarlo**.
4. Verificar en `/security/salud/` que "Lectura de Gmail (reparto)" pase de *sin datos* a **OK**
   dentro de los primeros 15 minutos.

Si se activa antes del paso 2, el POST devuelve 401 y el latido no se registra: el panel lo va a
mostrar como falla, que técnicamente es correcto pero por el motivo equivocado.

## Cómo probarlo a mano

```bash
curl -X POST "$AKUNACALCU_WEB_URL/security/salud/api/heartbeat/" \
  -H "Content-Type: application/json" \
  -H "X-Bot-Secret: $HEALTH_BOT_SECRET" \
  -d '{"clave":"gmail_reparto","detalle":"prueba manual"}'
```

Respuesta esperada: `{"ok": true, "clave": "gmail_reparto"}`.
