# REQ-054 — ID de cliente visible en todo el sistema + Provincia del cliente

- **Estado:** Aprobado
- **Fecha:** 2026-10-20
- **Complejidad:** Mediano
- **Origen:** RF-023 (prioridad Alta). La provincia la pide RF-02 (PDF de Colocación, REQ-057); se resuelve acá porque es un dato del cliente.
- **Plan:** [Plan RF Akun — octubre 2026](../team/plan-rf-akun-2026-10.md) · Sprint 1
- **Apps afectadas:** `comercial`, `presupuestos`, `core`

## User Story

Como **administrativo o vendedor** quiero **que cada cliente tenga un ID único, correlativo y no
editable, visible en Clientes, Presupuestos y Ventas**, para **identificarlo sin ambigüedad
(dos clientes con el mismo nombre) y seguir su historia**.

## Decisiones tomadas

| Pregunta | Decisión | Motivo |
|---|---|---|
| ¿Numeración nueva o el ID interno? | **El ID interno (pk) formateado: `C-00123`** | Ya es único, correlativo y no editable. Sin migración ni backfill. MySQL 8 no reutiliza ids. Los huecos (clientes dados de baja, inserts fallidos) son aceptables para trazabilidad |
| ¿Cambiar el nombre del cliente (`__str__`)? | **No** | `__str__` lo usan `Venta.__str__`, `Presupuesto.__str__`, el orden A-Z de cobranzas, reportes, auditoría, AFIP y asientos contables. El código se muestra aparte |
| ¿Provincia como texto o tabla? | **FK opcional a `core.Provincia`** (existe sin uso, tabla vacía) | Datos normalizados para los PDFs; un texto libre traería "Bs As"/"BA"/"Buenos Aires" |
| ¿Completar la provincia de los clientes existentes? | **No** | `localidad` es texto libre, no se puede deducir con seguridad. Quedan vacíos y se completan al editar |

## Criterios de Aceptación

**ID de cliente**
- [ ] Todo cliente muestra su ID con formato `C-00123` (5 dígitos, el pk) y no se puede editar en ningún formulario
- [ ] Clientes: columna "ID" en el listado, ID en el encabezado del detalle y de solo lectura en el form de edición
- [ ] Ventas: ID debajo del nombre en el listado (tabla y kanban) y en el detalle
- [ ] Presupuestos: ID en el listado y en el detalle
- [ ] El select de cliente de Ventas y de Presupuestos muestra "Nombre · C-00123" y se puede buscar por el ID
- [ ] El buscador de Clientes acepta `C-123`, `c123` o el número solo; Ventas y Presupuestos aceptan `C-123` (con prefijo, para no mezclar con nº de pedido/presupuesto)
- [ ] El Excel de ventas tiene una columna "ID Cliente" y los totales siguen en sus columnas
- [ ] El PDF del presupuesto muestra el ID en "Datos del cliente"

**Provincia**
- [ ] Existen las 24 jurisdicciones (23 provincias + CABA) cargadas por migración
- [ ] El cliente tiene un campo Provincia **opcional** en el alta, la edición y el modal de alta rápida (REQ-055); dar de alta sin provincia sigue funcionando
- [ ] Se ve en el detalle del cliente

## Diseño técnico

**Piezas compartidas en `Cliente` (`comercial/models.py` ~l.72)**, que después usan los PDFs de REQ-056/057/058:
- `@property codigo` → `f"C-{self.pk:05d}"`
- `etiqueta_selector()` → `f"{self} · {self.codigo}"` (Select2 busca sobre ese texto)
- `@staticmethod pk_desde_codigo(texto, permitir_numero=False)` → acepta `C-00123`, `c123`, `C 123`; devuelve int o None
- `datos_documento()` → dict `codigo, nombre_completo, direccion, localidad, provincia ('' si null), cuit formateado, condicion_iva, telefono, email`. **Única fuente de datos del cliente para todos los PDFs**: reemplaza el armado repetido en `Recibo.construir_pdf_bytes` (~l.563) y `_build_blank_recibo_context` (`presupuestos/views.py` ~l.759)
- `provincia = ForeignKey('core.Provincia', on_delete=PROTECT, null=True, blank=True, related_name='clientes', verbose_name='Provincia')`

