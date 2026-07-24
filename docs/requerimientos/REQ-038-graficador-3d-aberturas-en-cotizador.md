# REQ-038 — Graficador 3D de aberturas en el cotizador de presupuestos

- **Estado:** Implementado
- **Fecha:** 2026-07-24
- **Derivó en:** [FEAT-030](../features/FEAT-030-graficador-3d-aberturas-cotizador.md)

## Contexto

El cotizador de `/presupuestos/` permite agregar ítems (aberturas) configurando extrusora, línea, producto, marco, hoja, vidrio, tratamiento, medidas y opcionales, y calcula el precio contra `/pricing/api/pricing/calculate/`. Hoy el vendedor arma la abertura "a ciegas": no ve cómo queda. Los cotizadores comerciales de aberturas muestran un diseño de la abertura según los parámetros.

Se validó un **prototipo de visor 3D** (Three.js) que dibuja aberturas paramétricas (ventana corrediza, batiente, oscilobatiente, proyectante, paño fijo, puerta batiente y corrediza), con apertura animada, mosquitero, travesaños, persiana, vidrio DVH/tintado, acotaciones y captura PNG. Prototipo en `scratchpad/visor-aberturas-3d.html`.

El análisis técnico previo confirmó que el `snapshot_item` que ya persiste `build_item_snapshot` (`presupuestos/pdf_descriptions.py`) contiene todos los parámetros de entrada que el 3D necesita, **salvo la tipología**, que hay que derivar de `producto.descripcion` + `producto.cantidad_hojas`.

## User Story

```
Como vendedor
quiero ver un diseño 3D de la abertura al calcular cada ítem del presupuesto
para confirmar visualmente que la configuración (tipo, medidas, hojas, opcionales)
es correcta antes de guardarla y mostrársela al cliente.
```

## Criterios de aceptación

- [ ] Al calcular un ítem en el modal de agregar/editar de `/presupuestos/`, se muestra un visor 3D al lado del resultado del precio.
- [ ] El 3D se genera interpretando los parámetros del ítem: **tipología** (derivada del producto), ancho, alto, cantidad de hojas, opcionales (mosquitero / premarco) y vidrio.
- [ ] La **tipología** se clasifica automáticamente desde `producto.descripcion` + `producto.cantidad_hojas` a una de: corrediza, batiente, oscilobatiente, proyectante, paño fijo, puerta batiente, puerta corrediza.
- [ ] Si la tipología no se puede clasificar con confianza, cae a un **default razonable** (paño fijo) sin romper el visor ni el cálculo.
- [ ] El visor permite **rotar con el mouse** y se **actualiza** cuando cambian los parámetros / al recalcular.
- [ ] El 3D se carga de forma **lazy** (Three.js se descarga solo al abrir el modal), sin afectar el tiempo de carga de la página de presupuesto.
- [ ] **No se agregan dependencias con build**: Three.js se sirve como módulo estático autocontenido; el modal (React por Babel, sin build) lo invoca imperativamente.
- [ ] No se rompe el flujo actual de agregar / editar / eliminar ítems ni el cálculo de precio (PVC, terciarizado y aluminio siguen funcionando).

## Alcance

**Incluye:** visor 3D en vivo dentro del modal de ítem (aluminio), clasificador de tipología, mapeo de parámetros → visor.

**Fuera de alcance (fase 2, futura):** imagen PNG por ítem en la lista y en el PDF, color de perfil real, mano de apertura (izq/der) como dato.

## Complejidad estimada

**Grande** — combina frontend 3D (Three.js), clasificador de tipología en el backend, e integración con el modal React existente sin introducir build.

## Relación con el backlog

Nueva user story **US-038**. Se apoya sobre el módulo de Presupuestos (REQ-006 / FEAT-005) y el cotizador de `pricing`. No reemplaza ningún ítem existente del backlog.
