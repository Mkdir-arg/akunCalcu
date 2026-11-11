# Workflow n8n — Resumen de la dirección por WhatsApp (REQ-071)

Dos piezas:

1. **«Resumen Direccion AkunCalcu (WhatsApp)»** (`iEON0QIYoc8O9Bbk`): workflow nuevo que arma y avisa.
2. **Rama «Ver resumen»** dentro de «WhatsApp Gastos Diarios AkunCalcu v2» (`VfdJhVTZmKj7HoES`).
   Meta permite un solo webhook por app, así que el botón del aviso llega a ese workflow.

## 1. Workflow nuevo

```
Horario (lun-vie 19:00 · sáb 13:00, America/Argentina/Buenos_Aires)
  → Elegir Periodo        sábado = 'semana', resto = 'dia'
  → Pedir Datos Django    GET  /resumenes/api/datos/?periodo=…    (X-Bot-Secret, 3 intentos)
  → Redactar con GPT      gpt-4o-mini: solo redacta el JSON, no calcula (ADR-031)
  → Guardar Resumen       POST /resumenes/api/guardar/            (Django recorta a 4000 caracteres)
  → Un Item por Destinatario   números autorizados con «Recibe el resumen» (Django)
  → WhatsApp Aviso Resumen     plantilla resumen_listo + botón quick reply payload VER_RESUMEN
```

Si Django o GPT fallan después de 3 intentos, la ejecución se corta y **no se manda nada**.
El envío tiene `onError: continueRegularOutput` para que un número con problemas no bloquee al otro.
Meta responde `accepted`, que no quiere decir «entregado»: los rechazos (`failed`) llegan al nodo
«Fallo de Envio» del workflow de gastos.

## 2. Rama «Ver resumen» en el workflow de gastos

Va **entre «Normalizar Evento» y «Es Mensaje»**, para que el botón no llegue al bot de gastos:

```
Normalizar Evento → IF Es Ver Resumen
                      ├─ sí → Pedir Ultimo Resumen   GET /resumenes/api/ultimo/?telefono={{numero_origen}}
                      │         → WhatsApp Resumen Completo (texto libre; la ventana de 24 h está abierta)
                      └─ no → Es Mensaje (todo sigue igual que hoy)
```

- Condición: `tipo_evento === 'mensaje' && tipo_mensaje === 'button' && texto === 'Ver resumen'`.
  «Normalizar Evento» ya carga `texto = m.button.text` para los mensajes de tipo `button`.
- «Pedir Ultimo Resumen» va **sin `onError`**: un número sin «Recibe el resumen» marcado recibe
  404 de Django, la ejecución se corta y a esa persona no se le contesta nada.

⚠️ **Antes de aplicarla:** el borrador de ese workflow es distinto de la versión publicada (hay
cambios sin publicar, por ejemplo el nodo «Unificar Texto»). Hay que publicar o descartar ese
borrador primero; si no, al guardar se pisa uno de los dos.

## Plantilla de Meta `resumen_listo`

- Categoría **Utility**, idioma `es_AR`.
- Cuerpo: `Tu resumen {{1}} de Akun está listo. Tocá «Ver resumen» para leerlo.`
  `{{1}}` = «del día» o «de la semana».
- Botón de respuesta rápida: `Ver resumen`.

## Variables de entorno

| Variable | Dónde | Para qué |
|---|---|---|
| `RESUMEN_BOT_SECRET` | Railway: `web` **y** n8n | Clave del header `X-Bot-Secret` |
| `META_WA_TOKEN`, `META_PHONE_NUMBER_ID` | n8n (ya existen) | Envío por la Graph API |
| `AKUNACALCU_WEB_URL` | n8n (ya existe) | Dirección base de Django |

## Puesta en marcha

1. Marcar «Recibe el resumen» en los números autorizados (Gastos diarios → Números autorizados), cargar las variables y hacer el deploy de `web` (la migración `resumenes/0001` corre sola).
2. Crear la plantilla `resumen_listo` y esperar a que Meta la apruebe.
3. Apuntar el webhook de Meta a n8n (paso pendiente de FIX-026) y agregar la rama «Ver resumen».
4. Probar a mano el workflow nuevo con «Execute workflow» y tocar el botón desde uno de los 2 números.
5. Activar el workflow nuevo.
