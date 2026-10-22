# REQ-057 — Planilla de Colocación (PDF) desde el presupuesto confirmado

- **Estado:** Aprobado
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

- [ ] En un presupuesto confirmado con venta, el detalle muestra el botón "Colocación" (azul, ícono herramientas)
- [ ] El botón abre un modal con: colocador (desplegable de cuentas de tipo colocadores activas, opción "A definir"), fecha (por defecto hoy) y observaciones (precargadas con el comentario del presupuesto)
- [ ] "Generar" abre en una pestaña nueva un PDF A4 titulado **COLOCACIÓN** con la identidad Akun
- [ ] El PDF contiene colocador, fecha, cliente con ID, domicilio, localidad, provincia, teléfono, nº de presupuesto
- [ ] Tabla de aberturas con cantidad, tipología, medidas y color por ítem (puede ocupar varias hojas y repite el encabezado)
- [ ] Importes: valor total, seña / a cuenta, saldo pendiente, forma de pago; en PVC además cotización y montos en US$
- [ ] Recuadro de observaciones y firmas (colocador / cliente)
- [ ] En un presupuesto sin venta (o con la venta dada de baja) el botón no aparece y la URL redirige al detalle con un mensaje
- [ ] Un colocador que no sea de tipo colocadores (POST manipulado) sale en blanco

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

## Tests

- Sin venta → redirige con mensaje; con venta → 200 y PDF por GET y por POST
- Contexto: seña = sena + pagos; saldo; forma de pago combinada; cotización solo en PVC; ítem PVC con medidas y color vacíos; ítem de aluminio con color del snapshot
- Colocador de tipo proveedores posteado → sale en blanco
- El botón solo aparece si está confirmado con venta; la ruta está registrada
- `build_ficha_item` con `SimpleTestCase`; la salida de `build_pdf_item_context` no cambia tras el refactor
- Verificación visual con el script de PNG (varias hojas, corte de tabla)

**Migración:** No.
