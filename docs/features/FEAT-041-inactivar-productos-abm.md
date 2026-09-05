# FEAT-041 — Inactivar y reactivar productos desde el ABM

- **Estado:** Implementado
- **Fecha:** 2026-09-05
- **Requerimiento:** [REQ-051](../requerimientos/REQ-051-inactivar-productos-abm.md)
- **Apps:** `pricing`
- **Migración:** ninguna

## Qué hace

En `/pricing/config/productos/` cada producto activo tiene el botón **Inactivar** (con confirmación)
y cada inactivo el botón **Activar**. Un producto inactivo **no se ofrece en el cotizador** del
presupuesto, pero **sigue en el listado** con el badge "Inactivo", así se puede volver a activar sin
perder marcos, hojas ni aperturas admitidas. El filtro Activos / Inactivos de la tabla, que ya
existía, pasa a servir.

Los ítems de presupuesto ya guardados con un producto inactivo siguen abriéndose, dibujándose e
imprimiendo igual: la API por id no filtra por estado.

## Lo que ya existía y lo que cambió

| Antes | Ahora |
|---|---|
| Botón con tacho "Desactivar" → `bloqueado='Si'` | Mismo campo y misma vista, botón **Inactivar** con texto claro |
| El listado **ocultaba** los bloqueados: se vivía como un borrado sin vuelta | El listado muestra **todos**, con badge de estado |
| Sin forma de reactivar | Botón **Activar** → `bloqueado='No'` (vista nueva `producto_activate`) |
| El cotizador excluía `bloqueado='Si'` | Igual, ahora con un test que lo fija |

**Efecto en los datos existentes**: los productos que se habían "eliminado" con el tacho reaparecen
en el listado como Inactivos. Nada cambia de estado; es la misma marca que ya tenían.

## Cómo está armado

- `pricing/config_views.py`: `productos_config` deja de excluir `bloqueado='Si'`; `producto_delete`
  cambia el mensaje; nueva `producto_activate` (POST, `@login_required` + `is_staff`).
- `pricing/urls.py`: `config-producto-activate` → `config/productos/<pk>/activar/`.
- `pricing/templates/pricing/config/productos.html`: botón Inactivar (SweetAlert2, texto explica que
  se puede reactivar) o formulario Activar según el estado; `escapejs` en el nombre que va al JS.
- Los selectores de producto de Marcos y Hojas siguen usando `exclude(bloqueado='Si')`: no ofrecen
  inactivos.

## Decisiones

1. **Reutilizar `bloqueado`** en lugar de un campo `activo` nuevo: la tabla `productos` es legacy
   (`managed=False`, cada columna nueva exige `ALTER TABLE` a mano, ADR-018) y no hay borrado físico
   en ningún lado, así que "eliminado" e "inactivo" siempre fueron lo mismo. Un solo estado.
2. **Valor activo = `'No'`**, como usan el resto de las entidades legacy (`Extrusora` filtra
   `isnull | 'No'`).

## Verificación

- 6 tests nuevos (`ProductoActivarInactivarTest`, con mocks porque la tabla legacy no existe en la
  base de test): inactivar, activar, GET no cambia nada, sin login, listado con ambos estados y sus
  botones, la API del cotizador excluye inactivos.
- Suite `pricing` sin regresiones respecto del baseline. `makemigrations --check`: sin cambios.

## Pendiente

- Replicar el mismo patrón (listar inactivos + botón Activar) en Extrusoras, Líneas, Marcos, Hojas,
  Perfiles y Accesorios, que hoy también ocultan lo inactivo sin vuelta.
