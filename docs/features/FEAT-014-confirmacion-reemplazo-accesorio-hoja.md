# FEAT-014 — Confirmación antes de reemplazar accesorio en hoja configurator

**Estado:** Implementado  
**Fecha:** 2026-05-26  
**Requerimiento:** [REQ-030](../requerimientos/REQ-030-confirmacion-reemplazo-accesorio-vidrio.md)  
**Sprint:** Fuera de sprint activo

---

## Descripción funcional

Antes de que el autosave reemplace un accesorio ya cargado en la tabla de accesorios de la hoja configurator, se muestra un modal SweetAlert2 pidiendo confirmación al usuario.

Si el campo estaba vacío (primera carga), el guardado ocurre sin interrupción.

---

## Criterios de aceptación cumplidos

- [x] Modal SweetAlert2 aparece al cambiar un selector de accesorio que ya tenía valor
- [x] El mensaje muestra el nombre del accesorio anterior y el nuevo
- [x] Botón "Sí, reemplazar" (rojo) y "Cancelar" (gris)
- [x] Al confirmar: se guarda normalmente con el autosave existente
- [x] Al cancelar: el selector vuelve al valor anterior sin guardar
- [x] No hay modal si el selector estaba vacío (primera selección)
- [x] El checkbox "Obligatorio" sigue guardando sin modal
- [x] No se afectan las fórmulas de perfiles ni el formulario de vidrios

---

## Archivos modificados

| Archivo | Cambio |
|---|---|
| `akuna_calc/pricing/templates/pricing/config/hoja_form.html` | Agregado `data-previous-value` al `<select>` de accesorios; lógica de confirmación SweetAlert2 en el listener `change` de `accesoriosBody` |

---

## Decisiones técnicas

- Se usa `data-previous-value` en el DOM del select para rastrear el último valor confirmado sin estado JS adicional.
- Para revertir Select2 sin re-disparar el handler nativo, se usa `.trigger('change.select2')` (notifica solo la UI de Select2, no el evento `change` del DOM).
- Cambio JS-only: no requiere migración, ni cambio de modelo, ni endpoint nuevo.
