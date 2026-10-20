# REQ-059 — Cuenta corriente de proveedores en pesos y en dólares

- **Estado:** Aprobado
- **Fecha:** 2026-10-20
- **Complejidad:** Grande
- **Origen:** RF-004 (prioridad Alta) + RF-017 (prioridad Media), juntos porque tocan el mismo reporte. Retoma lo que quedó abierto de REQ-010 / REQ-017.
- **Plan:** [Plan RF Akun — octubre 2026](../team/plan-rf-akun-2026-10.md) · Sprint 3
- **Apps afectadas:** `comercial`
- **ADR:** ADR-022 (a registrar al implementar): cuenta corriente bimonetaria

## User Story

Como **administrativo** quiero **ver la cuenta corriente de cada proveedor separada en pesos y en
dólares, con los pagos en US$ bien identificados y un acceso directo para corregir un movimiento**,
para **saber cuánto le debo realmente en cada moneda**.

## Hallazgo que define el diseño

**Hoy no existe un saldo en dólares.** `Compra.save()` calcula `saldo = valor_total - sena - Σ pagos.monto`,
todo en pesos. Una compra en USD se guarda en pesos a la cotización del día de compra, y cada pago en
USD a la cotización del día de pago: **la diferencia de cambio aparece como deuda o saldo a favor
falso** aunque en dólares esté saldada. El reporte (`construir_cuenta_corriente_proveedor`,
`comercial/views.py` ~l.186) suma todo en pesos y no menciona USD en ningún lado.

## Decisiones tomadas

- **Dos cuentas por proveedor:**
  - **Cuenta en pesos:** compras en pesos, con sus señas y pagos por `monto`. Un pago hecho en US$ sobre una compra en pesos impacta por su monto en pesos (como lo cargó el usuario) y se marca "USD 500 @ 1.350"
  - **Cuenta en USD:** compras en dólares con `valor_total_usd` y `cotizacion_usd`. Debe = `valor_total_usd`; haber de seña y pagos en USD = su monto USD; seña o pago hecho en pesos = `monto / cotización de la compra`, marcado "≈ convertido". Una compra USD sin cotización (dato viejo) se trata como pesos
- **"Saldos consolidados"** = saldo en pesos y saldo en USD por proveedor, y totales por moneda de todos los proveedores. **Nunca se suman monedas en silencio**
- Se mantiene **Debe = compras, Haber = pagos** como hoy (Xubio lo usa al revés; cambiarlo confundiría)
- **Botón de edición por fila:** compra o seña → editar la compra; pago → detalle de la compra con el modal de edición del pago abierto. En el listado, además, editar el proveedor
- **Fase 2, fuera de este REQ:** que una compra USD pase a "pagado" cuando su saldo en dólares llega a 0 (hoy puede quedar pendiente o marcarse pagada antes de tiempo por la diferencia de cambio). Se registra como FIX aparte

## Criterios de Aceptación

- [ ] El detalle del proveedor muestra dos secciones: cuenta en pesos y cuenta en USD, cada una con debe, haber y saldo acumulado
- [ ] Los pagos en dólares se distinguen visualmente (fondo verde claro, distintivo "USD x @ cotización") — RF-017
- [ ] Las conversiones aproximadas llevan la marca "≈"
- [ ] El listado de proveedores muestra saldo en pesos y saldo en USD, con totales por moneda
- [ ] Filtro de moneda: todas / pesos / USD (USD = proveedores con algún movimiento en dólares). Al filtrar, el saldo acumulado sigue siendo el completo y la pantalla lo aclara
- [ ] Cada fila del detalle tiene un botón Editar que lleva a corregir ese movimiento y vuelve al reporte al guardar; solo lo ve quien tiene acceso a Gastos
- [ ] El Excel incluye moneda, monto USD y cotización, y respeta el filtro de moneda
- [ ] El detalle de una compra en USD muestra una tarjeta "Saldo USD"
- [ ] Una compra USD 1000 @1000 pagada con USD 1000 @1200 muestra saldo USD 0 (hoy mostraría deuda falsa en pesos)

## Diseño técnico

- `comercial/models.py` (`Compra` ~l.312-372, `PagoCompra` ~l.375-402), métodos calculados **sin migración**, única fuente de verdad para el detalle y el reporte: `Compra.es_usd_contable`, `Compra.sena_en_usd()`, `Compra.saldo_usd` (property), `PagoCompra.monto_en_usd(cotizacion_fallback)`
- `comercial/views.py` ~l.186-269: `construir_cuenta_corriente_proveedor(proveedor, moneda='todas')` devuelve `cuentas={'ARS': {...}, 'USD': {...}}`; cada movimiento con `moneda, es_usd, monto_usd, cotizacion, convertido, edit_url`. **Las claves actuales** (`total_compras, total_senas, total_pagos, saldo_actual, movimientos`) se mantienen apuntando a la cuenta en pesos para no romper nada. La usan solo `reportes_proveedores`, `reporte_proveedor_detalle` y `exportar_reporte_proveedores_excel`
- Listado (~l.2276-2309): filtro `moneda` (`Exists` sobre compra o pago en USD), columnas de saldo por moneda, fila de totales
- Detalle (~l.2312-2327): dos secciones; `puede_editar = user_has_route_access(user, 'comercial:compra_edit')`
- Excel (~l.2330-2409): columnas Moneda / USD / Cotización
- `comercial/forms.py` (`ReporteProveedorForm` ~l.436-451): `ChoiceField moneda`, copiado de `ReporteCobranzasForm` (patrón de REQ-022)
- Plantillas `reportes/reporte_proveedor_detalle.html` y `reportes/reportes_proveedores.html`
- `compras/detail.html`: tarjeta "Saldo USD" (~l.107-114 y 423) y un JS chico que lee `?editar_pago=<id>` y abre el modal existente `editarPago` (~l.687; filas `pago-row-N`)
- Botones: `comercial:compra_edit` y `comercial:compra_detail?editar_pago=<id>#pago-row-<id>`, con `{% with_return_to %}` (`compra_edit` ya respeta el `return_to`); proveedor → `comercial:cuenta_edit`

## Impacto

- Sin FKs nuevas, sin URL names nuevos, sin rutas nuevas en `access_control`
- **Cambio visible en los datos:** las compras en USD salen de la cuenta en pesos y pasan a la de USD, así que **los totales en pesos del reporte bajan**. Antes de deployar: contar en producción cuántas compras USD hay y avisar al usuario
- `Compra.saldo` y `estado` **no cambian** en este REQ
- `test_reporte_proveedor_detalle_sin_linea_de_fecha_repetida` hace `assertNotContains('Fecha:')`: ninguna etiqueta nueva puede decir "Fecha:"

## Tests

1. Compra USD 1000 @1000 + pago USD 1000 @1200 → `saldo_usd == 0` y la compra no suma a la cuenta en pesos
2. Compra en pesos + pago en USD → cuenta en pesos, `es_usd`, el HTML contiene "USD"
3. Pago en pesos sobre compra USD → convertido a la cotización de la compra, marcado
4. `?moneda=usd` filtra proveedores
5. Botón editar visible con `comercial.gastos`, oculto con solo `reportes.proveedores`
6. Excel con filas USD → 200
7. Unit tests de `Compra.saldo_usd`
- `ComprasProveedorTest` (`comercial/tests.py` ~l.573-1103) debe seguir verde, incluido el caso RF-006 (compra en pesos + pago en USD que da saldo 3000)

**Migración:** No.
