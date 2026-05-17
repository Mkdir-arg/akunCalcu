# FEAT-010 — Buscador de accesorios en configurador de hojas

> **Requerimiento**: [REQ-025](../requerimientos/REQ-025-buscador-accesorios-config-hojas.md)
> **Fecha**: 2026-05-17
> **Apps afectadas**: `pricing`

## Descripción funcional

Se mejoró la pantalla de edición de hojas para que el campo **Accesorio** dentro del bloque de accesorios funcione como buscador en lugar de depender de un selector largo sin filtro.

- El usuario ahora puede escribir dentro del campo de selección para encontrar accesorios por código o descripción.
- La mejora aplica tanto a filas de accesorios ya cargadas como a filas nuevas agregadas dinámicamente desde la misma pantalla.
- El flujo de autosave y el guardado final siguen enviando el mismo valor de accesorio que antes, por lo que no cambió la persistencia.

## Criterios de aceptación cumplidos

- [x] En `/pricing/config/hojas/<id>/editar/`, el campo **Accesorio** dentro de la sección de accesorios permite buscar escribiendo texto.
- [x] La búsqueda filtra los accesorios disponibles por código y/o descripción para agilizar la selección.
- [x] El usuario puede seguir seleccionando un accesorio existente sin cambiar el flujo actual de guardado.
- [x] La mejora aplica tanto a filas existentes como a filas nuevas agregadas dinámicamente en la pantalla.
- [x] No se modifica la lógica de guardado de accesorios de la hoja; solo mejora la interacción de selección.
- [x] La interfaz mantiene el estilo y componentes ya usados por el sistema.
- [x] Existe al menos un test que cubre la renderización del comportamiento esperado de la vista afectada.

## Archivos modificados

- `pricing/templates/pricing/config/hoja_form.html` — inicialización manual de Select2 para los selects dinámicos de accesorios.
- `pricing/tests.py` — test de renderizado del template para validar el buscador y su inicialización.
- `docs/team/design-system.md` — aclaración del patrón para selects dinámicos creados por JavaScript.

## Decisiones técnicas

- Se reutilizó Select2 ya incluido globalmente en `core/base.html`; no se agregaron librerías nuevas.
- La inicialización del buscador se hace manualmente solo para los selects dinámicos de accesorios, porque el bootstrap global de Select2 corre una sola vez al cargar la página.
- No hubo cambios de modelo ni migraciones porque `DespieceAccesoriosHoja` ya persiste el accesorio como texto y el valor enviado sigue siendo el código existente.

## Validación

- `python manage.py test pricing.tests.HojaFormTemplateTest --settings=akuna_calc.settings_test_sqlite --verbosity 2`