# REQ-005 — Página de detalle de cliente

> Estado: En desarrollo
> Fecha: 2026-03-06
> Derivó en: FEAT-004

## User Story

Como usuario del sistema, quiero ver una página de detalle de cada cliente que consolide toda su información y actividad comercial, para tener una visión completa de la relación con ese cliente sin tener que navegar por múltiples secciones.

## Criterios de Aceptación

- [ ] La URL es `/comercial/clientes/ver/<id>/`
- [ ] Muestra los datos personales del cliente (nombre, CUIT, condición IVA, dirección, teléfono, email)
- [ ] Muestra KPIs destacados: total comprado, saldo pendiente total, cantidad de ventas, cantidad de facturas emitidas
- [ ] Muestra el historial completo de ventas del cliente
- [ ] Muestra el historial de todos los pagos recibidos
- [ ] Muestra las facturas electrónicas emitidas al cliente
- [ ] El listado de clientes tiene un botón "Ver" que navega al detalle
- [ ] La página es visualmente atractiva y consistente con el design system

## Complejidad

Mediano

## Notas

Los gastos (Compras) están asociados a proveedores, no a clientes. El historial financiero del cliente se construye desde Venta, PagoVenta y Factura.
