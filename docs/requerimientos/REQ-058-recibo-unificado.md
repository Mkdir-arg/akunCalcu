# REQ-058 — Recibo unificado entre Presupuestos y Ventas

- **Estado:** Aprobado
- **Fecha:** 2026-10-20
- **Complejidad:** Mediano
- **Origen:** RF-01 (prioridad Alta)
- **Depende de:** [REQ-054](./REQ-054-id-cliente-y-provincia.md) (`datos_documento()`) y [REQ-056](./REQ-056-pdf-medicion-y-base-pdf-comun.md) (helper del logo y `pdf_response`)
- **Plan:** [Plan RF Akun — octubre 2026](../team/plan-rf-akun-2026-10.md) · Sprint 2
- **Apps afectadas:** `comercial`, `presupuestos`

## User Story

Como **administrativo** quiero **que el recibo que sale de Presupuestos sea el mismo que el de
Ventas** para **mantener un único formato y que un cambio futuro se haga en un solo lugar**.

## Situación actual

| Aspecto | Presupuestos (`recibo_blank.html`) | Ventas (`recibo_pdf.html`) |
|---|---|---|
| Uso | Planilla en blanco para completar a mano | Recibo con los datos reales del pago (modelo `Recibo`) |
| Copias | 2 | 1 (ORIGINAL) |
| Datos | Todo vacío | Fecha, importe en letras, concepto, pagos, retenciones, firma |
| Tipografía / logo | 14px / logo 145 | 16px / logo 170 |

Ambos son A4 apaisado con el mismo encabezado fiscal.

## Decisiones tomadas

- **Queda una sola plantilla: la de Ventas** (`comercial/recibo_pdf.html`). Se borra `recibo_blank.html`
- Desde Presupuestos se renderiza **la misma plantilla** con lo que se conoce (cliente con ID, nº de presupuesto y total en el concepto) y los datos del pago **en blanco** para completar a mano
- **Una copia**, como en Ventas ("mismo diseño, campos y funcionalidades")
- **Desde Presupuestos nunca se crea un `Recibo`** ni se muestra el próximo número: adelantaría o pisaría la numeración (además `Recibo.pago` es obligatorio). El Nº queda en blanco
- El recibo **mantiene su diseño** (documento fiscal para el cliente); no adopta la base azul de los PDFs internos. Solo comparte el helper del logo
- **Fuera de alcance, para avisar al cliente:** el encabezado del recibo tiene hardcodeado "Elpidio González 5326" mientras la configuración dice "José Cubas 4388". Puede ser domicilio fiscal vs. comercial; no se toca sin confirmar

## Criterios de Aceptación

- [ ] El botón "Recibo" del presupuesto descarga un recibo con el mismo diseño, campos y tamaños que el de Ventas
- [ ] Muestra los datos del cliente (con ID), y en el concepto el nº de presupuesto y el total (en US$ en PVC)
- [ ] Fecha, Nº, importe en letras, pagos, retenciones y total quedan en blanco (no "0,00") para completar a mano
- [ ] Entra en una hoja (verificado con el render a PNG)
- [ ] Generar el recibo desde el presupuesto **no crea ningún registro de Recibo** ni consume numeración
- [ ] El recibo de Ventas sale exactamente igual que antes
- [ ] Se conserva el nombre de archivo `recibo_plantilla_<numero>.pdf`

## Diseño técnico

- `comercial/recibos.py` (nuevo): `contexto_cliente_recibo(cliente)` (hoy duplicado en `comercial/models.py` ~l.563-568 y `presupuestos/views.py` ~l.759-771; pasa a usar `datos_documento()`) y `render_recibo_pdf_bytes(context)`
- `Recibo.construir_pdf_bytes` usa esas funciones y **mantiene su firma** (hay tests que la parchean)
- `presupuestos/views.py` ~l.759-799: `recibo()` arma el contexto de planilla y llama a `core.pdf.pdf_response`; se borran `_build_blank_recibo_context` y `recibo_blank.html`
- Contexto en modo planilla: `recibo` como **dict** (`numero=''`, `importe_letras=''`, `concepto='Presupuesto PRES-… — total $X'`, `importe=None`), retenciones y `fecha_texto` vacías, `first_page_payment_rows` con 1 fila en blanco (`'\xa0'`, `importe=None`). Probar 2 filas con el PNG; si desborda a una segunda hoja, queda 1
- `comercial/templates/comercial/recibo_pdf.html`, guardas que en Ventas siempre se cumplen (no cambia su salida):
  - TOTAL (~l.173 y 243): `{% if recibo.importe %}` (porque `formato_numero(None)` devuelve `'0,00'`)
  - Importes de filas (~l.149, 196, 219): `{% if row.importe %}`
  - Fecha (~l.79): `|default` con espacios para que el recuadro no colapse
  - Importe en letras y concepto (~l.124 y 128): `|default:"&nbsp;"`

## Impacto

URLs y permisos sin cambios (`presupuestos-recibo`, `descargar_pdf_recibo_venta` y `descargar_pdf_recibo` ya registradas). Datos: ninguno.

## Tests

- Deben seguir pasando: `comercial/tests.py` (~l.3-20 y 424-477), `presupuestos/tests.py` (~l.956 botón, ~l.1031 descarga)
- Nuevos: recibo desde presupuesto → `Recibo.objects.count() == 0`; HTML en modo planilla contiene el nº de presupuesto y **no** contiene "0,00"; HTML de un `Recibo` real sigue mostrando número e importe formateado
- Render a PNG antes y después del recibo de Ventas: idéntico

**Migración:** No.
