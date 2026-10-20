# REQ-060 — Gastos diferenciados por moneda en los reportes

- **Estado:** Aprobado (interpretación a confirmar con el cliente antes de codificar)
- **Fecha:** 2026-10-20
- **Complejidad:** Pequeño / Mediano
- **Origen:** RF-011 (prioridad Media): "Agregar gastos en pesos en tipos de gastos. Objetivo: permitir registrar gastos diferenciados por moneda. Observación: evaluar compatibilidad con reportes."
- **Plan:** [Plan RF Akun — octubre 2026](../team/plan-rf-akun-2026-10.md) · Sprint 3
- **Apps afectadas:** `comercial`

## User Story

Como **administrativo** quiero **ver los gastos de cada tipo separados en pesos y en dólares** para
**saber cuánto gasté en cada moneda sin que se mezclen**.

## Qué muestra el código

- La moneda **ya es un dato de cada gasto** (`Compra.compra_en_dolares`), no del tipo: un mismo tipo puede tener gastos en pesos y en USD. Registrar gastos en dólares ya es posible
- **Todos los reportes de gastos mezclan monedas sin decirlo**: suman `valor_total` (equivalente en pesos) y ninguna plantilla menciona USD (`reportes_gastos` ~l.2219-2251 con totales por tipo de cuenta y por tipo de gasto, el Excel, `compras/list.html`)
- Bug vecino: el Excel de gastos (`exportar_reporte_gastos_excel` ~l.2412-2494) **ignora los filtros** que el reporte guarda en la sesión y exporta todo; tampoco tiene columna Tipo de Gasto

## Interpretación adoptada

"Diferenciar por moneda los gastos dentro del reporte por tipo de gasto", con el mismo patrón que las cobranzas en USD (REQ-022). **Se le muestra al cliente en una línea antes de codificar.**

Descartadas: moneda en `TipoGasto` (modela mal el dato) y moneda en Gastos Diarios por voz (requiere migración, cotización y parseo; además esa entrada está caída porque el webhook de Meta apunta a la Evolution que ya no existe).

## Criterios de Aceptación

- [ ] El reporte de gastos tiene filtro Moneda: todas / solo pesos / solo USD
- [ ] "Total por Tipo de Gasto" y "Total por Tipo de Cuenta" muestran una columna Pesos y una columna USD (informativa)
- [ ] El detalle del reporte y el listado de gastos marcan con un distintivo los gastos en USD
- [ ] El total en pesos no cambia respecto de hoy
- [ ] El Excel respeta los filtros aplicados (incluida la moneda) y suma columnas Tipo de Gasto y USD
- [ ] Dashboard y reporte general quedan como están (equivalente en pesos); se aclara en la documentación

## Diseño técnico

- `comercial/forms.py` (`ReporteGastosForm` ~l.393-434): campo `moneda` igual a `moneda_cobranza`
- `comercial/views.py` (~l.2167-2273): filtrar por `compra_en_dolares` y `valor_total_usd > 0`; agregar `monto_usd` y `es_usd` a cada gasto; `total_usd` por grupo; guardar `moneda` en la sesión
- `comercial/views.py` (~l.2412-2494): leer los filtros de la sesión como hace `exportar_reporte_excel` (~l.2080) y agregar columnas
- Plantillas `reportes/reportes_gastos.html` (~l.120-160 y tabla 168+) y `compras/list.html` (~l.107)

## Tests

- Filtro solo USD y solo pesos
- `por_tipo_gasto` con `total_usd` separado y el total en pesos intacto
- El Excel respeta los filtros de la sesión
- `ReportesGastosTest` (~l.1725) sigue pasando

**Migración:** No.
