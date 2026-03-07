# FEAT-004 — Página de detalle de cliente

> Estado: Implementado
> Fecha: 2026-03-06
> Sprint: —
> REQ: REQ-005

## Descripción funcional

Página en `/comercial/clientes/ver/<id>/` que consolida toda la información comercial de un cliente en un solo lugar.

## Criterios cumplidos

- [x] URL `/comercial/clientes/ver/<id>/`
- [x] Datos personales del cliente (nombre, CUIT, condición IVA, dirección, teléfono, email)
- [x] KPIs: total comprado, total cobrado, saldo pendiente, cantidad de ventas, facturas emitidas
- [x] Historial de ventas con estado y saldo coloreado
- [x] Historial de pagos con forma de pago e íconos
- [x] Facturas electrónicas con CAE y estado
- [x] Gráfico de barras: ventas por mes (últimos 12 meses)
- [x] Gráfico donut: distribución de pedidos por estado
- [x] Botón "Ver" en el listado de clientes
- [x] 4 tests pasando

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `comercial/views.py` | Vista `cliente_detail` agregada |
| `comercial/urls.py` | URL `clientes/<int:pk>/ver/` agregada |
| `comercial/templates/comercial/clientes/list.html` | Botón "Ver" (ojo azul) por fila |
| `comercial/templates/comercial/clientes/detail.html` | Template nuevo creado |
| `comercial/tests.py` | Tests creados (4 tests) |

## Decisiones técnicas

- Chart.js 4.4.0 agregado via CDN en `extra_js` (no en base.html). Ver ADR-005.
- Los gastos (Compras) no se muestran por cliente porque en el modelo están ligados a proveedores (Cuenta), no a clientes.
- Pagos limitados a los últimos 30 en la query para evitar listas muy largas.
