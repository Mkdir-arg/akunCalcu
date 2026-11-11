# Requerimientos — AkunCalcu

> Los requerimientos son ideas que pasaron por el análisis del equipo funcional (/idea) y están listas para entrar al flujo de desarrollo (/feature).
> Este archivo se actualiza al crear o cambiar el estado de un requerimiento.

## Estados posibles

| Estado | Significado |
|--------|-------------|
| Borrador | Idea inicial, sin analizar todavía |
| En análisis | El equipo funcional (PO + Arq) lo está evaluando |
| Aprobado | Listo para entrar a un sprint con /feature |
| En desarrollo | Tiene un FEAT-XXX asignado y está siendo implementado |
| Implementado | Derivó en una feature completada |
| Descartado | Se decidió no hacerlo |

---

## Tabla de requerimientos

| ID | Nombre | Estado | Fecha | Derivó en |
|----|--------|--------|-------|-----------|
| [REQ-001](./REQ-001-documento-v1.md) | Documento V1 del sistema | Implementado | 2026-03-04 | — |
| [REQ-002](./REQ-002-pedidos-telegram.md) | Pedidos por voz via Telegram | Implementado | 2026-03-04 | FEAT-001 |
| [REQ-003](./REQ-003-crud-fabrica-abm.md) | CRUD Fábrica ABM | Implementado | 2026-03-05 | FEAT-002 |
| [REQ-004](./REQ-004-formulas-marcos.md) | Sistema de Fórmulas para Marcos | Implementado | 2026-03-06 | FEAT-003 |
| [REQ-005](./REQ-005-detalle-cliente.md) | Página de detalle de cliente | En desarrollo | 2026-03-06 | FEAT-004 |
| [REQ-006](./REQ-006-modulo-presupuestos.md) | Módulo de Presupuestos | Implementado | 2026-03-11 | FEAT-005 |
| [REQ-007](./REQ-007-pagos-parciales-compras.md) | Pagos Parciales en Compras | Implementado | 2026-03-28 | FEAT-006 |
| [REQ-008](./REQ-008-mejora-presupuestos-cotizador.md) | Mejora Presupuestos: Paridad con Cotizador + UI | Implementado | 2026-03-30 | FEAT-007 |
| [REQ-009](./REQ-009-dolares-cobro-estado-colocado.md) | Registro de dólares en cobros + Estado obligatorio a Colocado | En desarrollo | 2026-04-01 | — |
| [REQ-010](./REQ-010-cuenta-corriente-proveedores.md) | Cuenta corriente por proveedor + forma de pago en gastos | En desarrollo | 2026-04-21 | — |
| [REQ-011](./REQ-011-navegacion-contexto-y-reporte-ventas-facturado.md) | Navegación con retorno contextual + reporte de ventas por importe facturado | En desarrollo | 2026-04-21 | — |
| [REQ-012](./REQ-012-reporte-cobranzas.md) | Reporte de cobranzas por cobro individual | En desarrollo | 2026-04-22 | — |
| [REQ-013](./REQ-013-reporte-ventas-todos.md) | Reporte de ventas muestra Blanco y Negro | En desarrollo | 2026-04-23 | — |
| [REQ-014](./REQ-014-premarco-en-opcionales-y-formulas-marcos.md) | Tipo Premarco en opcionales + relaciones con Líneas y Perfiles | En desarrollo | 2026-05-02 | — |
| [REQ-015](./REQ-015-vista-previa-pdf-ventas.md) | Vista previa de PDF desde ventas | En desarrollo | 2026-05-03 | — |
| [REQ-016](./REQ-016-rediseno-pdf-presupuestos-descripcion-narrativa.md) | Rediseño del PDF de presupuestos con descripción narrativa por ítem | Implementado | 2026-05-04 | FEAT-008 |
| [REQ-017](./REQ-017-compras-y-pagos-de-compra-en-dolares.md) | Compras y pagos de compra en dólares | En desarrollo | 2026-05-04 | — |
| [REQ-018](./REQ-018-recargos-obra-nueva-renovacion-y-fix-desglose-presupuesto.md) | Recargos por obra nueva o renovación + fix de desglose en presupuestos | En desarrollo | 2026-05-07 | — |
| [REQ-019](./REQ-019-roles-permisos-por-modulo-y-opcion.md) | Roles y permisos por módulo y opción | Implementado | 2026-05-09 | FEAT-009 |
| [REQ-020](./REQ-020-auditoria-actividad-usuarios.md) | Auditoría de actividad de usuarios | En desarrollo | 2026-05-10 | — |
| [REQ-021](./REQ-021-confirmacion-reemplazo-accesorios-vidrios.md) | Confirmación al reemplazar accesorios o vidrios en configurador de hojas | En desarrollo | 2026-05-15 | — |
| [REQ-022](./REQ-022-cobranzas-usd-separadas.md) | Visualización separada de cobranzas en USD | En desarrollo | 2026-05-16 | — |
| [REQ-023](./REQ-023-edicion-masiva-precios-perfiles.md) | Edición masiva de precios en perfiles | En desarrollo | 2026-05-16 | — |
| [REQ-024](./REQ-024-gastos-diarios-voz-whatsapp.md) | Gastos Diarios por nota de voz de WhatsApp | En desarrollo | 2026-05-17 | — |
| [REQ-025](./REQ-025-buscador-accesorios-config-hojas.md) | Buscador de accesorios en configurador de hojas | Implementado | 2026-05-17 | FEAT-010 |
| [REQ-026](./REQ-026-estandarizar-selectores-buscables-sistema.md) | Estandarizar selectores buscables en todo el sistema | Implementado | 2026-05-17 | FEAT-011 |
| [REQ-027](./REQ-027-deploy-railway.md) | Desplegar AkunCalcu en Railway (Django + MySQL + n8n + Evolution) | En desarrollo | 2026-05-17 | — |
| [REQ-028](./REQ-028-backup-automatizado-n8n-drive.md) | Backup automatizado de BD con n8n + Google Drive | Implementado | 2026-05-24 | FEAT-012 |
| [REQ-029](./REQ-029-modalidad-sena-presupuestos.md) | Modalidad de seña en presupuestos | Implementado | 2026-05-26 | FEAT-013 |
| [REQ-030](./REQ-030-confirmacion-reemplazo-accesorio-vidrio.md) | Confirmación modal antes de reemplazar accesorio o vidrio | En desarrollo | 2026-05-26 | — |
| [REQ-031](./REQ-031-modulo-agenda-recordatorios.md) | Módulo de Agenda con recordatorios por WhatsApp | En desarrollo | 2026-06-07 | — |
| [REQ-032](./REQ-032-presupuestos-pvc-en-dolares.md) | Presupuestos PVC siempre en dólares | Implementado | 2026-06-19 | FEAT-015 |
| [REQ-033](./REQ-033-productos-terciarizados-precio-manual.md) | Productos terciarizados con precio manual | Implementado | 2026-06-27 | FEAT-016 |
| [REQ-034](./REQ-034-confirmacion-presupuesto-genera-venta-y-pedido.md) | Confirmación de presupuesto genera venta y pedido de fábrica | Implementado | 2026-07-07 | FEAT-019 |
| [REQ-035](./REQ-035-ordenes-de-fabricacion-en-pedidos.md) | Órdenes de Fabricación dentro del pedido de fábrica (planilla digital + PDF A4) | Implementado | 2026-07-07 | FEAT-021 + FEAT-022 |
| [REQ-036](./REQ-036-eliminar-modulo-despiece.md) | Eliminar módulo de despiece y transformar Pedidos de Fábrica (prerrequisito de REQ-035) | Implementado | 2026-07-07 | FEAT-020 |
| [REQ-037](./REQ-037-reparto-automatico-solicitudes-presupuesto.md) | Reparto automático de solicitudes de presupuesto por email (n8n + round-robin) | Implementado | 2026-07-18 | FEAT-025 |
| [REQ-038](./REQ-038-graficador-3d-aberturas-en-cotizador.md) | Graficador 3D de aberturas en el cotizador de presupuestos | Implementado | 2026-07-24 | FEAT-030 |
| [REQ-039](./REQ-039-imagen-3d-por-item-en-lista-y-pdf.md) | Imagen 3D por ítem en la lista y en el PDF del presupuesto (Fase 2) | En desarrollo | 2026-07-24 | — |
| [REQ-040](./REQ-040-horario-evento-agenda.md) | Horario del evento en la agenda (separado de la hora de envío) | En desarrollo | 2026-07-24 | — |
| [REQ-041](./REQ-041-tirantes-divisores-relleno-por-seccion.md) | Tirantes divisores con relleno por sección en el cotizador | Implementado | 2026-07-27 | FEAT-031 |
| [REQ-042](./REQ-042-opcional-tipo-unidad.md) | Opcional de tipo "unidad" (cantidad × precio en el cotizador) | Implementado | 2026-07-27 | FEAT-032 |
| [REQ-043](./REQ-043-orden-manual-items-presupuesto.md) | Orden manual de los ítems del presupuesto (arrastrar) | Implementado | 2026-07-30 | FEAT-033 |
| [REQ-044](./REQ-044-orientacion-tirantes-divisores.md) | Orientación de los tirantes divisores (vertical u horizontal) | Implementado | 2026-08-01 | FEAT-034 |
| [REQ-045](./REQ-045-panel-salud-integraciones.md) | Panel de salud de las integraciones (n8n, backups, migraciones) | Implementado | 2026-08-01 | FEAT-035 |
| [REQ-046](./REQ-046-revestimientos-catalogo-vidrios.md) | Revestimientos en el catálogo de vidrios (campo Tipo) | Implementado | 2026-08-18 | FEAT-036 |
| [REQ-047](./REQ-047-aperturas-configurables.md) | Aperturas configurables por producto y por ítem (símbolo 2D, 3D, PDF) | Implementado | 2026-09-03 | FEAT-037 |
| [REQ-048](./REQ-048-elevacion-tecnica-cotas.md) | Elevación técnica con cotas en cotizador, PDF (anexo) y presupuesto | Implementado | 2026-08-26 | FEAT-038 |
| [REQ-049](./REQ-049-importar-cotizacion-pvc.md) | Importar los ítems de una cotización PVC externa al presupuesto | Implementado | 2026-09-04 | FEAT-039 |
| [REQ-050](./REQ-050-colocacion-en-dolares-pvc.md) | Colocación en dólares en los presupuestos PVC (entrada en US$, persistencia en pesos) | Implementado | 2026-09-04 | FEAT-040 |
| [REQ-051](./REQ-051-inactivar-productos-abm.md) | Inactivar y reactivar productos desde el ABM (ocultos en el cotizador) | Implementado | 2026-09-05 | FEAT-041 |
| [REQ-052](./REQ-052-inactivar-productos-masivo.md) | Inactivar o activar varios productos de una vez desde el ABM | Implementado | 2026-09-05 | FEAT-041 |
| [REQ-053](./REQ-053-filtros-ventas-siempre-visibles.md) | Panel de filtros siempre visible en Ventas (RF-025) | Implementado | 2026-10-20 | FEAT-042 |
| [REQ-054](./REQ-054-id-cliente-y-provincia.md) | ID de cliente visible en todo el sistema + Provincia del cliente (RF-023) | Implementado | 2026-10-20 | FEAT-043 |
| [REQ-055](./REQ-055-nuevo-cliente-desde-presupuesto.md) | Alta rápida de cliente desde el formulario de Presupuesto (RF-024) | Implementado | 2026-10-20 | FEAT-044 |
| [REQ-056](./REQ-056-pdf-medicion-y-base-pdf-comun.md) | Planilla de Medición (PDF) + base común de PDFs internos A4 (RF-03) | Implementado | 2026-10-20 | [FEAT-050](../features/FEAT-050-planilla-medicion.md) |
| [REQ-057](./REQ-057-pdf-colocacion.md) | Planilla de Colocación (PDF) desde el presupuesto confirmado (RF-02), con envío por WhatsApp | Implementado | 2026-11-09 | [FEAT-049](../features/FEAT-049-planilla-colocacion.md) |
| [REQ-058](./REQ-058-recibo-unificado.md) | Recibo unificado entre Presupuestos y Ventas (RF-01) | Aprobado | 2026-10-20 | — |
| [REQ-059](./REQ-059-cuenta-corriente-proveedores-usd.md) | Cuenta corriente de proveedores en pesos y en dólares (RF-004 + RF-017) | Aprobado | 2026-10-20 | — |
| [REQ-060](./REQ-060-gastos-por-moneda-en-reportes.md) | Gastos diferenciados por moneda en los reportes (RF-011) | Aprobado | 2026-10-20 | — |
| [REQ-061](./REQ-061-alerta-ventas-sin-facturar.md) | Alerta de ventas en blanco sin facturar al cierre del mes, sistema + WhatsApp (RF-012) | Aprobado | 2026-10-20 | — |
| [REQ-062](./REQ-062-estructuras.md) | Estructuras: varias aberturas ubicadas sobre una pared, cotizadas como un conjunto | Implementado (Etapa 1) | 2026-10-22 | [FEAT-045](../features/FEAT-045-estructuras.md) |
| [REQ-063](./REQ-063-circuito-pedidos-fabrica.md) | Circuito de pedidos de fábrica: estados, trabajo del taller y Orden de Fabricación mejorada | Implementado (Etapa 1) | 2026-10-29 | — |
| [REQ-064](./REQ-064-rediseno-taller.md) | Rediseño visual «Taller» de todo el sistema | Implementado | 2026-10-29 | [FEAT-046](../features/FEAT-046-rediseno-taller.md) |
| [REQ-065](./REQ-065-tiempo-real-polling.md) | Actualización en vivo por polling (listados, avisos, dólar, KPIs, edición simultánea) | Implementado | 2026-10-29 | [FEAT-047](../features/FEAT-047-tiempo-real.md) |
| [REQ-066](./REQ-066-animacion-login-ventana.md) | Animación de bienvenida en el login: la ventana se abre y sale una persona | En desarrollo | 2026-11-09 | — |
| [REQ-067](./REQ-067-orden-abertura-desde-catalogo.md) | Abertura de la Orden de Fabricación elegida del catálogo, con la lógica del cotizador | Implementado | 2026-11-10 | [FEAT-051](../features/FEAT-051-orden-abertura-desde-catalogo.md) |
| [REQ-068](./REQ-068-croquis-orden-fabricacion.md) | Croquis dibujado en el PDF de la Orden de Fabricación (apertura, paños fijos, travesaños) | Implementado | 2026-11-10 | [FEAT-052](../features/FEAT-052-croquis-orden-fabricacion.md) |
| [REQ-069](./REQ-069-novedades-del-sistema.md) | Novedades del sistema: borrador automático por cada cambio a main, revisión del admin y aviso al equipo | Implementado | 2026-11-10 | [FEAT-053](../features/FEAT-053-novedades-del-sistema.md) |
| [REQ-070](./REQ-070-optimizador-corte-marco.md) | Optimizador de corte de aluminio: perfiles de marco de varios pedidos acomodados en barras + planilla PDF | Implementado | 2026-11-10 | FEAT-054 |
| [REQ-071](./REQ-071-resumen-diario-whatsapp.md) | Resumen diario y semanal por WhatsApp para la dirección (n8n + GPT redacta, Django calcula) | Implementado | 2026-11-10 | [FEAT-055](../features/FEAT-055-resumen-diario-whatsapp.md) |
| [REQ-072](./REQ-072-modulo-tareas.md) | Módulo de tareas para empleados (responsable, fecha límite, estado) que se suma al resumen | Aprobado | 2026-11-10 | — |
| [REQ-073](./REQ-073-checks-flete-expreso-izaje.md) | Checks «Flete expreso CABA» y «No incluye izaje» en el presupuesto y en Observaciones del PDF | Implementado | 2026-11-11 | [FEAT-056](../features/FEAT-056-checks-flete-expreso-izaje.md) |
| [REQ-074](./REQ-074-adicionales-libres-item.md) | «Agregar adicional»: conceptos libres con etiqueta y precio en el ítem, fuera del margen y del IVA | Implementado | 2026-11-11 | [FEAT-057](../features/FEAT-057-adicionales-libres-item.md) |
| [REQ-075](./REQ-075-atencion-automatica-clientes-omnicanal.md) | Atención autónoma de clientes por WhatsApp, email e Instagram (cotiza aluminio, deriva PVC, agenda visita) | En desarrollo | 2026-11-11 | [FEAT-058](../features/FEAT-058-seccion-agente-configuracion.md) (Etapa 1a) |
| [REQ-076](./REQ-076-simulador-conversacion-agente.md) | Simulador de conversación del agente (chat de prueba con la configuración real) | En desarrollo | 2026-11-11 | — |
