# Sprint Actual — AkunCalcu

> Estado: Sin sprint activo
> Inicio: —
> Fin: —

## Objetivo del sprint

_Se define en el sprint planning._

## Items del sprint

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
