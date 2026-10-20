# FEAT-043 — ID de cliente en todo el sistema + Provincia del cliente

- **Estado:** Implementado
- **Fecha:** 2026-10-20
- **Requerimiento:** [REQ-054](../requerimientos/REQ-054-id-cliente-y-provincia.md) (RF-023)
- **Sprint:** Sprint 1 — plan RF Akun
- **Apps:** `comercial`, `presupuestos`, `core`
- **Migración:** `core/0002_seed_provincias` (carga las 24 jurisdicciones) + `comercial/0024_cliente_provincia` (FK nullable)

## Qué hace

Cada cliente se identifica con **`C-00123`**: el ID interno con 5 dígitos. Es único, correlativo y
no se puede editar porque no es un campo, es una propiedad (`Cliente.codigo`). Se ve en:

- **Clientes:** columna ID del listado, encabezado y bloque Información del detalle, y de solo lectura en el form de edición
- **Ventas:** debajo del nombre en la tabla y el kanban, y en el detalle
- **Presupuestos:** listado, detalle y PDF ("Datos del cliente")
- **Selects de cliente** de Ventas y Presupuestos: "Nombre · C-00123". Select2 busca sobre ese texto, así que se encuentra con el código completo (`C-00123`) o los dígitos (`00123`, `123`)
- **Excel de ventas:** columna "ID Cliente" después de "Cliente"

Buscadores: Clientes acepta `C-123`, `c123` o el número solo; Ventas y Presupuestos solo con prefijo
(`C-123`), porque el número solo ya busca por nº de pedido o de presupuesto. El código **suma** una
condición a la búsqueda, no reemplaza la existente.

El cliente tiene además **Provincia** opcional (FK a `core.Provincia`, que existía sin uso y vacía).
Los clientes existentes quedan sin provincia: la localidad es texto libre y no se puede deducir.

## Decisiones técnicas

- **No se tocó `Cliente.__str__` ni `get_nombre_completo`**: los usan `Venta.__str__`, `Presupuesto.__str__`, el orden A-Z de cobranzas, reportes, auditoría, AFIP y contabilidad. El código se muestra aparte, con `label_from_instance = Cliente.etiqueta_selector` en los forms
- **`Cliente.datos_documento()`** es la única fuente de los datos del cliente para documentos (código, nombre, domicilio, localidad, provincia, CUIT formateado, IVA, teléfono, email). Ya la usan los dos recibos; la van a usar los PDFs de Medición, Colocación y Recibo (REQ-056/057/058)
- `ClienteForm` pasó de `fields='__all__'` a `exclude=['deleted_at']`: antes exponía la baja lógica y editar un cliente dado de baja podía reactivarlo
- Se quitó la acción "eliminar seleccionados" de `ClienteAdmin`: era el único camino de borrado físico y borraba las ventas en cascada
- `pk_desde_codigo` limita a 9 dígitos para no armar consultas con números absurdos

## Criterios cumplidos

- [x] ID `C-00123` no editable en Clientes, Ventas y Presupuestos (listados, detalles, selects)
- [x] Búsqueda por ID en los tres módulos
- [x] Columna "ID Cliente" en el Excel con los totales en sus columnas
- [x] ID en el PDF del presupuesto
- [x] 24 jurisdicciones cargadas por migración (idempotente; la reversa no borra datos)
- [x] Provincia opcional en alta y edición; visible en el detalle

## Archivos

- `comercial/models.py` (campo `provincia`, `codigo`, `etiqueta_selector`, `pk_desde_codigo`, `datos_documento`; `Recibo.construir_pdf_bytes` usa `datos_documento`)
- `comercial/forms.py`, `comercial/admin.py`, `comercial/views.py` (búsquedas, Excel, JSON del alta AJAX)
- `comercial/templates/comercial/clientes/{list,detail,form}.html`, `ventas/{list,detail,form}.html`
- `presupuestos/forms.py`, `presupuestos/views.py`, `presupuestos/templates/presupuestos/{lista,detalle,pdf}.html`
- `core/migrations/0002_seed_provincias.py`, `comercial/migrations/0024_cliente_provincia.py`
- `comercial/tests.py` → `ClienteCodigoTest`, `ClienteProvinciaTest`
