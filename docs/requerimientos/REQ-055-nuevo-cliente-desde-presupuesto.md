# REQ-055 — Alta rápida de cliente desde el formulario de Presupuesto

- **Estado:** Aprobado
- **Fecha:** 2026-10-20
- **Complejidad:** Pequeño / Mediano
- **Origen:** RF-024 (prioridad Alta)
- **Depende de:** [REQ-054](./REQ-054-id-cliente-y-provincia.md) (provincia y `etiqueta_selector` en el modal)
- **Plan:** [Plan RF Akun — octubre 2026](../team/plan-rf-akun-2026-10.md) · Sprint 1
- **Apps afectadas:** `comercial`, `presupuestos`, `usuarios`

## User Story

Como **vendedor que arma un presupuesto** quiero **buscar al cliente o darlo de alta sin salir del
formulario**, igual que en Ventas, para **no perder lo que estoy cargando**.

## Decisiones tomadas

- **"Buscar Cliente" ya existe** en Presupuestos: es el select con buscador (REQ-026). Con REQ-054 además busca por ID. No se agrega otro botón.
- **"Nuevo Cliente"** abre el mismo modal que Ventas. El modal se **extrae a una pieza compartida** (no se copia): así un solo cambio arregla los dos módulos y no se duplican los bugs actuales.
- **Ruta propia para el alta rápida.** Hoy `comercial:cliente_create` exige `comercial.clientes`: un vendedor que solo tiene Presupuestos recibe 403 desde el modal (y lo mismo le pasa en Ventas a quien no tiene Clientes). Se crea `comercial:cliente_create_rapido`, habilitada para Clientes, Ventas y Presupuestos.

## Criterios de Aceptación

- [ ] El formulario de presupuesto (crear y editar) tiene un botón "+" junto al select de cliente, con el mismo diseño que en Ventas
- [ ] El botón abre el modal de alta; al guardar, el cliente queda creado, **seleccionado en el select** y el modal se cierra con un aviso de éxito
- [ ] Los errores de validación (email duplicado, campos obligatorios, error general) se muestran en el modal sin perder lo cargado en el presupuesto
- [ ] Un vendedor con acceso solo a Presupuestos puede dar de alta el cliente; un usuario sin acceso a ninguno de los tres módulos recibe 403
- [ ] El modal de Ventas sigue funcionando igual, ahora con el aviso de éxito (hoy falla: llama a `showNotification`, que no existe) y mostrando todos los errores
- [ ] El flujo "Crear cliente con estos datos" desde una solicitud sigue funcionando como hoy

## Diseño técnico

**Archivos nuevos**
- `comercial/templates/comercial/clientes/_modal_nuevo_cliente.html`: campos desde `ClienteForm` (incluye provincia), un lugar de error por campo (`data-error-for="<campo>"`) más `__all__`, csrf propio; atributos `data-select2-dropdown-parent`, `data-url`, `data-target="#id_cliente"`
- `comercial/templatetags/__init__.py` + `clientes_tags.py`: inclusion tag que arma `ClienteForm(auto_id='nc_%s')`, así no hay que tocar las vistas que lo usan
- `static/js/cliente-modal.js` (con `?v=1`): `window.AkunClienteModal.open/close`, alias `openClienteModal()` para no tocar el `onclick` existente. Al guardar: `new Option(etiqueta, id, true, true)`, `select.add(option)` y **`$(select).trigger('change')` con jQuery** (no `addEventListener`, ver FIX-014). Revisa `response.ok` antes de leer `errors` (el middleware responde 403 en JSON a XHR). Toast con `Swal.fire`

**Archivos modificados**
- `comercial/views.py`: vista nueva `cliente_create_rapido` (`@login_required`, `@require_POST`, siempre JSON, reutiliza `ClienteForm`; devuelve `{success, cliente:{id, nombre, codigo, etiqueta}}` o `{success:false, errors}` con 400). La rama AJAX de `cliente_create` (~l.847-868) se conserva por compatibilidad
- `comercial/urls.py`: `clientes/nuevo/rapido/`, name `cliente_create_rapido`
- `usuarios/access_control.py`: registrar la ruta con `['comercial.clientes', 'comercial.ventas', 'presupuestos.view']`
- `comercial/templates/comercial/ventas/form.html`: reemplazar el modal inline (~l.278-364) y su JS (~l.484-554) por el include y el .js
- `presupuestos/templates/presupuestos/form.html`: envolver `{{ form.cliente }}` (~l.37-38) en `flex gap-2` con el botón; incluir el modal **fuera** del `<form method="post">` (formularios anidados no son válidos), después de ~l.70

## Impacto

- `PresupuestoForm` y `VentaForm` no filtran el cliente por vendedor: el recién creado pasa la validación, y si el form se re-renderiza con errores ya aparece en la lista
- Se descarta registrar `cliente_create` para más módulos: resaltaría Ventas/Presupuestos en el menú al estar en /clientes/nuevo/ y al terminar redirige a un listado que el vendedor no puede ver
- Link "Crear cliente con estos datos" (`presupuestos/form.html` ~l.27): se deja como está. **Fuera de alcance, anotado:** si el vendedor no tiene `comercial.clientes`, ese link hoy le da "No tiene permisos"; mejora futura = abrir el modal precargado

## Tests

- Usuario con solo `presupuestos.view` → POST XHR a `cliente_create_rapido` → 200 con `codigo` y `etiqueta`, cliente creado
- Usuario sin permisos → 403 JSON
- Email duplicado → 400 con `errors.email`
- GET de crear presupuesto y de crear venta contienen `id="clienteModal"`
- Con `?solicitud=` sigue apareciendo "Crear cliente con estos datos"
- No deben romperse `ClienteCreatePrefillTest` ni `ClienteEmailUnicoTest`

**Migración:** No.
