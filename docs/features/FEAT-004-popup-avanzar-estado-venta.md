# FEAT-004 — Popup para avanzar estado al completar pago

**Requerimiento:** [REQ-004](../requerimientos/REQ-004-popup-avanzar-estado-venta.md)
**Fecha:** 2026-03-06

## Descripción funcional

Al registrar un pago que deja el saldo de una venta en $0, el sistema detecta automáticamente esta condición y muestra un popup SweetAlert2 preguntando si el usuario desea cambiar el estado de la venta de `pendiente` a `colocado`. Si confirma, el cambio se aplica via AJAX sin recargar la página; si cancela, el estado permanece sin cambios.

El popup solo aparece cuando el estado de la venta es `pendiente` — no se activa si la venta ya está en `entregado` o `colocado`.

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `akuna_calc/comercial/views.py` | + `from django.urls import reverse`; `venta_detail` pasa `avanzar_estado` al context; `registrar_pago` redirige con `?avanzar_estado=1` si saldo=0 y estado=pendiente; nueva view `cambiar_estado_venta` |
| `akuna_calc/comercial/urls.py` | + `path('api/venta/<int:pk>/cambiar-estado/', ...)` |
| `akuna_calc/comercial/templates/comercial/ventas/detail.html` | + bloque JS con SweetAlert2 condicional a `avanzar_estado` |

## Decisiones técnicas

- Se usa query param `?avanzar_estado=1` para pasar el flag entre el redirect de `registrar_pago` y `venta_detail`, evitando uso de sesiones o cookies.
- El cambio de estado se realiza via `fetch` POST al endpoint `/api/venta/<pk>/cambiar-estado/` con `Content-Type: application/x-www-form-urlencoded` y CSRF token en header.
- El endpoint `cambiar_estado_venta` valida que el estado enviado esté en `ESTADO_CHOICES` antes de guardar.
