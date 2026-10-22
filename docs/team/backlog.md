# Product Backlog — AkunCalcu

> Actualizado: 2026-10-22

## Leyenda
- 🟡 Pendiente
- 🔵 En sprint
- ✅ Completado
- ❌ Descartado

## Features pendientes

Origen: documento de requerimientos funcionales de Akun. Plan, orden y piezas compartidas en
[plan-rf-akun-2026-10.md](./plan-rf-akun-2026-10.md).

| ID | User Story | Complejidad | Estado |
|----|-----------|-------------|--------|
| US-053 | Como administrativo quiero ver siempre el panel de filtros de Ventas para buscar sin abrirlo cada vez (RF-025) | Pequeño | ✅ Sprint 1 |
| US-054 | Como administrativo quiero un ID único de cliente visible en Clientes, Presupuestos y Ventas, y su provincia (RF-023) | Mediano | ✅ Sprint 1 |
| US-055 | Como vendedor quiero dar de alta un cliente sin salir del formulario de presupuesto (RF-024) | Pequeño / Mediano | ✅ Sprint 1 |
| US-056 | Como vendedor quiero generar la planilla de Medición en PDF desde el presupuesto (RF-03) | Mediano | 🟡 Sprint 2 |
| US-057 | Como coordinador quiero generar la planilla de Colocación en PDF desde el presupuesto confirmado (RF-02) | Mediano | 🟡 Sprint 2 |
| US-058 | Como administrativo quiero que el recibo de Presupuestos sea el mismo que el de Ventas (RF-01) | Mediano | 🟡 Sprint 2 |
| US-059 | Como administrativo quiero la cuenta corriente de proveedores separada en pesos y en dólares (RF-004 + RF-017) | Grande | 🟡 Sprint 3 |
| US-060 | Como administrativo quiero ver los gastos por tipo separados en pesos y en dólares (RF-011) | Pequeño / Mediano | 🟡 Sprint 3 |
| US-061 | Como administración quiero que me avisen al cierre del mes las ventas en blanco sin facturar, en el sistema y por WhatsApp (RF-012) | Mediano | 🟡 Sprint 3 |
| US-062 | Como vendedor quiero ubicar varias aberturas sobre una pared y cotizarlas como una sola estructura, con plano y precio total ([REQ-062](../requerimientos/REQ-062-estructuras.md)) | Grande | ✅ Etapa 1 completada (FEAT-045); Etapa 2 pendiente |

---

## Completadas

| ID | User Story | Complejidad |
|----|-----------|-------------|
| US-001 | Como equipo de desarrollo, quiero un documento V1 del sistema para tener una referencia compartida | Pequeño ✅ |
| US-002 | Como vendedor, quiero enviar un audio de voz por Telegram con ítems de un pedido para que quede registrado en AkunCalcu | Grande ✅ |
| US-003 | Como administrador, quiero agregar, editar y eliminar de forma lógica los registros de Fábrica (Extrusoras, Líneas, Productos, Marcos, Hojas, Interiores, Perfiles, Accesorios, Vidrios, Tratamientos) para gestionar la configuración de la fábrica desde la interfaz web | Grande ✅ |
| US-004 | Como vendedor, quiero que al registrar el último pago de una venta (saldo = $0) me aparezca un popup para cambiar el estado a "Colocado" | Pequeño ✅ |
| US-005 | Como administrador, quiero agregar fórmulas de perfiles al configurar un Marco para definir automáticamente las dimensiones de los perfiles necesarios para fabricar ese marco | Mediano ✅ |
| US-006 | Como vendedor, quiero armar un presupuesto vinculado a un cliente, agregar N ítems con la lógica del cotizador, dejar comentarios y generar un PDF para el cliente | Grande ✅ |
| US-037 | Como responsable comercial, quiero que los pedidos de presupuesto que llegan por email se repartan automáticamente y por turnos entre los vendedores para que ninguno quede sin atender | Grande ✅ |
| US-038 | Como vendedor, quiero ver un diseño 3D de la abertura al calcular cada ítem del presupuesto para confirmar visualmente la configuración antes de guardarla | Grande ✅ |
| US-045 | Como responsable del sistema, quiero ver en una sola pantalla el estado de las integraciones para detectar en minutos una caída que hoy tarda días en descubrirse | Grande ✅ |
| US-049 | Como vendedor que arma un presupuesto en PVC, quiero subir el PDF de la cotización REHAU y que se carguen solos todos sus ítems, para no tipearlos uno por uno | Mediano ✅ |
| US-050 | Como vendedor que arma un presupuesto en PVC, quiero cargar la colocación en dólares para no convertirla a pesos a mano | Pequeño ✅ |
| US-051 | Como administrador del catálogo, quiero inactivar y reactivar productos para que el cotizador no los ofrezca sin perder su configuración | Pequeño ✅ |
| US-052 | Como administrador del catálogo, quiero seleccionar varios productos e inactivarlos o activarlos de una vez | Pequeño ✅ |

---

## Ideas sin refinar

_Acá van las ideas crudas antes de convertirlas en user stories._

- **Estructuras** ("necesito poder armar las estructuras"): concepto inexistente en el cotizador. Esperando definición del cliente → `/idea`
- **Presupuestos de Luzo a PVC**: esperando un PDF de muestra para decidir si sirve el importador REHAU (REQ-049)
- **Puertas**: el cotizador ya tiene puertas (REQ-047); esperando qué falta según el cliente
- **Dibujos**: si lo pendiente es la imagen 3D por ítem en el PDF, retomar REQ-039

---

## Deuda técnica / fixes pendientes

_Detectados durante REQ-062 (2026-10-22); no se tocaron para no mezclar alcance._

- **Rutas sin registrar en `usuarios/access_control.py`** (`presupuestos-item-editar`, `presupuestos-items-reordenar`, `presupuestos-observaciones`, `perfiles-list`): dejan pasar a cualquier usuario logueado. Candidato a `/fix`
- **Ícono `fa-arrow-up-arrow-down`** del botón "Orden" en `presupuestos/detalle.html`: no existe en FontAwesome 6.4.0, el botón se ve sin ícono
- **`pricing/services/formula_parser.py:32` usa `ast.Num`**, que no existe en Python 3.14. Prod usa 3.12 y hoy anda; rompe el día que se suba de versión
