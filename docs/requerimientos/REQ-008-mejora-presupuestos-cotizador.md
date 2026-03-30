# REQ-008 — Mejora de Presupuestos: Paridad con Cotizador + UI

> **Estado**: Implementado — [FEAT-007](../features/FEAT-007-mejora-presupuestos-cotizador.md)
> **Fecha**: 2026-03-30
> **Complejidad**: Mediano
> **Derivara en**: FEAT-007

## User Story

Como vendedor, quiero que el cotizador embebido en presupuestos tenga las mismas funcionalidades que el cotizador principal (opcionales, desglose completo, mano de obra) y una UI mejorada, para poder armar presupuestos completos sin tener que ir al cotizador aparte.

## Criterios de Aceptacion

### Funcionalidad
- [ ] Se pueden agregar opcionales (mosquiteros, otros) al cotizar un item del presupuesto
- [ ] Los opcionales se envian al backend y se guardan en el resultado_json del item
- [ ] El resultado muestra mano de obra cuando aplica
- [ ] El resultado muestra el desglose expandible completo (perfiles, accesorios, vidrio, tratamiento, mano de obra, opcionales)
- [ ] El boton "Ver desglose" de cada item guardado funciona y muestra un modal con el detalle completo

### UI
- [ ] Lista de presupuestos mejorada con KPIs de resumen
- [ ] El cotizador en el modal tiene paridad visual con el cotizador principal
- [ ] Codigo del cotizador unificado (sin duplicacion entre item_form.html y detalle.html)
