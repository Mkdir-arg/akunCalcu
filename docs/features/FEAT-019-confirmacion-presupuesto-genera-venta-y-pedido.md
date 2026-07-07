# FEAT-019 — Confirmación de presupuesto genera venta y pedido de fábrica

**Estado:** Implementado
**Fecha:** 2026-07-07
**Requerimiento:** [REQ-034](../requerimientos/REQ-034-confirmacion-presupuesto-genera-venta-y-pedido.md)

## Descripción funcional

Al cambiar el estado de un presupuesto a "Confirmado" desde su pantalla de detalle, un popup (SweetAlert2) pide el monto de la seña cobrada antes de ejecutar el cambio:

- Muestra el total del presupuesto como referencia.
- Precarga la seña sugerida según la modalidad guardada (50% o 70% del total), editable.
- La moneda depende del material: PVC en USD (con la cotización del presupuesto), Aluminio en pesos.
- La seña es obligatoria (mayor a 0) y no puede superar el total.

Al aceptar, en una única transacción (todo o nada):

1. El presupuesto pasa a "Confirmado" (queda bloqueado para edición, como antes).
2. Se crea una **Venta** en `comercial` con: cliente del presupuesto, número de pedido = número del presupuesto, valor total, seña ingresada (con `sena_usd`/cotización si es PVC) y estado "Pendiente". El saldo lo calcula `Venta.save()` y el circuito existente de pagos parciales y recibos funciona sin cambios sobre esa venta.
3. Se crea un **Pedido de fábrica** en `plantillas` con: número correlativo `PF-XXXX`, cliente (nombre del cliente del presupuesto), observación con referencia al presupuesto, estado "Borrador" y **sin ítems** — el despiece lo carga fábrica después.

El presupuesto queda vinculado a la venta (se activó la FK `venta`, declarada desde la migración 0002 pero nunca usada) y al pedido (FK nueva). El detalle del presupuesto confirmado muestra la tarjeta "Generado al confirmar" con links a ambos registros. Si se cancela el popup o falla una validación, no cambia nada. Los demás estados (Enviado, Vencido, Cancelado) siguen funcionando igual, sin popup.

## Criterios de aceptación cumplidos

- [x] Popup de seña al elegir "Confirmado" y presionar "Actualizar estado"; demás estados sin popup.
- [x] Popup con total de referencia y seña precargada según `modalidad_sena` (50%/70%), editable.
- [x] Moneda según material: PVC → USD con la cotización del presupuesto; Aluminio → pesos.
- [x] Seña obligatoria (> 0) y ≤ total, validada en servidor.
- [x] Operación atómica: estado + venta + pedido de fábrica.
- [x] Presupuesto vinculado a la venta (FK `venta`) y navegación a venta y pedido desde el detalle.
- [x] Cancelar el popup no cambia nada.
- [x] Sin doble venta/pedido para el mismo presupuesto.

## Archivos modificados

- `akuna_calc/plantillas/models.py`
- `akuna_calc/plantillas/migrations/0013_pedidofabrica_presupuesto.py` (nueva)
- `akuna_calc/presupuestos/models.py`
- `akuna_calc/presupuestos/views.py`
- `akuna_calc/presupuestos/templates/presupuestos/detalle.html`
- `akuna_calc/presupuestos/tests.py`

## Decisiones técnicas

- **Sin URLs nuevas**: la seña viaja como campo `sena` en el mismo POST del formulario de estado; `cambiar_estado` deriva a `_procesar_confirmacion()` solo cuando el estado destino es `confirmado`. Ver ADR-012.
- La venta se crea programáticamente replicando la conversión USD del `VentaForm` manual (`(usd × cotización).quantize(0.01)`).
- Número de pedido `PF-XXXX` buscando el primer número libre (el campo es `unique`; evita colisiones con pedidos manuales).
- Validación fuerte en servidor (el popup es solo UX): seña obligatoria/rango, PVC exige cotización USD, total > 0.
- FK `PedidoFabrica.presupuesto` nullable con `SET_NULL`: los pedidos manuales existentes y futuros siguen igual.
- Los ítems del presupuesto no se traducen al pedido de fábrica (las plantillas de despiece no mapean con los ítems del cotizador).

## Validación

- `python manage.py test presupuestos plantillas --settings=akuna_calc.settings_test_sqlite`
- Resultado: **98 tests OK** (15 nuevos en `ConfirmarPresupuestoTest`, sin regresiones).

## Pendiente de deploy

- Migración `plantillas/0013` pendiente de aplicar en Docker/Railway (se suma a las anteriores acumuladas).