**Migraciones**
- `core/migrations/0002_seed_provincias.py`: RunPython con `get_or_create` por código ISO; reversa noop
- `comercial/migrations/0024_cliente_provincia.py`: depende de `core 0002` y de la última de `comercial`

**Formularios**
- `ClienteForm` (`comercial/forms.py` ~l.37): `fields='__all__'` → `exclude=['deleted_at']` (hoy expone `deleted_at`, y editar un cliente dado de baja podría reactivarlo); provincia con queryset `activo=True` y `empty_label="Sin especificar"`
- `VentaForm.__init__` (~l.72) y `PresupuestoForm` (`presupuestos/forms.py` ~l.29): `self.fields['cliente'].label_from_instance = Cliente.etiqueta_selector`

**Pantallas** (líneas aproximadas)
- `clientes/list.html` columna en l.43/54 (el `colspan` del vacío pasa de 6 a 7); `clientes/detail.html` l.23-38 y l.113; `clientes/form.html` código de solo lectura si `form.instance.pk`, provincia después de localidad (~l.86)
- `ventas/list.html` l.226-227 y kanban l.383; `ventas/detail.html` l.30 y l.143
- `presupuestos/lista.html` l.137; `presupuestos/detalle.html` l.79 y l.138; `presupuestos/pdf.html` l.519
- Opcional: `security/fusionar.html` (ayuda a distinguir duplicados con el mismo nombre; plantilla genérica → `{% if c.codigo %}`)

**Búsquedas**
- `clientes_list` (`comercial/views.py` ~l.822): `pk_desde_codigo(q, permitir_numero=True)` → `Q(pk=n)`; actualizar el placeholder
- `ventas_list` (~l.303), `exportar_ventas_excel` (~l.937, mantener sincronizado) y `presupuestos.lista` (~l.145): solo con prefijo → `Q(cliente_id=n)`

**Excel de ventas** (`views.py` ~l.966-1008): columna "ID Cliente" después de "Cliente"; se corren los índices de formato numérico y totales (`[5,6,7]`→`[6,7,8]`, `range(1,11)`→`range(1,12)`, un ancho más en `col_widths`)

**JSON del alta AJAX** (`views.py` ~l.849): agregar `codigo` y `etiqueta`, mantener `nombre`

## Qué NO se toca

`Cliente.__str__`, `get_nombre_completo`, facturación AFIP, asientos de contabilidad, el nombre copiado en `PedidoFabrica`, agenda y reportes multiselect.

## Impacto

- **Borrado físico:** la app solo da de baja lógica (merge FEAT-029 también). El único borrado físico posible es la acción masiva del admin de Django (`queryset.delete()`), que borraría ventas en CASCADE. Refuerzo incluido: quitar la acción "eliminar seleccionados" de `ClienteAdmin` (`comercial/admin.py` ~l.11)
- No hay tests que comparen `str(cliente)` exacto
- La migración de datos de provincias debe correr también con `settings_test_sqlite`

## Tests

- `codigo` y `pk_desde_codigo` (variantes de formato, texto inválido → None)
- La etiqueta del select de ventas y presupuestos contiene el código
- `clientes_list?q=C-000xx` encuentra el cliente; `ventas_list?q=C-xx` filtra
- Excel de ventas: columna nueva y totales en las columnas correctas
- La migración deja 24 provincias; alta de cliente sin provincia → 302; con provincia → se guarda
- `datos_documento()['provincia'] == ''` si es null

**Migración:** Sí (`core/0002` datos + `comercial/0024` campo nullable). No afecta registros existentes.
