# REQ-056 — Planilla de Medición (PDF) + base común de PDFs internos A4

- **Estado:** Aprobado
- **Fecha:** 2026-10-20
- **Complejidad:** Mediano (incluye la base común que reutilizan REQ-057 y REQ-058)
- **Origen:** RF-03 (prioridad Alta)
- **Depende de:** [REQ-054](./REQ-054-id-cliente-y-provincia.md) (`Cliente.datos_documento()`)
- **Plan:** [Plan RF Akun — octubre 2026](../team/plan-rf-akun-2026-10.md) · Sprint 2
- **Apps afectadas:** `core`, `presupuestos`, `plantillas`, `comercial`, `usuarios`

## User Story

Como **vendedor** quiero **generar desde el presupuesto la planilla de Medición en PDF**, con los
datos del cliente ya cargados, para **coordinar la visita del medidor sin copiar datos a mano**.

## Decisiones tomadas

- **Usuario responsable = quien genera el PDF** ("usuario responsable que generó la orden de medición")
- **Se puede generar en cualquier estado** del presupuesto: la medición es previa a confirmar
- **No se guarda nada**: es un documento que se arma con los datos del momento
- **Identidad visual = la de la Orden de Fabricación** (azul #145ea7, negro #1d1d1b, logo arriba a la izquierda, barras de título azules, pie con datos de empresa desde la configuración). Se extrae a una **base común** que usan Medición, Colocación y, para el logo, el Recibo
- Debajo de los datos, un recuadro de **observaciones con renglones** para completar a mano en la visita (solo presentación)

## Criterios de Aceptación

- [ ] El detalle del presupuesto tiene un botón "Medición" (azul, ícono regla) junto a "Recibo"
- [ ] Abre en una pestaña nueva un PDF A4 vertical titulado **MEDICIÓN**, con logo Akun y el estilo de la Orden de Fabricación
- [ ] Contiene: fecha de emisión, nº de presupuesto, cliente (con ID `C-00123`), domicilio, localidad, teléfono y usuario responsable
- [ ] Recuadro de observaciones con renglones para completar a mano
- [ ] El pie muestra los datos de la empresa desde la configuración general (no hardcodeados)
- [ ] Solo accede quien tiene acceso a Presupuestos; presupuesto dado de baja → 404
- [ ] La Orden de Fabricación sigue saliendo exactamente igual que antes

## Diseño técnico

### Base común de PDF (archivos nuevos)

- `core/pdf.py`
  - `build_logo_data_url()`: hoy está **copiada tres veces** idéntica (`plantillas/views.py` ~l.20-31, `presupuestos/views.py` ~l.47-59, dentro de `Recibo.construir_pdf_bytes` en `comercial/models.py` ~l.519-558)
  - `contexto_base_pdf()` → `{'logo_url', 'empresa'}` (empresa desde `ConfiguracionGeneral.get_datos_empresa()`)
  - `render_pdf_bytes(html)`: lanza excepción si pisa devuelve `err`
  - `pdf_response(template, context, filename, inline=True, error_message=...)`: headers no-cache y 500 text/plain si falla, como hoy
- `core/templates/core/pdf/base_a4.html`: CSS tomado de `orden_pdf.html` (`@page` A4 margen 7mm, `.bar`, `.head`, `.logo`, `.title`, `.meta`, `.fields/.lbl/.val`, `.pie`, `.firmas`). Bloques `extra_css`, `titulo`, `meta`, `contenido`, `pie_derecha`. `meta` recorre `meta_filas` armada en Python
- `core/templates/core/pdf/_datos_cliente.html`: barra "DATOS DEL CLIENTE" + `filas_cliente` (pares etiqueta/valor desde `Cliente.datos_documento()`), **una tabla por fila, sin colspan**

**Reglas de xhtml2pdf para todas las plantillas nuevas** (se registran en un ADR nuevo): solo tablas con anchos en % por celda; altos en px/mm, nunca en %; nada de flex, grid ni colspan; las etiquetas deben entrar en su ancho (pisa ignora `nowrap`); `repeat="1"` en tablas largas.

**Refactor sin cambio de comportamiento**: `plantillas/views.py`, `presupuestos/views.py` y `comercial/models.py` pasan a usar `core.pdf`. La plantilla `orden_pdf.html` **no se toca**; migrarla a la base es opcional y solo si el render antes/después sale idéntico.

### Medición

- `presupuestos/urls.py`: `<int:pk>/medicion/`, name `presupuestos-medicion` (GET, `@login_required`), PDF `inline` `medicion_<numero>.pdf`
- `presupuestos/documentos_pdf.py` (nuevo, para no seguir engordando `views.py`): `build_medicion_context(presupuesto, user)`
- `presupuestos/views.py`: vista `medicion` (`get_object_or_404` con `deleted_at__isnull=True`)
- `presupuestos/templates/presupuestos/medicion_pdf.html`: extiende la base
- `presupuestos/templates/presupuestos/detalle.html` (~l.112-115): botón `bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-xl font-semibold text-sm inline-flex items-center`, ícono `fa-ruler-combined`, `target="_blank"`
- `usuarios/access_control.py` (~l.226): registrar `presupuestos:presupuestos-medicion` con `presupuestos.view`. **Ojo:** una ruta sin registrar no da 403, deja entrar a cualquier usuario logueado; registrarla es lo que la restringe

| Campo | Fuente |
|---|---|
| Fecha | Hoy (emisión) |
| Nº presupuesto | `presupuesto.numero` |
| Cliente / ID | `datos_documento()` |
| Domicilio, localidad, teléfono | `datos_documento()` |
| Responsable | `request.user.get_full_name()` o `username` |

## Verificación visual

`render_orden.py` (citado en la memoria del proyecto) **no existe**. Antes de tocar nada se crea un script en el scratchpad (fuera del repo) que renderiza con `render_to_string` + `pisa.CreatePDF` y pasa el PDF a PNG con pypdfium2 (ya está en el venv local). Se sacan PNG de referencia de la OF y del recibo de Ventas, y se comparan después del refactor.

## Tests

- `core/tests.py`: `pdf_response` devuelve `application/pdf` y empieza con `%PDF`; con `pisa.CreatePDF` parcheado para devolver `err` → 500
- Medición: 200 + PDF + nombre de archivo; sin login → 302; presupuesto borrado → 404; el HTML incluye cliente, número y usuario; la ruta está registrada con `presupuestos.view`; el detalle muestra el botón
- Los tests de la OF (`plantillas/tests.py` ~l.390-411) deben seguir pasando

**Migración:** No.
