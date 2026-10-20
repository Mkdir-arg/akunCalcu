# Plan de desarrollo — Requerimientos funcionales Akun (octubre 2026)

> Fecha: 2026-10-20 · Origen: documento "REQUERIMIENTOS FUNCIONALES AKUN ABERTURAS" (Google Docs)
> Estado: plan aprobado por el usuario; requerimientos REQ-053 a REQ-061 en estado Aprobado

## 1. Lo que el cliente pide y ya está hecho

| Pedido | Estado | Referencia |
|---|---|---|
| Importe de colocación en US$ en presupuestos PVC | En producción desde 2026-09-04 | REQ-050 / FEAT-040 |
| RF-OF-001 Rediseño de la Orden de Fabricación | Implementado: azul #145ea7, campo Estructura, Piso/Depto, croquis con cuadrícula, pie desde configuración, sin La Greca | REQ-035 / FEAT-022 |
| "Implementar lo de los dibujos" | Aperturas, plano con cotas y anexo de planos en el PDF hechos. Falta la imagen 3D por ítem en el PDF | REQ-047, REQ-048 hechos; REQ-039 abierto |
| "Cómo quedó lo de las puertas" | El cotizador tiene las aperturas puerta, puerta doble y puerta corrediza | REQ-047 |
| "Pasar los presupuestos de Luzo al sistema de PVC" | Existe el importador de cotizaciones REHAU (PDF). "Luzo" no aparece en el sistema | REQ-049 / FEAT-039 |

## 2. Respuestas a las preguntas abiertas (decididas por el equipo)

| Pregunta | Decisión |
|---|---|
| ID de cliente | ID interno formateado `C-00123`: único, correlativo, no editable, sin migración (REQ-054) |
| Provincia del cliente (la pide Colocación) | Campo opcional nuevo, tabla de las 24 jurisdicciones (REQ-054) |
| Formato de la planilla de Colocación (`.dotx` no adjunto) | Identidad de la Orden de Fabricación; si mandan el .dotx se ajusta la distribución (REQ-057) |
| Recibo único | El de Ventas; desde Presupuestos sale el mismo con el pago en blanco, una copia, sin consumir numeración (REQ-058) |
| Alerta de fin de mes | Banner en el sistema (desde 2 días antes del cierre) + WhatsApp el último día (REQ-061) |
| RF-011 "gastos en pesos en tipos de gastos" | Reportes de gastos con filtro de moneda y columnas Pesos / USD (REQ-060); se confirma con el cliente antes de codificar |
| Responsable en la planilla de Medición | Quien genera el PDF (REQ-056) |

## 3. Piezas compartidas (se construyen una sola vez)

| Pieza | Se crea en | La reutilizan |
|---|---|---|
| `Cliente.codigo`, `etiqueta_selector()`, `pk_desde_codigo()` | REQ-054 | Selects, búsquedas, listados, Excel, modal de alta |
| `Cliente.datos_documento()` (único armado de datos del cliente para documentos) | REQ-054 | PDF de presupuesto, Medición, Colocación, Recibo |
| `Cliente.provincia` + tabla de provincias | REQ-054 | Modal de alta (REQ-055), Colocación (REQ-057) |
| Modal de alta de cliente (partial + inclusion tag + `cliente-modal.js`) + ruta `cliente_create_rapido` | REQ-055 | Ventas y Presupuestos |
| `core/pdf.py` (logo, datos de empresa, render, respuesta) + `core/pdf/base_a4.html` + `_datos_cliente.html` | REQ-056 | Medición, Colocación, Recibo (logo), Orden de Fabricación (helpers) |
| `build_ficha_item(item)` (cantidad, tipología, medidas, color) | REQ-057 | Colocación; opcionalmente la creación de órdenes de fabricación |
| Helpers USD de `Compra` / `PagoCompra` (`saldo_usd`, `monto_en_usd`) | REQ-059 | Reporte de proveedores, detalle de compra, Excel |
| Filtro de moneda (patrón de `ReporteCobranzasForm`) | ya existe (REQ-022) | REQ-059, REQ-060 |
| `comercial/alertas.py` + `es_rol_administracion(user)` | REQ-061 | Banner, listado de ventas, endpoint de WhatsApp |
| Script de render PDF → PNG (scratchpad, fuera del repo) | REQ-056 | Verificación visual de todos los PDFs |

## 4. Sprints

### Prerrequisito del día 1 (no bloquea el Sprint 1)
- Crear y pedir a Meta la aprobación del template `alerta_ventas_sin_facturar` y verificar el billing de WhatsApp Business (REQ-061)
- Mandarle al cliente las preguntas de la sección 6

### Sprint 1 — Clientes (2026-10-20 → 2026-10-27)
| Orden | REQ | Pedido | Migración |
|---|---|---|---|
| 1 | [REQ-053](../requerimientos/REQ-053-filtros-ventas-siempre-visibles.md) | Filtros siempre visibles en Ventas (RF-025) | No |
| 2 | [REQ-054](../requerimientos/REQ-054-id-cliente-y-provincia.md) | ID de cliente + Provincia (RF-023) | Sí: `core/0002` (datos) + `comercial/0024` (nullable) |
| 3 | [REQ-055](../requerimientos/REQ-055-nuevo-cliente-desde-presupuesto.md) | Alta de cliente desde Presupuesto (RF-024) | No |

