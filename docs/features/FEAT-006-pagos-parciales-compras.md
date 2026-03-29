# FEAT-006 — Pagos Parciales en Compras

> **Estado**: Implementado
> **Fecha**: 2026-03-28
> **Requerimiento**: [REQ-007](../requerimientos/REQ-007-pagos-parciales-compras.md)

## Descripción Funcional

Se replicó la lógica de pagos del módulo de Ventas al módulo de Compras. Ahora las compras soportan:
- Monto total + seña (anticipo) al crear la compra
- Pagos parciales posteriores con historial completo
- Saldo dinámico recalculado automáticamente
- Vista de detalle con el mismo diseño que ventas

## Criterios Cumplidos

Todos los criterios de aceptación definidos en REQ-007 fueron verificados y aprobados.

## Archivos Modificados

| Archivo | Cambio |
|---------|--------|
| `comercial/models.py` | Modelo Compra: renombrado `importe_abonado`→`valor_total`, agregados `sena`, `saldo`, `estado`, `notas_internas`, `updated_at`, `save()` override. Nuevo modelo `PagoCompra` |
| `comercial/forms.py` | CompraForm actualizado con `valor_total`, `sena`, excluye campos calculados |
| `comercial/views.py` | 5 views nuevas: `compra_detail`, `registrar_pago_compra`, `editar_pago_compra`, `eliminar_pago_compra`, `guardar_nota_compra`. Renombre `importe_abonado`→`valor_total` en reportes y dashboard |
| `comercial/urls.py` | 6 rutas nuevas: detail, pago, API editar/eliminar pago, guardar nota |
| `comercial/admin.py` | Actualizado CompraAdmin + nuevo PagoCompraAdmin |
| `comercial/templates/comercial/compras/form.html` | Campo valor_total + seña |
| `comercial/templates/comercial/compras/list.html` | Columna saldo, boton Ver |
| `core/views.py` | Renombre `importe_abonado`→`valor_total` en dashboard home |

## Archivos Nuevos

| Archivo | Contenido |
|---------|-----------|
| `comercial/templates/comercial/compras/detail.html` | Vista detalle: KPIs, barra progreso, info compra, registrar pago, timeline, notas internas, historial pagos, modal editar pago |
| `comercial/migrations/0014_rename_importe_abonado_compra_valor_total_and_more.py` | Migración: renombre + campos nuevos + modelo PagoCompra |

## Decisiones Tecnicas

- Se reutilizó la misma estructura de diseño del `ventas/detail.html` adaptada a compras (sin percepciones, retenciones, WhatsApp, cotización dólar — funcionalidades exclusivas de ventas)
- El campo `importe_abonado` fue renombrado via `RenameField` en la migración para preservar datos existentes
- El estado de la compra cambia automáticamente a "pagado" cuando el saldo llega a 0, y vuelve a "pendiente" si se elimina un pago
- Las notas internas se guardan con `Compra.objects.filter().update()` para evitar el recálculo de saldo innecesario
