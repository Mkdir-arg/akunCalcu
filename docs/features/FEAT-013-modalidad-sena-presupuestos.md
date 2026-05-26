# FEAT-013 — Modalidad de seña en presupuestos

**Estado:** Implementado  
**Fecha:** 2026-05-26  
**Requerimiento:** [REQ-029](../requerimientos/REQ-029-modalidad-sena-presupuestos.md)

## Descripción funcional

Se incorporó en Presupuestos un selector de modalidad de seña con opciones predefinidas para adelanto/saldo, integrado en el panel lateral de configuración con el mismo diseño visual del resto de campos.

Opciones disponibles:
- 50% adelanto / 50% saldo
- 70% adelanto / 30% saldo

Ubicación en UI:
- Pantalla de detalle de presupuesto, dentro del bloque "Configuración de obra".
- Debajo de "Tipo" (incluyendo cuando el estado era "Sin definir").

## Criterios de aceptación cumplidos

- [x] Se muestra menú desplegable para modalidad de seña en la pantalla de detalle/edición operativa.
- [x] El selector está debajo de "Tipo" dentro de "Configuración de obra".
- [x] El selector mantiene el mismo diseño visual que el resto del panel lateral.
- [x] Incluye exactamente las opciones 50/50 y 70/30.
- [x] La modalidad seleccionada se guarda en el presupuesto.
- [x] Al reabrir el presupuesto se muestra la modalidad guardada.
- [x] Se define valor por defecto para presupuestos existentes y nuevos (50/50).

## Archivos modificados

- `akuna_calc/presupuestos/models.py`
- `akuna_calc/presupuestos/forms.py`
- `akuna_calc/presupuestos/templates/presupuestos/detalle.html`
- `akuna_calc/presupuestos/tests.py`
- `akuna_calc/presupuestos/migrations/0006_presupuesto_modalidad_sena.py`

## Decisiones técnicas

- Se modeló como `CharField` con `choices` cerrados para evitar valores libres y mantener consistencia operativa.
- Se definió default `50_50` para asegurar compatibilidad con presupuestos históricos en migración.
- Se reutilizó el endpoint y formulario existente de configuración de obra para evitar nuevas rutas y mantener permisos/sesión sin cambios.

## Validación

- Tests del módulo ejecutados con settings de prueba SQLite:
  - `python manage.py test presupuestos --settings=akuna_calc.settings_test_sqlite`
  - Resultado: 32 tests OK.
