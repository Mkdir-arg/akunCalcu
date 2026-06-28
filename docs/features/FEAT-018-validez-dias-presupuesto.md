# FEAT-018 — Validez del presupuesto en días

**Estado:** Implementado
**Fecha:** 2026-06-29

## Descripción funcional

En "Configuración de obra" del presupuesto se puede indicar la **validez en días** del presupuesto. Ese número **maneja la fecha de vencimiento**: `fecha_expiracion = fecha de creación + validez_dias`. El PDF muestra **"Validez: X días (hasta DD/MM/YYYY)"**.

Decisión (opción A, acordada con el usuario): la validez en días es la fuente; la fecha de vencimiento se deriva de ella, manteniendo un solo dato coherente en detalle, listado y PDF.

## Criterios de aceptación (cumplidos)

- [x] Campo "Validez (días)" en el panel "Configuración de obra".
- [x] Al guardar, recalcula `fecha_expiracion = created_at + validez_dias`.
- [x] Default 30 días; mínimo 1 (validado en el form).
- [x] El PDF muestra "Validez: X días (hasta DD/MM/YYYY)".

## Archivos involucrados

| Archivo | Cambio |
|---------|--------|
| `presupuestos/models.py` | Campo `validez_dias` (PositiveIntegerField, default 30) + método `aplicar_validez_dias()` |
| `presupuestos/migrations/0009_presupuesto_validez_dias.py` | NUEVO — AddField (modelo gestionado, migración Django normal) |
| `presupuestos/forms.py` | `PresupuestoConfiguracionObraForm`: campo `validez_dias` + validación (mín. 1, default 30) |
| `presupuestos/views.py` | `actualizar_configuracion_obra`: llama `aplicar_validez_dias()` tras guardar |
| `presupuestos/templates/presupuestos/detalle.html` | Input "Validez (días)" en el form de config obra |
| `presupuestos/templates/presupuestos/pdf.html` | "Validez: X días (hasta fecha)" |
| `presupuestos/tests.py` | Tests de default, recálculo y POST de config obra |

## Decisiones técnicas

- La validez se cuenta desde `created_at` (fecha de creación del presupuesto), no desde "hoy", para que sea estable.
- `validez_dias` es la fuente; `fecha_expiracion` se deriva. Toda la UI/PDF sigue usando `fecha_expiracion` (sin cambios en esa lógica).

## Pendiente de deploy

Requiere correr la migración `0009_presupuesto_validez_dias` en Docker/Railway (es migración Django normal, tabla gestionada — no legacy).
