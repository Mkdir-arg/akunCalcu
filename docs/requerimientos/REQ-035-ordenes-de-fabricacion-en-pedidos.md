# REQ-035 — Órdenes de Fabricación dentro del pedido de fábrica

**Estado:** Implementado (Etapa 1 — [FEAT-021](../features/FEAT-021-ordenes-de-fabricacion-etapa1.md); Etapa 2 PDF — [FEAT-022](../features/FEAT-022-orden-fabricacion-pdf.md))
**Fecha:** 2026-07-07
**Origen:** Pedido directo del usuario, con maqueta visual de la planilla "ORDEN DE FABRICACIÓN" (digitalización de la planilla papel actual de fábrica, heredada con datos de La Greca Home). Continuación natural de [FEAT-019](../features/FEAT-019-confirmacion-presupuesto-genera-venta-y-pedido.md).

## User Story

Como responsable de fábrica, quiero que cada pedido de fábrica contenga una orden de fabricación por cada ítem del presupuesto confirmado, poder editar el detalle de cada orden e imprimirla como PDF A4 con el diseño corporativo de Akun, para reemplazar la planilla papel actual y que fábrica trabaje con datos que nacen del presupuesto sin recargarlos a mano.

## Contexto

- Con FEAT-019, al confirmar un presupuesto se crea automáticamente el pedido de fábrica, pero como **cabecera vacía**. Este requerimiento define su contenido.
- La "orden de fabricación" hoy es una **planilla papel**; no existe en AkunCalcu. Aunque la especificación original habla de "rediseño visual manteniendo los campos de la base de datos", en este sistema es un **módulo nuevo**: modelo + generación + pantalla de edición + PDF.
- El módulo de despiece existente dentro del pedido (`PedidoFabricaItem` + plantillas de despiece) **se elimina antes** vía [REQ-036](./REQ-036-eliminar-modulo-despiece.md) (decisión del usuario, 2026-07-07): el detalle del pedido queda dedicado exclusivamente a las órdenes de fabricación.

Flujo completo resultante:

```
Presupuesto (N ítems) ──confirmar + seña──► Venta (comercial)
                                        └─► Pedido de fábrica (plantillas)
                                              └─► N Órdenes de Fabricación (una por ítem)
                                                    → editar detalle → imprimir PDF A4
```

## Criterios de Aceptación

**Generación y listado:**
- [ ] Al confirmar un presupuesto (flujo FEAT-019) se crea automáticamente una orden de fabricación por cada ítem, precargada con los datos disponibles.
- [ ] Dentro del detalle del pedido (`/plantillas/pedidos/<id>/`) se muestra la tabla de órdenes del pedido con acciones: ver/editar y descargar PDF.
- [ ] Se pueden agregar órdenes manualmente dentro de cualquier pedido (incluye pedidos creados a mano, sin presupuesto).
- [ ] Cada orden tiene N° correlativo propio (formato `0001`), fecha, y fecha comprometida.
- [ ] Requiere REQ-036 aplicado: el detalle del pedido muestra las órdenes como contenido único (el despiece fue eliminado).

**Edición de la orden (campos de la planilla):**
- [ ] Datos iniciales: Atendido por, Medición realizada por.
- [ ] Datos del cliente: Apellido y Nombre / Razón Social, Domicilio, Piso, Depto., Localidad, Mail, Teléfono.
- [ ] Detalle de la abertura: Tipo de abertura, Línea, Color.
- [ ] Sección Detalle: Mosquitero (y modelo), Travesaño, Tipo de Marco, Marco Desarmado, Umbral Transitable, Premarco, Guía para Persiana (y tipo de guía), Tapacinta, Lado, Modelo de Hoja, Travesaño divisor (y altura), Cantidad de hojas, Tipo de Vidrio, Contramarco (y modelo), Tipo de Trabajo, Altura.
- [ ] Campo nuevo **Estructura** (texto libre).
- [ ] Panel de observaciones (Nota) multilínea.
- [ ] Detalle de Medidas: tabla editable con columnas Item, Cantidad, Medida, Observaciones, Piso/Depto. — con alta dinámica de filas.

**PDF (una hoja A4 por orden):**
- [ ] Identidad visual Akun: azul corporativo `#145ea7`, negro `#1d1d1b`, fondo blanco, logo oficial arriba a la izquierda, títulos de sección con fondo azul, bordes finos, tipografía moderna (Roboto/Open Sans/Arial), espacios uniformes.
- [ ] Encabezado: logo, título "ORDEN DE FABRICACIÓN", N° Orden, Fecha, Fecha comprometida.
- [ ] Croquis: área ~35% de la hoja con cuadrícula gris clara, indicadores Interior / Exterior / flecha "Arriba", espacio libre **para dibujar a mano sobre el papel impreso**.
- [ ] Pie: solo logo/nombre Akun Aberturas + datos de contacto (dirección, teléfonos, sitio web) leídos desde la **configuración general del sistema** (`ConfiguracionGeneral`), sin ningún dato de La Greca Home ni datos hardcodeados.
- [ ] Cajas de firmas Preparó / Revisó / Producción (vacías, se firman en papel).
- [ ] Impresión A4 fiel a la maqueta (fuentes y distribución estables al imprimir); compatible con exportar a PDF.

