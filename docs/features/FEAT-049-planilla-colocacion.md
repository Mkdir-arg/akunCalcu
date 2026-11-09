# FEAT-049 — Planilla de Colocación (PDF) con envío por WhatsApp

- **Estado:** Implementado (en `development`)
- **Fecha:** 2026-11-09
- **Requerimiento:** [REQ-057](../requerimientos/REQ-057-pdf-colocacion.md) (RF-02) y la base común de PDF de [REQ-056](../requerimientos/REQ-056-pdf-medicion-y-base-pdf-comun.md)
- **Decisión:** [ADR-026](../team/decisions.md)
- **Apps:** `core` (base de PDF y cliente de WhatsApp), `presupuestos`, `usuarios` (permisos), `plantillas` y `comercial` (solo el refactor del logo)
- **Migración:** no

## Qué hace

En un presupuesto **confirmado con venta activa** aparece el botón **Colocación**. Abre una ventana con:

- **Colocador:** cuentas de tipo *colocadores* activas, o «A definir».
- **Fecha:** hoy por defecto.
- **Observaciones:** precargadas con las del presupuesto. Lo que se cambia acá no se guarda.

«Generar PDF» abre en una pestaña nueva la planilla A4 **COLOCACIÓN** con la identidad de la Orden de Fabricación:

- logo, número de presupuesto y fecha en el encabezado;
- colocador con su teléfono;
- datos del cliente: nombre con ID `C-00123`, domicilio, localidad, provincia y teléfono;
- tabla de aberturas con cantidad, tipología, medidas y color, que repite el encabezado si pasa de hoja;
- importes: valor total, seña / a cuenta, saldo pendiente y forma de pago. En PVC, además, la cotización y los montos en US$;
- observaciones, firmas del colocador y del cliente, y el pie con los datos de la empresa.

Después de abrir el PDF aparece **«¿Lo enviás por WhatsApp?»** con los **números autorizados** activos. Los elegidos reciben el
PDF con un mensaje (plantilla de Meta `planilla_colocacion`) desde el WhatsApp de Akun. Al final se muestra, número por número,
qué salió y qué falló con el motivo.

Sin venta (o con la venta dada de baja) el botón no aparece y la URL redirige al detalle con un mensaje.

## Criterios de aceptación

- [x] Botón «Colocación» solo en presupuestos confirmados con venta activa
- [x] Ventana con colocador (colocadores activos o «A definir»), fecha (hoy) y observaciones (las del presupuesto)
- [x] PDF A4 «COLOCACIÓN» con identidad Akun, en pestaña nueva
- [x] Colocador, fecha, cliente con ID, domicilio, localidad, provincia, teléfono y nº de presupuesto
- [x] Tabla de aberturas en varias hojas con encabezado repetido
- [x] Importes con forma de pago; en PVC cotización y US$
- [x] Observaciones y firmas
- [x] Sin venta → sin botón; la URL redirige con mensaje
- [x] Un colocador que no es de tipo colocadores (POST manipulado) sale en blanco
- [x] Pregunta de WhatsApp con números autorizados activos; sin números, no aparece
- [x] Envío a uno o varios números con resultado por número; número inactivo rechazado
- [x] Sin `META_WA_TOKEN` / `META_PHONE_NUMBER_ID` avisa que el envío no está configurado y el PDF sale igual

Cambio respecto del REQ: el botón usa `btn btn-secondary`, como el resto de la botonera desde el rediseño «Taller», en lugar del azul que pedía el REQ (anterior al rediseño).

## Archivos

| Archivo | Cambio |
|---|---|
| `core/pdf.py` (nuevo) | `build_logo_data_url`, `contexto_base_pdf`, `filas_cliente`, `render_pdf_bytes`, `pdf_response` |
| `core/templates/core/pdf/base_a4.html` (nuevo) | Base A4 de los PDF internos (estilo de la Orden de Fabricación) |
| `core/templates/core/pdf/_datos_cliente.html` (nuevo) | Barra «DATOS DEL CLIENTE», una tabla por renglón |
| `core/whatsapp.py` (nuevo) | Cliente de la Cloud API de Meta: `subir_pdf` y `enviar_plantilla_documento` |
| `presupuestos/documentos_pdf.py` (nuevo) | `venta_activa` y `build_colocacion_context` |
| `presupuestos/pdf_descriptions.py` | `build_ficha_item` (cantidad, tipología, medidas, color; contempla estructuras) |
| `presupuestos/forms.py` | `ColocacionPdfForm` y `ColocacionWhatsAppForm` |
| `presupuestos/views.py` | Vistas `colocacion` y `colocacion_whatsapp`; formulario y números en el detalle; usa `core.pdf` para el logo |
| `presupuestos/urls.py` | `presupuestos-colocacion` y `presupuestos-colocacion-whatsapp` |
| `presupuestos/templates/presupuestos/colocacion_pdf.html` (nuevo) | La planilla |
| `presupuestos/templates/presupuestos/detalle.html` | Botón, ventana y pregunta de WhatsApp (SweetAlert2) |
| `usuarios/access_control.py` | Las dos rutas con `presupuestos.view` |
| `plantillas/views.py`, `comercial/models.py` | El logo pasa a `core.pdf` (la función estaba copiada tres veces) |
| `presupuestos/tests.py`, `core/tests.py` | 33 tests nuevos |

## Decisiones técnicas

- **Nada se guarda:** colocador, fecha y observaciones solo salen en el PDF. Sin migración y sin evento de Agenda (dispararía recordatorios).
- **Los importes salen de la venta**, no del presupuesto: total = seña + pagos + saldo cierra aunque la venta se haya editado.
- **Envío directo a Meta desde Django** (no por n8n), con una plantilla con documento. Ver ADR-026.
- La planilla `Planilla Colocaciones.dotx` que cita el RF no llegó: se usó la identidad de la Orden de Fabricación.

## Puesta en marcha

1. Plantilla `planilla_colocacion` (cuenta *akun*, id `2904528229919976`) creada el 2026-11-09 y **en revisión de Meta**.
2. Variables en el servicio `web` de Railway: `META_WA_TOKEN` y `META_PHONE_NUMBER_ID`, cargadas como referencia a las del servicio de n8n (2026-11-09).
3. Medio de pago de la cuenta de WhatsApp: confirmado por el usuario.
4. Pendiente: prueba real a un número propio cuando Meta apruebe la plantilla.
