# Sprint Actual — AkunCalcu

> Estado: Sprint 1 activo (plan RF Akun, ver [plan-rf-akun-2026-10.md](./plan-rf-akun-2026-10.md))
> Inicio: 2026-10-20
> Fin: 2026-10-27

## Objetivo del sprint

Clientes: ID de cliente visible en todo el sistema, provincia del cliente, alta rápida desde
Presupuestos y filtros de Ventas siempre visibles. Deja listas las piezas que usan los PDFs del Sprint 2.

**Tareas en paralelo del día 1:** pedir a Meta la aprobación del template `alerta_ventas_sin_facturar`
(REQ-061) y enviar al cliente las preguntas de la sección 6 del plan.

## Sprint 1 — en curso

| ID | User Story | Estado | Notas |
|----|-----------|--------|-------|
| US-053 | Filtros siempre visibles en Ventas (REQ-053, RF-025) | ✅ Completado | Solo template |
| US-054 | ID de cliente + Provincia (REQ-054, RF-023) | ✅ Completado | Migraciones `core/0002` (datos) + `comercial/0024` |
| US-055 | Alta rápida de cliente desde Presupuesto (REQ-055, RF-024) | ✅ Completado | Depende de US-054 |
| US-062 | Estructuras: varias aberturas sobre una pared, cotizadas como un conjunto (REQ-062) | ✅ Completado (Etapa 1) | Fuera de plan; FEAT-045 / ADR-022. Sin migración. Etapa 2 pendiente. Falta probar con el catálogo real |
| US-064 | Rediseño visual «Taller» de todo el sistema (REQ-064) | ✅ Completado | Fuera de plan; FEAT-046 / ADR-023. Solo en `development`; PDF intactos |
| US-065 | Actualización en vivo por polling (REQ-065) | ✅ Completado | Fuera de plan; FEAT-047 / ADR-024. Migraciones de `core` |
| US-063 | Circuito de pedidos de fábrica: estados, etapas del taller, liberar, revisiones y PDF (REQ-063) | ✅ Completado (Etapa 1) | Fuera de plan; FEAT-048 / ADR-025. Migración `plantillas/0017`. Etapas 2 (tablero, QR) y 3 (planos) pendientes |
| US-057 | Planilla de Colocación (PDF) + envío por WhatsApp a números autorizados (REQ-057, RF-02) | ✅ Completado | Adelantado del Sprint 2; FEAT-049 / ADR-026. Incluye la base común de PDF (parte de REQ-056). Sin migración. Falta aprobación de Meta de la plantilla `planilla_colocacion` y prueba real |
| US-056 | Planilla de Medición en PDF desde el presupuesto (REQ-056, RF-03) | ✅ Completado | Adelantado del Sprint 2; FEAT-050. Usa la base común de FEAT-049. Sin migración |
| US-067 | Abertura de la Orden de Fabricación elegida del catálogo, con la cascada del cotizador (REQ-067) | ✅ Completado | Fuera de plan; FEAT-051 / ADR-027. Migración `plantillas/0018`. Falta probar la cascada con el catálogo real en prod |
| US-068 | Croquis dibujado en el PDF de la Orden de Fabricación (REQ-068) | ✅ Completado | Fuera de plan; FEAT-052 / ADR-028. Sin migración. Falta confirmar «vista desde el interior» con fábrica y probar con órdenes reales |
| US-069 | Novedades del sistema generadas desde GitHub (REQ-069) | ✅ Completado | Fuera de plan; FEAT-053 / ADR-029. Migración `novedades/0001`. Faltan los secrets en GitHub y Railway y probarlo en el navegador |
| US-070 | Optimizador de corte de perfiles de marco (REQ-070) | ✅ Completado | Fuera de plan; FEAT-054 / ADR-030. Migración `optimizador/0001`. Falta probar en el navegador y con el catálogo real |
| US-071 | Resumen diario y semanal por WhatsApp para la dirección (REQ-071) | ✅ Completado | Fuera de plan; FEAT-055 / ADR-031. Migración `resumenes/0001`. n8n `iEON0QIYoc8O9Bbk` inactivo: faltan plantilla de Meta, webhook (FIX-026), rama en gastos y variables |
| US-073 | Checks «Flete expreso CABA» y «No incluye izaje» en el presupuesto (REQ-073) | ✅ Completado | Fuera de plan; FEAT-056. Migración `presupuestos/0013`. Falta probar en el navegador |
| US-074 | «Agregar adicional»: conceptos libres con etiqueta y precio en el ítem (REQ-074) | ✅ Completado | Fuera de plan; FEAT-057. Sin migración. Falta probar en el navegador |

## Items completados (sprints anteriores)

