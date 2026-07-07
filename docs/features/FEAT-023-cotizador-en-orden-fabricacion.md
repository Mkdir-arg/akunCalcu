# FEAT-023 — Cotizador para rellenar la abertura en la Orden de Fabricación

**Estado:** Implementado
**Fecha:** 2026-07-07
**Relacionado:** [FEAT-021](./FEAT-021-ordenes-de-fabricacion-etapa1.md) (edición de la orden). Pedido directo del usuario: "llevar el pop up de cotización a órdenes".

## Descripción funcional

En la pantalla de edición de una orden de fabricación (`/plantillas/ordenes/<id>/editar/`) se agregó el botón **"Cargar desde cotizador"** dentro de la sección "Detalle de la abertura". Abre un modal con los mismos selectores en cascada del cotizador (Extrusora → Línea → Producto → Marco → Modelo de hoja → Vidrio, y Color/Terminación), alimentados por las APIs de catálogo de `pricing`.

Al confirmar con "Usar selección", se completan automáticamente los campos de la orden:

| Campo de la orden | Origen |
|---|---|
| Tipo de abertura | Producto (descripción) |
| Línea | Línea (nombre) |
| Color | Tratamiento / Terminación (descripción) |
| Tipo de vidrio | Vidrio (descripción) |
| Modelo de hoja | Hoja (descripción) |
| Cantidad de hojas | Hoja (campo `cantidad`) |

**No calcula ni guarda precios** — la orden de fabricación es la planilla de fábrica, no lleva monto. El resto de los campos (SI/NO, medidas, nota) se siguen cargando a mano. Los valores cargados quedan como texto editable, así que se pueden ajustar antes de guardar.

## Decisiones técnicas

- **No se reutilizó el componente React del cotizador de presupuestos** (está acoplado a `pricing` y a la creación de `ItemPresupuesto` con cálculo de precio). En su lugar se hizo un modal liviano en **JS vanilla** que consume los endpoints de catálogo existentes (`/pricing/api/pricing/{extrusoras,lineas,productos,marcos,hojas,vidrios,tratamientos}/`) — sin librerías nuevas, sin Babel/React, sin llamadas de cálculo.
- Los `<select>` del modal llevan clase `no-select2` (native) y bindean `change` con `addEventListener`: al ser nativos no dependen de Select2, evitando el problema de binding documentado en [[select2-global-change-binding]].
- El relleno copia el texto de la opción elegida a los inputs de la orden por su id Django (`id_tipo_abertura`, `id_linea`, `id_color`, `id_tipo_vidrio`, `id_modelo_hoja`, `id_cantidad_hojas`).

## Archivos modificados

- `akuna_calc/plantillas/templates/plantillas/orden_form.html` — botón, modal y JS del cotizador.
- `akuna_calc/plantillas/tests.py` — test de render del botón/modal.

Sin cambios de modelo, migraciones ni backend (solo template + JS que consume APIs ya existentes).

## Validación

- `python manage.py test plantillas --settings=akuna_calc.settings_test_sqlite` → **22 OK**.
- El flujo real de datos usa tablas legacy de `pricing` (no disponibles en SQLite de test), por lo que la carga en cascada se verifica en el entorno con MySQL. El test cubre que el botón, el modal y las URLs de API estén presentes en la página.
