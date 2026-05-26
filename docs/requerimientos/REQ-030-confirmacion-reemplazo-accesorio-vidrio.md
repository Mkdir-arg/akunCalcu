# REQ-030 — Confirmación modal antes de reemplazar accesorio o vidrio

**Estado:** Implementado — [FEAT-014](../features/FEAT-014-confirmacion-reemplazo-accesorio-hoja.md)  
**Fecha:** 2026-05-26  
**Prioridad:** ALTA  
**Tipo:** Bug + UX  
**Origen:** RF-003 — Reportado por usuario en configurador de hojas

## User Story

Como configurador de hojas, quiero recibir una confirmación modal antes de reemplazar un accesorio o vidrio que ya tengo cargado, para evitar cambios involuntarios que se guarden automáticamente y generen errores en la configuración.

## Criterios de Aceptación

- [ ] Cuando se cambia el valor de un selector de accesorio (ya cargado antes) en el formulario de edición de hoja, aparece modal SweetAlert2.
- [ ] La modal pregunta: "¿Deseas reemplazar este accesorio?" con detalles del accesorio anterior y el nuevo.
- [ ] Botones: "Sí, reemplazar" (rojo), "Cancelar" (gris).
- [ ] Si confirma: guarda automáticamente el cambio (flujo actual).
- [ ] Si cancela: revierte el selector al valor anterior, sin guardar cambio.
- [ ] El mismo comportamiento aplica a los selectores de vidrio.
- [ ] La modal NO aparece si el campo estaba vacío (primera carga, caso trivial).
- [ ] El check se dispara por cambio de `<select>`, no por blur o submit.

## Ubicación afectada

- URL: `https://web-production-3be54.up.railway.app/pricing/config/hojas/<id>/editar/`
- Template: `akuna_calc/pricing/templates/pricing/config/hoja_form.html`
- Lógica: Select2 + evento de cambio en JavaScript

## Fuera de alcance

- Confirmación en otros selectores del formulario (solo accesorios y vidrios).
- Confirmar cada línea agregada dinámicamente si ya tiene accesorio (solo campos raíz).

## Estimación

Pequeño (2-3 horas).

## Riesgos identificados

- Select2 puede disparar eventos múltiples al cambiar → usar flag/debounce para evitar modales duplicadas.
- Si el usuario cierra la modal accidentalmente (clic fuera), la UI debe quedar consistente.

## Derivó en

—