| ID | User Story | Estado | Notas |
|----|-----------|--------|-------|
| US-003 | CRUD Fábrica ABM (Extrusoras, Líneas, Productos, Marcos, Hojas, Interiores, Perfiles, Accesorios, Vidrios, Tratamientos) | ✅ Completado | Soft delete via bloqueado; IDs manuales; migración RunSQL |
| US-004 | Popup para avanzar estado al completar pago de venta | ✅ Completado | Redirect con query param; fetch AJAX; SweetAlert2 |
| US-006 | Módulo de Presupuestos — Paso 1 de Fábrica | ✅ Completado | App nueva; cotizador embebido; PDF via @media print; FEAT-005 |
| US-008 | Mejora Presupuestos: Paridad con Cotizador + UI | ✅ Completado | Opcionales, desglose, KPIs, unificación; FEAT-007 |
| US-009 | Rediseño del PDF de presupuestos con descripción narrativa por ítem | ✅ Completado | Implementado fuera de sprint activo; FEAT-008 |
| US-019 | Roles y permisos por módulo y opción | ✅ Completado | Implementado fuera de sprint activo; FEAT-009 |
| US-025 | Buscador de accesorios en configurador de hojas | ✅ Completado | Implementado fuera de sprint activo; FEAT-010 |
| US-026 | Estandarizar selectores buscables en todo el sistema | ✅ Completado | Implementado fuera de sprint activo; FEAT-011 |
| US-028 | Backup automatizado de BD con n8n + Google Drive | ✅ Completado | Implementado fuera de sprint activo; FEAT-012 |
| US-029 | Modalidad de seña en presupuestos | ✅ Completado | Implementado fuera de sprint activo; FEAT-013 |
| US-030 | Confirmación antes de reemplazar accesorio en hoja configurator | ✅ Completado | Implementado fuera de sprint activo; FEAT-014 |
| US-032 | Presupuestos PVC siempre en dólares | ✅ Completado | Implementado fuera de sprint activo; FEAT-015 |
| US-033 | Productos terciarizados con precio manual | ✅ Completado | Implementado fuera de sprint activo; FEAT-016 (migración pendiente de verificar en prod) |
| US-034 | Confirmar presupuesto pide seña y genera venta + pedido de fábrica | ✅ Completado | Implementado fuera de sprint activo; FEAT-019 (migración plantillas/0013 pendiente en prod) |
| US-036 | Eliminar módulo de despiece; Pedidos de Fábrica queda solo | ✅ Completado | Implementado fuera de sprint activo; FEAT-020 (migración plantillas/0014 pendiente en prod — borra datos del despiece) |
| US-035 | Órdenes de Fabricación en el pedido (planilla + PDF A4) | ✅ Completado | Etapa 1 (FEAT-021) + Etapa 2 PDF A4 (FEAT-022). Migraciones plantillas/0015 y configuracion/0003 pendientes en prod |
| US-046 | Revestimientos en el catálogo de vidrios (campo Tipo) | ✅ Completado | Implementado fuera de sprint activo; FEAT-036 + ADR-018. Reemplaza MaterialCiego. Pendiente: cargar los revestimientos |
| US-047 | Aperturas configurables por producto y por ítem (3D, símbolo 2D, PDF) | ✅ Completado | FEAT-037 + ADR-019. Migr. pricing/0007 aplicada. Pendiente: cargar aperturas admitidas en los productos |
| US-048 | Elevación técnica con cotas: pestaña Plano, anexo en PDF, miniatura | ✅ Completado | FEAT-038 + ADR-020 (retroactivo: se hizo sin REQ) |
| US-049 | Importar cotización REHAU (PDF) a presupuesto PVC con vista previa | ✅ Completado | FEAT-039 + ADR-021. Sin migración. Pendiente: copiar PDF reales a `test_data/` y confirmar costo vs precio final |
| US-050 | Colocación en US$ en presupuestos PVC (persistencia en pesos) | ✅ Completado | FEAT-040, extiende ADR-010. Sin migración; los existentes no cambian |
| US-051 | Inactivar / activar productos desde el ABM (ocultos en el cotizador) | ✅ Completado | FEAT-041. Reutiliza `bloqueado`; los "eliminados" reaparecen como Inactivos |
| US-052 | Inactivar / activar varios productos de una vez | ✅ Completado | REQ-052, dentro de FEAT-041. Sin migración |
| US-037 | Reparto automático de solicitudes de presupuesto (n8n + round-robin) | ✅ Completado | App `solicitudes` nueva; FEAT-025. Migraciones solicitudes/0001, usuarios/0004 y usuarios/0005 pendientes en prod |
| US-038 | Graficador 3D de aberturas en el cotizador de presupuestos | ✅ Completado | Three.js como módulo estático; clasificador de tipología; FEAT-030. Sin migración |
| US-042 | Opcional de tipo "unidad" (cantidad × precio en el cotizador) | ✅ Completado | Tipo `unidad` + campo `precio_unidad`; FEAT-032. Migración `plantillas/0016` pendiente en prod |
| US-043 | Orden manual de los ítems del presupuesto (arrastrar) | ✅ Completado | Sin migración (`orden` ya existía); FEAT-033 |
| US-041 | Tirantes divisores con relleno por sección en el cotizador | ✅ Completado | Modelo `MaterialCiego` + ABM; motor de secciones; FEAT-031 / ADR-016. Migración `pricing/0005` pendiente en prod |
| US-045 | Panel de salud de las integraciones (n8n, backups, migraciones) | ✅ Completado | App `security`; FEAT-035 / ADR-017. Migración `security/0004` **ya aplicada en prod**; workflow de latido `iDrsq7vyGPHG7qAb` activo |
| US-044 | Orientación de los tirantes divisores (vertical u horizontal) | ✅ Completado | Sin migración; `medida_mm` + `orientacion` en el JSON, retrocompatible; FEAT-034 / ADR-016 punto 10. Falta verificar el render 3D con Docker |

## Impedimentos

_Ninguno._

---

## Historial de sprints anteriores

Ver `docs/team/changelog.md` para el detalle de cada sprint.