### Sprint 2 — Documentos del presupuesto
| Orden | REQ | Pedido | Migración |
|---|---|---|---|
| 1 | [REQ-056](../requerimientos/REQ-056-pdf-medicion-y-base-pdf-comun.md) | Base PDF común + Medición (RF-03) | No |
| 2 | [REQ-057](../requerimientos/REQ-057-pdf-colocacion.md) | Colocación (RF-02) | No |
| 3 | [REQ-058](../requerimientos/REQ-058-recibo-unificado.md) | Recibo unificado (RF-01); puede ir en paralelo con 2 | No |

### Sprint 3 — Proveedores, gastos y alertas
| Orden | REQ | Pedido | Migración |
|---|---|---|---|
| 1 | [REQ-059](../requerimientos/REQ-059-cuenta-corriente-proveedores-usd.md) | Cuenta corriente de proveedores en pesos y USD (RF-004 + RF-017) | No |
| 2 | [REQ-060](../requerimientos/REQ-060-gastos-por-moneda-en-reportes.md) | Gastos por moneda en reportes (RF-011) | No |
| 3 | [REQ-061](../requerimientos/REQ-061-alerta-ventas-sin-facturar.md) | Alerta de ventas sin facturar: banner, después WhatsApp cuando Meta apruebe el template (RF-012) | No |

### Después (requiere definición del cliente)
- **Estructuras** ("necesito poder armar las estructuras"): concepto inexistente en el cotizador; hoy "Estructura" es solo un texto libre de la Orden de Fabricación. Pasa por `/idea`
- **Luzo**: con un PDF de muestra se decide si sirve el importador de REHAU o hace falta otro
- **Puertas**: qué falta concretamente
- **Dibujos**: si lo pendiente es la imagen 3D por ítem en el PDF, se retoma REQ-039

## 5. Reglas para no romper lo que hay

- **No tocar** `Cliente.__str__` ni `get_nombre_completo` (los usan facturación AFIP, contabilidad, cobranzas, auditoría)
- **La Orden de Fabricación y el recibo de Ventas tienen que salir idénticos** después del refactor de PDFs: PNG de referencia antes de tocar nada y comparación después
- **Rutas nuevas siempre registradas en `usuarios/access_control.py`**: una ruta sin registrar no da 403, deja entrar a cualquier usuario logueado
- **Endpoints para n8n**: prefijo exento estrecho (`/comercial/api/alertas/`), nunca `/comercial/api/` entero
- **Select2 global**: modales con `data-select2-dropdown-parent`; selects que se actualizan por JS disparan `change` con jQuery
- **xhtml2pdf**: solo tablas, sin flex/grid/colspan/altos en %; se registra en un ADR nuevo junto con la base PDF
- **Django 4.2 en prod vs. 6 en el venv local**: nada de `timezone.utc`, `db_default`, `GeneratedField`
- **Tests**: con `settings_test_sqlite`, comparando contra el baseline de `main` (comercial ya tiene fallas previas) antes de afirmar "0 regresiones"
- **REQ-059 cambia números visibles**: los totales en pesos del reporte de proveedores bajan porque las compras en USD pasan a su propia cuenta. Avisar al usuario antes del deploy, con el conteo de compras USD en producción

## 6. Preguntas para enviar al cliente

1. **Estructuras:** ¿qué es "armar una estructura"? ¿Varias aberturas unidas en un solo conjunto (por ejemplo, una ventana con paños fijos al costado), con un precio y un dibujo conjunto? Un ejemplo real (foto o presupuesto) ayuda mucho.
2. **Luzo:** ¿nos mandan uno o dos PDF de presupuestos de Luzo? Con eso vemos si sirve el importador que ya usamos para REHAU.
3. **Puertas:** el cotizador ya tiene puertas de abrir, dobles y corredizas. ¿Qué es lo que falta: tipologías, precios, accesorios, el dibujo?
4. **Dibujos:** ya están los planos con medidas en el PDF. ¿Lo que falta es la imagen 3D de cada abertura en el presupuesto?
5. **Gastos (RF-011):** lo entendimos como "ver en los reportes de gastos cuánto se gastó en pesos y cuánto en dólares, por tipo de gasto". ¿Es eso?
6. **Colocación:** si tienen la `Planilla Colocaciones.dotx`, nos sirve para copiar la distribución.
7. **Recibo:** el encabezado dice "Elpidio González 5326" y la configuración del sistema dice "José Cubas 4388". ¿Cuál es el correcto, o son domicilio fiscal y comercial?
8. **Orden de Fabricación:** el rediseño ya está en el sistema. ¿Lo vieron? ¿Hay algo que no coincida con la maqueta?

## 7. Hallazgos fuera de alcance (para FIX aparte)

- Compras en USD: la diferencia de cambio deja saldo falso en pesos y puede marcar la compra como pagada antes de tiempo (fase 2 de REQ-059)
- Rutas de presupuestos sin registrar en `access_control`: `presupuestos-eliminar`, `-items-reordenar`, `-item-editar`, `-observaciones` (cualquier usuario logueado entra)
- `/security/salud/api/` está exento de seguridad pero no de auditoría: el latido cada 15 min probablemente llena `AuditLog`
- El link "Crear cliente con estos datos" desde una solicitud no funciona para vendedores sin acceso a Clientes
- `render_orden.py`, citado en la memoria, no existe
