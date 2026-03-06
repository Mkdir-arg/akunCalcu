# FEAT-003 — Sistema de Fórmulas para Marcos

> Estado: Implementado
> Fecha: 2026-03-06
> REQ: REQ-004

## Descripción funcional

Al crear o editar un Marco, el formulario incluye una sección "Fórmulas de Perfiles" donde el administrador puede agregar múltiples filas. Cada fórmula define cuántos perfiles se necesitan, la fórmula de dimensión (ej: "Alto - 500"), el ángulo de corte y el código de perfil a usar. Al guardar, las fórmulas se persisten en la tabla `despiece_perfiles_marcos`.

## Criterios de aceptación cumplidos

- [x] CA-1: Campos Extrusora, Línea y Producto en el formulario de Marco
- [x] CA-2: Sección "Fórmulas de Perfiles" con botón "Agregar Fórmula"
- [x] CA-3: Cada fórmula tiene Cantidad / Variable / Operador / Valor / Ángulo / Perfil / botón Eliminar
- [x] CA-4: La fórmula se construye como texto "Alto - 500" al guardar
- [x] CA-5: Selector de Perfil carga lista completa desde nueva API `/pricing/api/perfiles-simple/`
- [x] CA-6: Al guardar, las fórmulas se persisten en `despiece_perfiles_marcos`
- [x] CA-7: Al editar, las fórmulas existentes se cargan correctamente en la tabla
- [x] CA-8: Al guardar en edición, se eliminan las anteriores y se insertan las nuevas
- [x] CA-9: Sin errores silenciosos — `messages.warning` en la vista y `.catch()` en el fetch

## Bugs corregidos

### Bug principal: fórmulas no se guardaban
**Causa raíz:** El JS asignaba índices incrementales sin resetear. Si el usuario agregaba y eliminaba filas, el POST podía contener `formula_cantidad_2` sin que existiera `formula_cantidad_0`. La condición Python `if 'formula_cantidad_0' in request.POST` fallaba y no se guardaba nada.

**Solución:** Listener en el evento `submit` del form que re-numera todos los inputs a índices consecutivos (0, 1, 2...) antes de enviar. Garantiza que siempre exista `formula_cantidad_0`.

### Bug secundario: selector de perfiles vacío
**Causa raíz:** La API `/pricing/api/pricing/perfiles/` usa DRF `APIView` con autenticación de sesión. Podía rechazar el fetch del browser por conflictos de autenticación/CSRF.

**Solución:** Nueva vista Django simple `api_get_perfiles` en `config_views.py` con `@login_required`, que retorna la lista de perfiles como `JsonResponse` sin DRF. URL: `/pricing/api/perfiles-simple/`.

### Bug de timing: fórmulas en modo edición
**Causa raíz:** Las fórmulas existentes se cargaban en un `setTimeout(500)` esperando que el fetch de perfiles terminara. Esto era frágil y podía fallar si la red era lenta.

**Solución:** Las fórmulas existentes se inyectan como datos estáticos desde Django en el template (`formulasIniciales`). Se cargan en el `.then()` del fetch de perfiles, garantizando que el selector ya tenga opciones antes de construir las filas.

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `akuna_calc/pricing/config_views.py` | Nueva vista `api_get_perfiles` al final del archivo |
| `akuna_calc/pricing/urls.py` | Nueva URL `api/perfiles-simple/` |
| `akuna_calc/pricing/templates/pricing/config/marco_form.html` | Reescrito: fix de índices, nueva API de perfiles, carga de fórmulas existentes sin setTimeout, JS movido a `{% block extra_js %}` |
| `akuna_calc/pricing/tests.py` | Creado: 6 tests de status code para las vistas afectadas |

## Decisiones técnicas

- Se creó una vista Django simple para perfiles en lugar de usar el endpoint DRF existente, para evitar problemas de autenticación y simplificar el flujo.
- La re-numeración de índices se hace en el cliente (JS) en el evento submit, sin cambiar la lógica del servidor.
- Los datos de fórmulas existentes se inyectan server-side como JSON en el template, eliminando la dependencia de timing.
