# FEAT-011 — Estandarización de selectores buscables en todo el sistema

> **Requerimiento**: [REQ-026](../requerimientos/REQ-026-estandarizar-selectores-buscables-sistema.md)
> **Fecha**: 2026-05-17
> **Apps afectadas**: `core`, `comercial`, `pricing`, `facturacion`, `presupuestos`, `security`, `pedidos`, `gastos_diarios`

## Descripción funcional

Se unificó el comportamiento y la apariencia de los selectores del sistema para que usen el mismo patrón visual e interactivo del buscador **Tipo de Factura** del reporte de cobranzas.

- Los selects de formularios y filtros ahora comparten un estilo Select2 centralizado desde `core/base.html`.
- Los selects creados dinámicamente por JavaScript reutilizan el mismo helper global, evitando inicializaciones distintas por pantalla.
- Los modales que contienen selects ahora declaran su contenedor para que los dropdowns se rendericen correctamente dentro del modal.
- Se mantuvieron fuera del patrón solo los micro-selects inline donde el buscador perjudica la legibilidad o rompe una UI compacta: selectores tipo píldora de estado en tablas y selectores técnicos de variable/operador dentro de fórmulas de marco.

## Criterios de aceptación cumplidos

- [x] Los campos `<select>` de formularios, filtros y pantallas operativas usan el mismo patrón visual e interactivo que el selector de **Tipo de Factura** del reporte de cobranzas, salvo excepciones inline explícitas donde el buscador degrada la usabilidad.
- [x] El usuario puede buscar escribiendo dentro del selector en los casos operativos generales del sistema.
- [x] La estandarización aplica tanto a selects renderizados al cargar la página como a selects agregados dinámicamente mediante JavaScript.
- [x] Los selects conservan el comportamiento funcional actual: valor seleccionado, validaciones, guardado, filtros y envíos de formularios.
- [x] Los placeholders, estados deshabilitados, ancho visual y limpieza de selección mantienen un criterio uniforme en todo el sistema.
- [x] No se introdujeron librerías nuevas.
- [x] Existe una forma centralizada y reutilizable de aplicar el comportamiento mediante `window.AkunSelect2` en `core/base.html`.
- [x] Se agregaron tests del patrón común y de templates con selects dinámicos.

## Archivos modificados

- `akuna_calc/core/templates/core/base.html` — helper global `window.AkunSelect2` y estilo Select2 compartido.
- `akuna_calc/core/templates/core/includes/table_filters.html` — filtros compactos integrados al patrón global.
- `akuna_calc/core/tests.py` — test de render del helper y estilos compartidos.
- `akuna_calc/comercial/forms.py` — filtros de cobranzas alineados al patrón común.
- `akuna_calc/comercial/templates/comercial/reportes/reportes_cobranzas.html` — eliminación del CSS local duplicado del selector buscador.
- `akuna_calc/comercial/templates/comercial/ventas/form.html` — modal de cliente migrado al helper global con dropdown parent declarativo.
- `akuna_calc/comercial/templates/comercial/compras/form.html` — modal de cuenta migrado al helper global con dropdown parent declarativo.
- `akuna_calc/comercial/templates/comercial/ventas/list.html` — filtros de listado integrados al patrón buscable.
- `akuna_calc/comercial/tests.py` — regresión del render inicial de cobranzas con widgets unificados.
- `akuna_calc/pricing/forms.py` — selects dependientes de configuración habilitados para el patrón global.
- `akuna_calc/pricing/templates/pricing/config/hoja_form.html` — helper compartido para perfiles y accesorios dinámicos.
- `akuna_calc/pricing/templates/pricing/config/marco_form.html` — helper compartido para perfiles, accesorios y refresh de selects dependientes.
- `akuna_calc/pricing/templates/pricing/config/perfiles.html` — filtros alineados al patrón global.
- `akuna_calc/pricing/tests.py` — regresiones de `hoja_form` y `marco_form`.
- `akuna_calc/facturacion/templates/facturacion/crear_factura.html` — reinit global para selects agregados por formset.
- `akuna_calc/presupuestos/forms.py` — selector de tipo de obra alineado al patrón global.
- `akuna_calc/presupuestos/templates/presupuestos/lista.html` — filtro de estado alineado al patrón global.
- `akuna_calc/presupuestos/templates/presupuestos/detalle.html` — selector de cambio de estado alineado al patrón global.
- `akuna_calc/security/templates/security/audit_list.html` — filtros alineados al patrón global.
- `akuna_calc/pedidos/templates/pedidos/pedidos_list.html` — filtro de estado alineado al patrón global.
- `akuna_calc/gastos_diarios/templates/gastos_diarios/gasto_list.html` — filtro de estado alineado al patrón global.
- `docs/team/design-system.md` — reglas actualizadas del patrón Select2 global.
- `memory/MEMORY.md` — memoria del proyecto con el helper y excepciones permitidas.

## Decisiones técnicas

- Se reutilizó Select2 ya presente en el proyecto y se consolidó su configuración en `core/base.html` con un helper global: `window.AkunSelect2`.
- Los selects dinámicos deben usar `init`, `reinit` o `refresh` del helper compartido en lugar de instanciar Select2 manualmente pantalla por pantalla.
- Los modales deben declarar `data-select2-dropdown-parent` para que el dropdown quede contenido visualmente en el modal sin lógica duplicada.
- `no-select2` queda reservado para micro-selects inline muy compactos, no para formularios o filtros generales.

## Validación

- `python manage.py test core.tests.BaseTemplateSelect2HelperTest pricing.tests.HojaFormTemplateTest pricing.tests.MarcoFormTemplateTest comercial.tests.ReporteCobranzasTest.test_reporte_cobranzas_get_inicial_no_materializa_movimientos --settings=akuna_calc.settings_test_sqlite --verbosity 2`