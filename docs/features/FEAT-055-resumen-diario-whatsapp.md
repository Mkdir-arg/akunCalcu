# FEAT-055 — Resumen diario y semanal por WhatsApp para la dirección

**Estado:** Implementado en Django (en `development`, sin commitear). n8n creado e inactivo; falta la puesta en marcha.
**Fecha:** 2026-11-10
**Requerimiento:** [REQ-071](../requerimientos/REQ-071-resumen-diario-whatsapp.md)
**ADR:** ADR-031
**Workflow n8n:** [n8n-resumen-direccion-workflow.md](../n8n/n8n-resumen-direccion-workflow.md)

## Qué hace

Dos personas de la dirección reciben por WhatsApp:
- **De lunes a viernes a las 19:00**: el resumen del día.
- **Los sábados a las 13:00**: el resumen de la semana, con un ranking por vendedor.

El mensaje que llega es la plantilla «Tu resumen está listo», con el botón **Ver resumen**. Al tocarlo
llega el resumen completo, con secciones en negrita: ventas, presupuestos, para seguir (sin respuesta
hace 7 días o más y pedidos atrasados), fábrica, agenda, solicitudes y equipo.

Django calcula todos los números. GPT-4o-mini, desde n8n, solo los redacta. Cada resumen queda
guardado en el admin (**Resúmenes de la dirección**), con los datos, el texto y quién lo abrió.

## Criterios de aceptación

| Criterio | Estado |
|---|---|
| La API con `X-Bot-Secret` devuelve los números del día o de la semana; sin la clave, 403 | ✅ Testeado |
| Presupuestos creados (cantidad y monto por vendedor), confirmados y sin respuesta 7+ días | ✅ Testeado |
| Ventas del período comparadas con el período anterior (excluye las borradas) | ✅ Testeado |
| Fábrica (cambios de estado, atrasados) y agenda programada por colocador o técnico | ✅ Agenda testeada · fábrica sin test propio |
| Solicitudes por vendedor y actividad por usuario | ✅ Actividad testeada · solicitudes sin test propio |
| n8n arma el texto con GPT y Django lo guarda, lun-vie 19:00 y sáb 13:00 | ✅ Workflow creado y validado · ⏳ inactivo |
| Las 2 personas reciben la plantilla con el botón «Ver resumen» | ⏳ Falta crear y aprobar la plantilla en Meta |
| Al tocar el botón llega el resumen completo, y el bot de gastos no lo procesa | ⏳ Falta la rama en el workflow de gastos |
| Otro número no recibe nada | ✅ Django responde 404 (testeado) · ⏳ rama n8n pendiente |

## Archivos

| Archivo | Cambio |
|---|---|
| `gastos_diarios/models.py`, `forms.py`, `numero_form.html`, `numero_list.html`, migración `0004` | Campo `recibe_resumen`: casilla en el formulario y etiqueta «Recibe resumen» en el listado |
| `resumenes/models.py` | Modelo `Resumen` (período, desde, hasta, datos, texto, abierto_por); único por período y fecha |
| `resumenes/migrations/0001_initial.py` | Tabla nueva; no depende de otras apps |
| `resumenes/services.py` | `calcular_datos(periodo, fecha)`: un bloque por sección, `destinatarios()`, `rango()` |
| `resumenes/forms.py` | `GuardarResumenForm`: valida y recorta el texto a 4000 caracteres |
| `resumenes/views.py` | `api_datos` (GET), `api_guardar` (POST), `api_ultimo` (GET) |
| `resumenes/urls.py`, `admin.py`, `apps.py`, `tests.py` | Namespace `resumenes`, admin de solo lectura, 19 tests |
| `akuna_calc/settings.py`, `akuna_calc/urls.py` | Registro de la app y de la ruta `resumenes/` |
| `security/middleware.py` | `/resumenes/api/` en `SECURITY_EXEMPT_PREFIXES` y `AuditMiddleware.EXCLUDED_PATHS` |
| `usuarios/access_control.py` | Las 3 APIs en `PUBLIC_ROUTE_KEYS`; si no, `RouteAccessMiddleware` las manda al login |
| n8n `iEON0QIYoc8O9Bbk` | Workflow nuevo, inactivo |

## Decisiones técnicas

- **GPT no calcula** (ADR-031): recibe solo el JSON de Django, con la regla de no inventar cifras.
- **Ranking por vendedor**: `Venta` no tiene vendedor; el ranking sale de `Presupuesto.created_by`
  de los presupuestos cuya venta se creó en el período.
- **Confirmados**: se cuentan por la fecha de creación de la venta asociada. El presupuesto no guarda
  la fecha en que se confirmó.
- **Sin respuesta**: `estado='enviado'` y creado hace 7 días o más. No hay fecha de envío.
- **Agenda**: solo lo programado, porque `EventoAgenda` no tiene un estado «realizado». Se excluyen los cancelados.
- **Comparación de ventas**: el mismo período de la semana anterior (día contra día, semana contra semana).
- **Botón en lugar de pedir «OK» por escrito**: el webhook de Meta es único y lo comparte con el bot de
  gastos. El botón llega con `type: button` y se filtra antes del parseo de gastos.
- **Destinatarios desde la web**: casilla «Recibe el resumen» en *Números autorizados* (`gastos_diarios.NumeroAutorizado.recibe_resumen`, migración `gastos_diarios/0004`), la misma lista que usan la agenda y el bot de gastos. Una sola fuente. n8n los recibe en
  `api_datos`, y `api_ultimo` valida el teléfono contra esa misma lista.

## Pendientes para ponerlo en marcha

1. Variable `RESUMEN_BOT_SECRET` en Railway (`web` y n8n) y marcar «Recibe el resumen» en los 2 números autorizados.
2. Plantilla `resumen_listo` en Meta (Utility, `es_AR`, con botón de respuesta rápida).
3. Webhook de Meta apuntado a n8n (FIX-026) y rama «Ver resumen» en `VfdJhVTZmKj7HoES`. El borrador
   de ese workflow tiene cambios sin publicar: resolverlo antes.
4. Prueba manual y activación del workflow nuevo.

## Riesgo conocido

El JSON que va a OpenAI incluye nombres de clientes y montos, como ya pasa con el bot de gastos.
