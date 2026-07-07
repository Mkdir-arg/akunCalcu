# FEAT-022 — PDF A4 de la Orden de Fabricación + datos de contacto en Configuración (Etapa 2)

**Estado:** Implementado
**Fecha:** 2026-07-07
**Requerimiento:** [REQ-035](../requerimientos/REQ-035-ordenes-de-fabricacion-en-pedidos.md) — **Etapa 2 de 2** (cierra el requerimiento). La Etapa 1 fue [FEAT-021](./FEAT-021-ordenes-de-fabricacion-etapa1.md).

## Descripción funcional

Cada orden de fabricación se puede **imprimir como PDF A4** con la identidad visual de Akun, replicando la planilla papel:

- **Encabezado:** logo, título "ORDEN DE FABRICACIÓN", N° de orden, fecha y fecha comprometida.
- **Cuerpo:** atendido por / medición realizada por; Datos del Cliente; Detalle de la abertura; sección Detalle completa (todos los campos SI/NO + Estructura); panel de NOTA a la derecha; tabla de Detalle de Medidas (con filas en blanco para completar a mano).
- **Croquis:** área cuadriculada gris clara con indicadores Interior / Arriba / Exterior, para dibujar a mano sobre el papel impreso.
- **Pie:** nombre y datos de contacto de Akun (dirección, teléfonos, web) leídos desde `ConfiguracionGeneral`, más las cajas de firma Preparó / Revisó / Producción.

El botón "Imprimir PDF" está en la tabla de órdenes del pedido y en la pantalla de edición de la orden.

**Datos de contacto configurables:** se agregaron las claves `empresa_nombre`, `empresa_direccion`, `empresa_telefonos`, `empresa_web` a `ConfiguracionGeneral`, con una pantalla de edición en Configuración General (solo staff). El PDF las lee en cada render, de modo que cambiar el pie no requiere tocar código.

## Criterios de aceptación cubiertos (cierre del REQ-035)

- [x] Identidad visual: azul `#145ea7`, negro `#1d1d1b`, fondo blanco, logo, títulos de sección con fondo azul, bordes finos, tipografía Arial, tamaño A4.
- [x] Encabezado con logo, título, N° orden, fecha y fecha comprometida.
- [x] Todos los campos de la planilla + Nota + tabla de medidas.
- [x] Croquis cuadriculado con Interior/Exterior/Arriba, para dibujo a mano.
- [x] Pie con datos de contacto desde configuración (sin datos hardcodeados ni de La Greca Home) + firmas.
- [x] Optimizado para impresión A4 / exportación a PDF.

## Archivos modificados

- `akuna_calc/configuracion/models.py` — helpers `get_valor`/`set_valor`/`get_datos_empresa` + `EMPRESA_DEFAULTS`
- `akuna_calc/configuracion/migrations/0003_seed_datos_empresa.py` (nueva, data migration)
- `akuna_calc/configuracion/forms.py` — `DatosEmpresaForm`
- `akuna_calc/configuracion/views.py`, `urls.py`, `templates/configuracion/general.html`, `datos_empresa_form.html` (nuevo)
- `akuna_calc/plantillas/views.py` — `orden_pdf` + `_build_logo_data_url`
- `akuna_calc/plantillas/urls.py`, `tests.py`
- `akuna_calc/plantillas/templates/plantillas/orden_pdf.html` (nuevo), `pedido_detail.html` y `orden_form.html` (botón PDF)
- `akuna_calc/usuarios/access_control.py` — ruta `orden_pdf`

## Decisiones técnicas

- PDF con **xhtml2pdf** (patrón ADR-006, sin librerías nuevas). Todo el layout es **table-based**: xhtml2pdf no soporta flexbox/grid, `height:100%` ni columnas más angostas que su padding (ambos casos hacían fallar el render; se resolvió con layouts de una sola columna y anchos holgados). El croquis es una tabla de celdas con borde gris claro.
- El logo se embebe como data URI; se replicó el helper `_build_logo_data_url` localmente en `plantillas` para no crear un import circular con `presupuestos`.
- Los datos de contacto viven en `ConfiguracionGeneral` (clave/valor), sembrados por data migration y editables por pantalla — cumple "sin modificar código a futuro".

## Validación

- `python manage.py test plantillas presupuestos configuracion --settings=akuna_calc.settings_test_sqlite`
- Resultado: **116 tests OK** (nuevos: generación de PDF válido con `%PDF` + uso de datos de empresa desde config), sin regresiones.
- PDF de muestra generado y validado (`err=0`, documento `%PDF` A4).

## Pendiente de deploy

- Migración `configuracion/0003_seed_datos_empresa` pendiente de aplicar en Docker/Railway (siembra las 4 claves de contacto; idempotente vía `get_or_create`).
- **Nota:** los valores de contacto sembrados son los de la maqueta; ajustarlos en Configuración → Datos de contacto de la empresa con los datos reales de Akun.