## Decisiones de negocio (definidas con el usuario, 2026-07-07)

| Punto | Decisión |
|---|---|
| Generación de órdenes | Automática al confirmar (una por ítem, precargada) **+** alta manual dentro del pedido |
| Croquis | Área cuadriculada vacía para dibujar a mano en el papel impreso (sin editor digital) |
| Despiece existente | ~~Convive con las órdenes~~ → **Actualizado 2026-07-07: se elimina antes (REQ-036)**; el detalle del pedido queda solo para órdenes |

## Precarga automática (desde el presupuesto / ítem)

| Se precarga | Se completa a mano |
|---|---|
| N° orden, fecha | Atendido por / Medición realizada por (editables; puede sugerirse el usuario) |
| Cliente: nombre/razón social, domicilio, localidad, mail, teléfono | Piso y Depto. (no existen como campos del Cliente) |
| Tipo de abertura, Línea, Color y Tipo de vidrio (del snapshot del cotizador del ítem) | Todo el bloque "Detalle" (mosquitero, marco, premarco, hoja, contramarco, etc.) |
| Fecha comprometida (desde `plazo_entrega_dias` del presupuesto, si está cargado) | **Estructura** y Nota |
| 1 fila de medidas: cantidad + "ancho x alto" del ítem | Filas de medidas adicionales |

⚠️ Los ítems **PVC** no pasan por el cotizador de despiece: precargan solo cliente, descripción y medidas/cantidad; línea, color y vidrio quedan para completar.

## Diseño técnico preliminar

- Modelo nuevo `OrdenFabricacion` en `plantillas`: FK a `PedidoFabrica` (related_name `ordenes`), FK opcional a `presupuestos.ItemPresupuesto` (trazabilidad, SET_NULL), numeración correlativa, ~25 campos del formulario + `estructura`. Modelo hijo `MedidaOrdenFabricacion` para la tabla de medidas. Migración nueva.
- Generación automática: extender `_procesar_confirmacion()` (FEAT-019), que ya tiene presupuesto y pedido en la misma transacción.
- Views/URLs nuevas en `plantillas`: editar orden, alta manual, PDF, manejo dinámico de filas de medidas.
- PDF: template HTML A4 con `@media print` (patrón ADR-006, sin librerías nuevas); croquis con cuadrícula por CSS; logo existente (`AKUN-LOGO.png`).
- Configuración: claves nuevas en `ConfiguracionGeneral` (dirección, teléfonos, web) + data migration con los valores actuales; el PDF las lee en cada render.

## Fuera de alcance

- Editor de dibujo digital para el croquis (el dibujo se hace a lápiz sobre la hoja impresa).
- Workflow digital de firmas Preparó/Revisó/Producción (quedan como cajas en papel).
- La eliminación del módulo de despiece se hace en REQ-036 (prerrequisito), no acá.
- Estados de producción por orden (se puede proponer como requerimiento futuro).

## Estimación

**Grande.** Partición sugerida en dos etapas si se quiere entregar antes:
1. Modelo + generación automática/manual + tabla y pantalla de edición de órdenes.
2. PDF con el diseño corporativo + claves de contacto en configuración.

## Riesgos identificados

- La fidelidad "exactamente igual a la maqueta" en A4 exige iteración fina de CSS de impresión (parte más artesanal del trabajo).
- Ítems PVC con precarga parcial (dicho arriba).
- Piso/Depto. no existen en el modelo `Cliente`: nacen vacíos en la orden. Si se quieren en el cliente, es otro requerimiento.
- Pedidos/órdenes generados antes de esta feature no se backfillean (los pedidos existentes quedan sin órdenes; se pueden cargar a mano).

## Maqueta de referencia

Planilla "ORDEN DE FABRICACIÓN" provista por el usuario (imagen, 2026-07-07): encabezado con logo + N°/fechas, datos del cliente, detalle de la abertura + detalle con campos SI/NO, nota lateral, tabla de medidas, croquis cuadriculado con Interior/Exterior/Arriba, pie con firmas y datos de contacto.

## Derivó en

- [FEAT-021](../features/FEAT-021-ordenes-de-fabricacion-etapa1.md) — Etapa 1: modelo + generación automática/manual + edición (implementada 2026-07-07).
- [FEAT-022](../features/FEAT-022-orden-fabricacion-pdf.md) — Etapa 2: PDF A4 corporativo + datos de contacto en Configuración (implementada 2026-07-07). **Requerimiento completo.**
