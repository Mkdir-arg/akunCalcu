# FEAT-039 — Importar los ítems de una cotización REHAU (PDF) a un presupuesto PVC

- **Estado:** Implementado
- **Fecha:** 2026-09-04
- **Requerimiento:** [REQ-049](../requerimientos/REQ-049-importar-cotizacion-pvc.md)
- **ADR:** [ADR-021](../team/decisions.md)
- **Apps:** `presupuestos` (módulo de lectura, formularios, vista, template) · `usuarios` (registro de la ruta)
- **Migración:** ninguna

## Qué hace

Los presupuestos en PVC se cotizan en el software de REHAU, que entrega un PDF. Hasta ahora cada
ítem se volvía a tipear a mano en AkunCalcu (descripción, cantidad, valor USD, margen). Ahora:

1. En un presupuesto **PVC** aparece el botón **"Importar cotización"** al lado de "Agregar item"
   (solo si tiene tipo de obra y no está bloqueado).
2. Se sube el PDF y se indica el margen a aplicar (default 30 %, el mismo de la carga manual).
3. El sistema lee el texto del PDF y muestra una **vista previa**: número de cotización, cliente,
   fecha y total neto del PDF; una fila por ítem con tilde "incluir", tipología, descripción,
   cantidad y unitario USD **editables**, y el total USD y el unitario en pesos calculados en
   vivo. Avisa en amarillo si el total neto del PDF no cierra con la suma de los ítems, y en azul
   si el presupuesto ya tenía ítems.
4. "Confirmar importación" crea todos los ítems marcados de una vez, a continuación de los
   existentes, con **exactamente la misma cuenta que la carga manual**, y deja una entrada en el
   Historial: "Se importaron 2 ítems desde la cotización REHAU Nº 481 (31/08/2026, HERNAN BARBERMAN)".

El archivo **no se guarda**: se lee en memoria, los datos detectados viajan en el formulario de
la vista previa y se descarta.

## Qué se importa y qué no

| Dato | Se importa | Fuente en el PDF |
|---|---|---|
| Tipología (V1, V2…) | Sí | etiqueta "Tipología: Vn" |
| Descripción | Sí | título (sistema, color, vidrio) + componentes (marco, hoja, contramarco, mosquitero) |
| Cantidad | Sí | columna UNIDADES |
| Valor unitario USD | Sí | columna UNITARIO |
| Número, cliente, fecha, total neto | Sí (para el historial y el control) | cabecera y pie |
| **Medidas (ancho × alto)** | **No** | están solo en el dibujo, que es una imagen |
| IVA, total proyecto, m², ml | No | no aplican al ítem |

La descripción queda como `"V1 · Corredera Ventana Lineal EURO-DESIGN SLIDE S920 en color Rob/Rob.
Vidrio 3+3/9/4. Marco 3 Euro-Design Slide, Hoja1 Euro-Design Slide, Cuarto caña 17 mm,
Contramarco 60 mm, Con mosquitero"`, dentro de los 300 caracteres del campo.

## Cómo está armado

- **`presupuestos/importar_rehau.py`** — dos funciones separadas a propósito:
  `extraer_texto(archivo)` (pypdf, todas las páginas, límite de 40) y `parsear_cotizacion(texto)`
  (regex ancladas en la fila de precio `1.469,56U$S 1 1.469,56U$S`; las etiquetas de tipología se
  asocian por conteo, así el parser no depende del orden en que pypdf devuelve el texto). Devuelve
  `CotizacionRehau` con ítems y advertencias; lanza `ImportacionError` si no hay texto o ítems.
- **`ImportarCotizacionForm`** (archivo + margen; valida tamaño ≤ 10 MB y firma `%PDF-`),
  **`ItemImportadoFormSet`** (una fila por ítem de la vista previa) y
  **`ConfirmarImportacionForm`** (margen editable + origen oculto) en `forms.py`.
- **`_fields_item_pvc(...)`** en `views.py`: la cuenta del ítem PVC (pesos con la cotización del
  presupuesto, margen, recargo de renovación) extraída de `_fields_item_desde_post`, que ahora la
  llama. La importación usa la misma función, con un bloque `origen` extra en `resultado_json`
  (`sistema`, `numero`, `cliente`, `fecha`, `tipologia`). El `tipo` sigue siendo `pvc_simple`, así
  el PDF, el editor de ítem, los totales en USD y la confirmación no cambian.
- **`importar_cotizacion`** (GET formulario / POST con archivo → vista previa / POST `confirmar` →
  creación en `transaction.atomic`) y la ruta `presupuestos-importar`, registrada bajo
  `presupuestos.view` en `usuarios/access_control.py`.
- **`templates/presupuestos/importar.html`** con los dos pasos; el JS de la vista previa recalcula
  totales al editar (cotización y recargo vienen del servidor con `unlocalize`).
- **`requirements.txt`** declara `pypdf` explícito aunque ya viniera como dependencia de xhtml2pdf.

## Decisiones

1. **Parser determinista, no IA.** El PDF lo genera siempre el mismo software con la misma
   estructura; tres muestras reales (458, 462, 481) lo confirman. Si REHAU cambia el diseño, el
   sistema dice "no se encontraron ítems" y no crea nada.
2. **Vista previa sin estado en el servidor.** Los datos detectados viajan en el formset; no hay
   sesión, ni archivo temporal, ni tabla de importaciones.
3. **El unitario del PDF se toma como costo** al que se aplica el margen (asunción registrada en
   REQ-049; si fuera precio final, el vendedor pone margen 0 en el formulario).
4. **Los PDF reales de clientes quedan fuera del repo** (`test_data/*.pdf` en `.gitignore`): traen
   nombre y teléfono. El pipeline completo se testea con un PDF generado en memoria con reportlab.

## Verificación

- 22 tests nuevos en `presupuestos/tests.py` (`ParserRehauTest`, `ImportarCotizacionViewTest`):
  cabecera e ítems de las tres muestras, descripción legible, tipologías repetidas y dos páginas,
  advertencias de total, PDF real generado con reportlab, PDF roto, vista previa, archivo que no es
  PDF, PDF sin ítems, confirmación con la cuenta manual (orden, precio, `origen`, historial, total),
  recargo de renovación, sin ítems marcados, valores inválidos, aluminio/bloqueado/sin cotización,
  botón solo en PVC.
- Suite `presupuestos` + `usuarios`: 202 tests OK. `makemigrations --check`: sin cambios.
- Test con los PDF reales de la carpeta `presupuestos/test_data/`: **se saltea hasta que se copien**.

## Pendiente

- Copiar los tres PDF a `akuna_calc/presupuestos/test_data/` y correr
  `ParserRehauTest.test_pdfs_reales_de_la_carpeta`: es la única verificación con el pypdf de verdad
  sobre el archivo de verdad (el orden del texto podría diferir del de las muestras).
- Confirmar con el usuario si el unitario del PDF es costo o precio final.
