# REQ-036 — Eliminar el módulo de despiece y transformar Pedidos de Fábrica

**Estado:** Implementado
**Fecha:** 2026-07-07
**Origen:** Decisión del usuario tras análisis de arquitectura. **Prerrequisito de [REQ-035](./REQ-035-ordenes-de-fabricacion-en-pedidos.md)** (Órdenes de Fabricación).

## User Story

Como administrador del sistema, quiero eliminar los módulos obsoletos de despiece (Calcular, Configurar Plantillas, Historial y los ítems de despiece dentro de los pedidos) para sacar código muerto del sistema y dejar Pedidos de Fábrica como contenedor exclusivo de las futuras Órdenes de Fabricación.

## Contexto

La app `plantillas` contiene dos mundos independientes:

1. **Despiece** (obsoleto): plantillas de cálculo de medidas de corte con su motor de fórmulas propio (`formula_engine`, Shunting Yard con MIN/MAX/IF), pantalla Calcular, Historial de ejecuciones, y los ítems/filas de despiece dentro de los pedidos de fábrica. Corresponde al grupo de menú "Despiece" (`despiece.*` en `usuarios/access_control.py`).
2. **Opcionales de Fábrica** (vigente): `OpcionalFabrica`/`FormulaOpcional`/`AccesorioOpcional`/`RelacionProductoOpcional` — **usados por el cotizador de `pricing`** (`pricing/services/calculator.py`, `catalog_views.py`, `config_views.py` y `presupuestos/pdf_descriptions.py`) para calcular mosquiteros, premarcos, etc. en los presupuestos de aluminio. Corresponde al permiso `fabrica.opcionales`.

Este requerimiento elimina el mundo 1 completo y conserva el 2 intacto.

## Alcance — SE ELIMINA

- **Modelos + tablas (datos incluidos):** `ProductoPlantilla`, `CampoPlantilla`, `CalculoEjecucion`, `PedidoFabricaItem`, `PedidoFabricaFila`. Migración de borrado (atención al orden: `PedidoFabricaItem` tiene FK PROTECT a `ProductoPlantilla`).
- **Views:** `plantilla_list/create/edit/toggle`, `plantilla_campos`, `campo_create/edit/delete`, `plantilla_probar`, `calcular_index/ejecutar/ajax`, `historial_calculos`, `pedido_add_item`, `pedido_item_calcular/add_fila/duplicate/delete`, `pedido_fila_delete`.
- **URLs:** todas las anteriores. La raíz `/plantillas/` (hoy listado de plantillas) pasa a **redirigir al listado de pedidos**.
- **Servicios y utilitarios:** `plantillas/services/formula_engine.py`, `plantillas/forms.py` (PlantillaForm/CampoForm), management command `seed_plantillas`.
- **Templates:** `plantilla_list/form/campos/probar`, `campo_form`, `calcular_index/ejecutar`, `historial_calculos` + limpieza de `pedido_detail.html` (se quita todo el bloque de ítems/filas de despiece; queda la cabecera del pedido, lista para las órdenes del REQ-035).
- **Admin:** registros de los modelos eliminados (queda `PedidoFabrica` sin inline de ítems).
- **Permisos (registro `access_control.py`):** `despiece.calcular`, `despiece.plantillas`, `despiece.historial` (el menú se limpia solo al quitarlos). `despiece.pedidos` se conserva, con sus rutas reducidas a las de pedidos.
- **Tests** del despiece (formula_engine, plantillas, ítems de pedidos).

## Alcance — SE CONSERVA (intocable, confirmado por el usuario)

- **`PedidoFabrica`** (cabecera): listado, alta manual y detalle, con la FK `presupuesto` de FEAT-019 y la generación automática al confirmar presupuestos.
- **Todo el grupo "Fábrica" del menú:** Opcionales (en `plantillas`), Extrusoras, Líneas, Productos, Marcos, Perfiles, Hojas, Interior, Accesorios, Vidrios, Tratamientos (ABM del cotizador en `pricing`).
- El cotizador de `pricing` y el módulo de presupuestos completos.

## Criterios de Aceptación

- [ ] El menú ya no muestra "Calcular", "Configurar Plantillas" ni "Historial"; "Pedidos de Fábrica" sigue visible y funcional.
- [ ] `/plantillas/` redirige al listado de pedidos de fábrica.
- [ ] El detalle del pedido no muestra nada de despiece: pantalla limpia con los datos de cabecera (y el link al presupuesto de origen si existe).
- [ ] El grupo Fábrica completo sigue funcionando igual: opcionales, ABMs, cotizador y presupuestos (validado con las suites de `pricing`, `presupuestos` y `plantillas`).
- [ ] Confirmar un presupuesto (FEAT-019) sigue creando venta + pedido sin errores.
- [ ] Existe la migración de borrado; `manage.py check` y los tests pasan sin referencias rotas.
- [ ] Los roles que tengan guardados permisos `despiece.calcular/plantillas/historial` no rompen nada (strings huérfanos ignorados).

## Decisiones (2026-07-07)

| Punto | Decisión |
|---|---|
| Datos del despiece en producción | **Se borran definitivamente** (plantillas configuradas, historial de cálculos, ítems/filas de pedidos). Confirmado por el usuario. |
| Grupo Fábrica (Opcionales + ABMs del cotizador) | **No se toca para nada.** |
| Nombre de la app | Se mantiene `plantillas` (renombrarla implica migraciones invasivas sin beneficio funcional; queda como nombre técnico interno). |
| Orden de trabajo | REQ-036 primero → después REQ-035 (las órdenes se construyen sobre el pedido ya limpio). |

## Riesgos identificados

- Borrado de datos irreversible en producción (confirmado).
- Una migración más en la cola pendiente de Docker/Railway — aplicar y verificar con el resto.
- Verificar tras el borrado que ningún template/JS residual referencie URLs eliminadas (el system check de Django no cubre `{% url %}` en templates no renderizados por tests).

## Estimación

Mediano.

## Derivó en

[FEAT-020](../features/FEAT-020-eliminar-modulo-despiece.md)
