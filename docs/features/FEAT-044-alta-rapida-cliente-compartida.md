# FEAT-044 — Alta rápida de cliente desde Presupuestos (modal compartido con Ventas)

- **Estado:** Implementado
- **Fecha:** 2026-10-20
- **Requerimiento:** [REQ-055](../requerimientos/REQ-055-nuevo-cliente-desde-presupuesto.md) (RF-024)
- **Sprint:** Sprint 1 — plan RF Akun
- **Apps:** `comercial`, `presupuestos`, `usuarios`
- **Migración:** ninguna

## Qué hace

El formulario de presupuesto (crear y editar) tiene un botón **"+"** junto al select de cliente que
abre el mismo modal de alta que Ventas. Al guardar, el cliente queda creado, **seleccionado** en el
select ("Nombre · C-00123") y aparece un aviso de éxito. Los errores de validación se muestran campo
por campo en el modal sin perder lo cargado en el presupuesto. "Buscar cliente" es el select con
buscador que ya existía.

## Decisiones técnicas

- **Modal extraído, no copiado:** `clientes/_modal_nuevo_cliente.html` + inclusion tag `{% modal_nuevo_cliente '#id_cliente' %}` (`comercial/templatetags/clientes_tags.py`, arma `ClienteForm(auto_id='nc_%s')`) + `static/js/cliente-modal.js`. Ventas y Presupuestos usan la misma pieza; el modal incluye Provincia
- **Ruta propia `comercial:cliente_create_rapido`** (`clientes/nuevo/rapido/`, POST, siempre JSON), habilitada para `comercial.clientes`, `comercial.ventas` y `presupuestos.view`. Antes el modal posteaba a `cliente_create`, que exige Clientes: un vendedor sin ese acceso recibía 403. La rama AJAX vieja de `cliente_create` se conserva
- El JS agrega la opción con `new Option(...)` y dispara `change` **con jQuery** (Select2 global, ver FIX-014). El modal declara `data-select2-dropdown-parent` para que el select de provincia se despliegue dentro
- Arregla dos fallas del modal viejo de Ventas: el aviso de éxito llamaba a `showNotification`, que no existe, y la limpieza de errores no encontraba nada. El aviso usa `titleText` de SweetAlert2 (no interpreta HTML del nombre cargado)
- El link "Crear cliente con estos datos" desde una solicitud no cambió

## Criterios cumplidos

- [x] Botón "+" en crear y editar presupuesto
- [x] Crea, selecciona, cierra y avisa
- [x] Errores en el modal sin perder lo cargado
- [x] Vendedor con solo Presupuestos puede crear; sin acceso → 403
- [x] Modal de Ventas con aviso de éxito y todos los errores
- [x] Flujo desde solicitud intacto

**Sin probar en navegador** antes del deploy (no había Docker ni Playwright en el entorno): el JS se
revisó línea por línea y el render del tag se verificó; queda la prueba manual de ambos modales en prod.

## Archivos

- Nuevos: `comercial/templatetags/{__init__,clientes_tags}.py`, `comercial/templates/comercial/clientes/_modal_nuevo_cliente.html`, `static/js/cliente-modal.js`
- `comercial/views.py` (`cliente_create_rapido`), `comercial/urls.py`, `usuarios/access_control.py`
- `comercial/templates/comercial/ventas/form.html`, `presupuestos/templates/presupuestos/form.html`
- `comercial/tests.py` → `ClienteCreateRapidoTest`; `presupuestos/tests.py` (`CrearPresupuestoDesdeSolicitudTest`)
