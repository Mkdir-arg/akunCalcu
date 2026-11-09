# REQ-057 — Planilla de Colocación (PDF) desde el presupuesto confirmado

- **Estado:** Implementado
- **Derivó en:** [FEAT-049](../features/FEAT-049-planilla-colocacion.md)
- **Fecha:** 2026-10-20
- **Complejidad:** Mediano
- **Origen:** RF-02 (prioridad Alta)
- **Depende de:** [REQ-054](./REQ-054-id-cliente-y-provincia.md) (provincia, `datos_documento()`) y [REQ-056](./REQ-056-pdf-medicion-y-base-pdf-comun.md) (base común de PDF)
- **Plan:** [Plan RF Akun — octubre 2026](../team/plan-rf-akun-2026-10.md) · Sprint 2
- **Apps afectadas:** `presupuestos`, `usuarios`

## User Story

Como **responsable de coordinar colocaciones** quiero **generar desde el presupuesto aprobado la
planilla de Colocación en PDF**, con cliente, aberturas, importes y colocador, para **entregársela
al colocador sin cargar datos a mano**.

## Decisiones tomadas

| Pregunta | Decisión | Motivo |
|---|---|---|
| ¿Desde qué estado? | **Solo presupuesto confirmado con venta activa** | "Presupuesto aprobado". Seña, saldo y forma de pago viven en la Venta |
| ¿Se guarda colocador/fecha/observaciones? | **No.** Se eligen en un modal y salen en el PDF | No se pidió persistencia; sin migración |
| ¿Crear un evento de Agenda? | **No** | Dispararía recordatorios por WhatsApp y una segunda fuente de verdad. Solo se reutiliza el filtro de colocadores |
| Formato de referencia (`Planilla Colocaciones.dotx`) | **No vino adjunto**: se usa la identidad de la Orden de Fabricación | Misma base que Medición. Si el cliente manda el .dotx, se ajusta la distribución |
| Forma de pago | **Medios de pago usados** (efectivo, transferencia…) **+ modalidad de seña** (50/50, 70/30) | El pedido es ambiguo; mostrar las dos no cuesta y el colocador cobra con eso |
| Localidad | **Se incluye** además de provincia | El domicilio sin localidad no sirve para llegar |
| PVC | Cotización del dólar + total y saldo **también en US$** (derivados de pesos ÷ cotización, ADR-010) | El presupuesto PVC se piensa en dólares |
| Datos de la venta para quien solo tiene Presupuestos | **Se aceptan** | El detalle del presupuesto ya enlaza a la venta; el colocador necesita saber cuánto cobrar |

## Criterios de Aceptación

- [x] En un presupuesto confirmado con venta, el detalle muestra el botón "Colocación" (azul, ícono herramientas)
- [x] El botón abre un modal con: colocador (desplegable de cuentas de tipo colocadores activas, opción "A definir"), fecha (por defecto hoy) y observaciones (precargadas con el comentario del presupuesto)
- [x] "Generar" abre en una pestaña nueva un PDF A4 titulado **COLOCACIÓN** con la identidad Akun
- [x] El PDF contiene colocador, fecha, cliente con ID, domicilio, localidad, provincia, teléfono, nº de presupuesto
- [x] Tabla de aberturas con cantidad, tipología, medidas y color por ítem (puede ocupar varias hojas y repite el encabezado)
- [x] Importes: valor total, seña / a cuenta, saldo pendiente, forma de pago; en PVC además cotización y montos en US$
- [x] Recuadro de observaciones y firmas (colocador / cliente)
- [x] En un presupuesto sin venta (o con la venta dada de baja) el botón no aparece y la URL redirige al detalle con un mensaje
- [x] Un colocador que no sea de tipo colocadores (POST manipulado) sale en blanco

## Diseño técnico

- `presupuestos/urls.py`: `<int:pk>/colocacion/`, name `presupuestos-colocacion`, GET y POST. El PDF sale `inline` `colocacion_<numero>.pdf`. **POST** desde el modal (con `target="_blank"` y csrf) para no chocar con el límite de largo de URL con observaciones largas; GET devuelve la planilla con colocador vacío, para completar a mano
- `presupuestos/forms.py`: `ColocacionPdfForm(forms.Form)`: colocador `ModelChoiceField` con `Cuenta.objects.filter(tipo_cuenta__tipo='colocadores', activo=True, deleted_at__isnull=True)` (mismo filtro que `agenda/forms.py` ~l.49-51, copiado sin tocar agenda), fecha y observaciones (`max_length=1000`). Un campo inválido sale en blanco
- `presupuestos/views.py`: vista `colocacion` (condición: `estado == 'confirmado'`, `presupuesto.venta` y `venta.deleted_at is None`; se usa la venta y no solo el estado porque `cambiar_estado` permite des-confirmar y la venta queda). En `detalle` (~l.244-249) agregar el form al contexto solo si hay venta
- `presupuestos/pdf_descriptions.py`
  - Extraer la primera mitad de `build_pdf_item_context` (~l.597-618) a `_resolver_snapshot(item)` (refactor sin cambio de salida)
  - `build_ficha_item(item)` → cantidad (`item.cantidad`), tipología (mismo criterio que la OF: `snapshot.producto.descripcion` o `item.descripcion`), medidas (`ancho x alto` solo si ambos > 0; en PVC y terciarizados se guardan en 0 → vacío), color (`snapshot.tratamiento.descripcion` con el respaldo legacy de `_build_legacy_snapshot`)
