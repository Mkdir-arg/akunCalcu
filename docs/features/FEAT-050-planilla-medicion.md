# FEAT-050 — Planilla de Medición (PDF)

- **Estado:** Implementado (en `development`)
- **Fecha:** 2026-11-10
- **Requerimiento:** [REQ-056](../requerimientos/REQ-056-pdf-medicion-y-base-pdf-comun.md) (RF-03)
- **Base:** la base común de PDF que nació con [FEAT-049](./FEAT-049-planilla-colocacion.md) (`core/pdf.py`, ADR-026)
- **Apps:** `presupuestos`, `usuarios` (permiso de la ruta)
- **Migración:** no

## Qué hace

En el detalle de cualquier presupuesto, sin importar su estado, aparece el botón **Medición**, con ícono de regla, al lado de
«Presupuesto». Abre en una pestaña nueva la planilla A4 **MEDICIÓN** con la identidad de la Orden de Fabricación:

- logo de Akun, título MEDICIÓN y, en el encabezado, el número de presupuesto y la fecha de emisión (hoy);
- **usuario responsable**: quien genera el PDF (su nombre completo o, si no lo tiene, el usuario);
- datos del cliente: nombre con ID `C-00123`, domicilio, localidad y teléfono;
- 10 renglones de observaciones para completar a mano en la visita;
- firmas del medidor y del cliente, y el pie con los datos de la empresa sacados de la configuración general.

No se guarda nada: el documento se arma con los datos del momento. Se puede imprimir o descargar desde el visor del navegador.

## Criterios de aceptación

- [x] Botón «Medición» en el detalle del presupuesto
- [x] PDF A4 vertical titulado MEDICIÓN, con logo y estilo de la Orden de Fabricación, en pestaña nueva
- [x] Fecha, nº de presupuesto, cliente con ID, domicilio, localidad, teléfono y usuario responsable
- [x] Recuadro de observaciones con renglones
- [x] Pie con los datos de la empresa desde la configuración
- [x] Solo entra quien tiene acceso a Presupuestos; presupuesto dado de baja → 404
- [x] La Orden de Fabricación no cambia (no se tocó)

Cambio respecto del REQ: el botón usa `btn btn-secondary`, como el resto de la botonera desde el rediseño «Taller»,
en lugar del azul que pedía el REQ. «Recibo» ahora está en el menú «⋯», así que el botón va al lado de «Presupuesto».

## Archivos

| Archivo | Cambio |
|---|---|
| `presupuestos/documentos_pdf.py` | `build_medicion_context(presupuesto, user, fecha)` |
| `presupuestos/views.py` | Vista `medicion` (GET, `@login_required`, `get_object_or_404` con `deleted_at__isnull=True`) |
| `presupuestos/urls.py` | `<int:pk>/medicion/`, name `presupuestos-medicion` |
| `presupuestos/templates/presupuestos/medicion_pdf.html` | Nuevo; extiende `core/pdf/base_a4.html` |
| `presupuestos/templates/presupuestos/detalle.html` | Botón «Medición» |
| `usuarios/access_control.py` | Ruta registrada con `presupuestos.view` |
| `presupuestos/tests.py` | `PlanillaMedicionPdfTest` (7 tests) |

## Decisiones técnicas

- Se reutiliza la base común de PDF (`contexto_base_pdf`, `filas_cliente`, `pdf_response`) sin agregar nada a `core`.
- El PDF sale `inline` como `medicion_<numero>.pdf`.
- Render verificado con un script de scratchpad (`render_to_string` + pisa + pypdfium2): una hoja, sin cortes.