- `presupuestos/documentos_pdf.py`: `build_colocacion_context(presupuesto, colocador, fecha, observaciones)`
- `presupuestos/templates/presupuestos/colocacion_pdf.html`: extiende la base; tabla de ítems con `repeat="1"`; importes y firmas en `pie_derecha`
- `presupuestos/templates/presupuestos/detalle.html`: botón dentro de `{% if presupuesto.estado == 'confirmado' and presupuesto.venta %}` después de Medición, ícono `fa-screwdriver-wrench`; modal (patrón `#modal-orden`, ~l.706-761) con **`data-select2-dropdown-parent`** (Select2 global de base.html); JS en `extra_js`
- `usuarios/access_control.py` (~l.226): registrar `presupuestos:presupuestos-colocacion` con `presupuestos.view`

| Campo | Fuente |
|---|---|
| Colocador | `Cuenta.nombre` y `telefono` |
| Cliente, ID, domicilio, localidad, provincia, teléfono | `Cliente.datos_documento()` |
| Nº presupuesto | `presupuesto.numero` |
| Valor total | `venta.get_total_con_percepciones()` (PVC: + `venta.valor_total_usd`) |
| Seña / a cuenta | `venta.sena + Σ pagos.monto` (misma fórmula que `venta_detail`, `comercial/views.py` ~l.473) |
| Saldo | `venta.saldo` |
| Forma de pago | medios distintos de `venta.pagos` (`get_forma_pago_display`) + `venta.forma_pago` si hay seña + `get_modalidad_sena_display` |
| Cotización dólar | solo si `presupuesto.es_pvc()`: `presupuesto.cotizacion_usd` |
| Observaciones | las del modal |

El total sale de la **venta** a propósito: así total = seña + saldo cierra aunque la venta se haya editado después de confirmar.

## Impacto

FK nuevas: ninguna. Datos existentes: solo lectura. URL name nuevo. Form nuevo sin modelo.

**Nota (2026-10-22):** si [REQ-062](./REQ-062-estructuras.md) (estructuras) se implementa antes, `build_ficha_item` tiene que contemplar `resultado_json['tipo'] == 'estructura'`. Ese ítem no tiene `producto` en el snapshot: la tipología sale del título de la estructura, las medidas son las del conjunto y el color sale de `snapshot.tratamiento`.

## Ampliación 2026-11-09 — Envío por WhatsApp

Pedido del usuario: al generar la planilla, preguntar si se envía por WhatsApp, mostrar la lista de
números habilitados y mandarla.

| Pregunta | Decisión |
|---|---|
| ¿Qué lista? | **Números autorizados** (`gastos_diarios.NumeroAutorizado`, activos): la misma del bot y la agenda |
| ¿Qué se manda? | El **PDF + un texto**, como plantilla de Meta `planilla_colocacion` (Utility, `es_AR`, encabezado DOCUMENT). Fuera de la ventana de 24 h Meta solo entrega plantillas aprobadas |
| ¿Por dónde? | **Django → Meta Graph API directo** (no n8n): el resultado vuelve en el momento y no depende de que n8n esté vivo |
| ¿Se guarda algo? | No. Sin migración |

Texto de la plantilla: «Hola, te enviamos la planilla de colocación del presupuesto {{1}} del cliente
{{2}}. Fecha prevista de colocación: {{3}}. Ante cualquier duda, respondé este mensaje.» Pie: «Akun
Aberturas». Creada en la cuenta *akun* (empresa MKDIR) el 2026-11-09, id `2904528229919976`, en revisión.

### Criterios de aceptación (ampliación)

- [x] Al tocar «Generar PDF» se abre el PDF y aparece «¿Lo enviás por WhatsApp?» con los números autorizados activos (casillas)
- [x] Sin números autorizados activos la pregunta no aparece
- [x] «Enviar» exige al menos un número; manda el mismo PDF a cada uno y muestra cuáles salieron y cuáles fallaron con el motivo de Meta
- [x] Si faltan `META_WA_TOKEN` / `META_PHONE_NUMBER_ID` en el entorno, avisa que el envío no está configurado (el PDF sale igual)
- [x] Un número inactivo o inexistente posteado no se acepta

### Diseño técnico (ampliación)

- `core/whatsapp.py`: `subir_pdf()` (POST `/{phone_id}/media`, multipart con `urllib`, sin dependencias nuevas) y `enviar_plantilla_documento()` (POST `/{phone_id}/messages`). Los errores de Meta se traducen a `EnvioWhatsAppError` con código y mensaje
- `presupuestos/forms.py`: `ColocacionWhatsAppForm` = `ColocacionPdfForm` + `numeros`
- `presupuestos/views.py`: `colocacion_whatsapp` (POST, JSON), ruta `presupuestos-colocacion-whatsapp`, registrada con `presupuestos.view`
- `detalle.html`: SweetAlert después del submit del modal; `fetch` con el mismo `FormData` + `numeros`
- **Variables de entorno nuevas en el servicio web de Railway:** `META_WA_TOKEN`, `META_PHONE_NUMBER_ID` (`1119452454594540`), opcional `META_WA_API_VERSION` (default `v21.0`)

### Pendientes externos

- Aprobación de la plantilla por Meta
- Confirmar en Billing Hub que la cuenta *akun* tiene medio de pago (si no, Meta acepta y no entrega: error 131042)
- Cargar las variables de entorno en Railway

## Tests

- Sin venta → redirige con mensaje; con venta → 200 y PDF por GET y por POST
- Contexto: seña = sena + pagos; saldo; forma de pago combinada; cotización solo en PVC; ítem PVC con medidas y color vacíos; ítem de aluminio con color del snapshot
- Colocador de tipo proveedores posteado → sale en blanco
- El botón solo aparece si está confirmado con venta; la ruta está registrada
- `build_ficha_item` con `SimpleTestCase`; la salida de `build_pdf_item_context` no cambia tras el refactor
- Verificación visual con el script de PNG (varias hojas, corte de tabla)

**Migración:** No.
