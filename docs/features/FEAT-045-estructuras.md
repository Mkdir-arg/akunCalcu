# FEAT-045 — Estructuras: varias aberturas sobre una pared, cotizadas como un conjunto (Etapa 1)

- **Estado:** Implementado (Etapa 1; la Etapa 2 sigue pendiente)
- **Fecha:** 2026-10-22
- **Requerimiento:** [REQ-062](../requerimientos/REQ-062-estructuras.md)
- **Sprint:** Fuera de plan (Sprint 1 RF Akun en curso)
- **Apps:** `pricing`, `presupuestos`, `usuarios`, `static/js`
- **Migración:** ninguna
- **Maquetas:** [editor](https://claude.ai/artifact/BuhHK7nCrSHSK1Cnh9Lbuz) · [dentro del presupuesto](https://claude.ai/artifact/A2jDVaD3iMnwHCLxF6RakK)

## Qué hace

En un presupuesto de aluminio no bloqueado con tipo de obra, el botón **"Agregar estructura"**
(`fa-object-group`) junto a "Agregar item" abre un editor modal:

- **Datos comunes:** nombre (máx. 150), extrusora, línea, tratamiento y margen; pared ancho x alto
  (referencia, no se cobra) y perfil de unión opcional.
- **Aberturas (hasta 12):** "Agregar abertura" abre el cotizador existente en **modo módulo**
  (extrusora, línea y tratamiento bloqueados con "Viene de la estructura"; medidas y margen solo
  lectura; botón "Aplicar a la abertura"). Se ubican arrastrando sobre la pared (grilla de 10 mm,
  imán a bordes de pared y de otras aberturas; si se suelta superpuesta vuelve a su lugar) o con
  medidas exactas en mm (ancho, alto, desde la izquierda, desde el piso).
- **Etiquetas M1..Mn** por posición (izquierda a derecha, abajo hacia arriba).
- **Juntas** detectadas solas (bordes que coinciden con solape mayor a 0; tocarse en una esquina no
  cuenta). Con perfil de unión, cada junta se cobra como un tirante: largo x peso/m x precio/kg +
  tratamiento + margen, prorrateado por largo. Sin perfil, suma pura.
- **Precio** = suma de módulos + unión, recalculado siempre en el servidor (vista previa automática
  700 ms después del último cambio). No deja guardar con errores, módulos sin configurar o precio
  desactualizado.

La estructura es **un renglón** del presupuesto: miniatura SVG, cantidad, ver desglose (tabla de
módulos y juntas, y desglose por módulo), editar con todo restaurado, eliminar y reordenar. En
renovación el recargo de colocación se suma una vez por unidad de estructura.

**PDF:** renglón con el detalle de las aberturas y plano de la pared en el anexo, a ancho completo,
con cotas y etiquetas. **Confirmar** el presupuesto genera **una orden de fabricación por módulo**
(M1..Mn) con numeración corrida (antes era base + índice de ítem), campo "Estructura" con el texto
del conjunto y `MedidaOrdenFabricacion.item = 'M2'`.

## Criterios cumplidos

- [x] Botón "Agregar estructura" en presupuestos de aluminio no bloqueados
- [x] El editor define la pared, los datos comunes y el perfil de unión opcional
- [x] Se agregan aberturas, cada una con la misma cascada del cotizador actual
- [x] Cada abertura se arrastra sobre la pared (imán, grilla de 10 mm) y se ajusta con medidas exactas en mm
- [x] No se guarda con aberturas superpuestas o fuera de la pared, y se explica el motivo
- [x] Las juntas se detectan solas; con perfil de unión se cobran por largo
- [x] Precio = aberturas + juntas, siempre recalculado en el servidor
- [x] Un renglón del presupuesto con cantidad, miniatura, desglose, editar, eliminar y reordenar
- [x] Al editar, el editor se abre con todo restaurado
- [x] En renovación, el recargo de colocación se suma una vez por unidad de estructura
- [x] PDF: renglón con detalle de aberturas y plano de la pared en el anexo
- [x] Al confirmar, una orden de fabricación por abertura (M1..Mn), consecutivas y con "Estructura" completado
- [x] Ítems y presupuestos existentes sin cambios

## Archivos

- Nuevos:
  - `pricing/services/estructura.py` — normalizar con lista blanca, geometría, validación, juntas, envolvente, cálculo por módulo (con `PricingCalculateSerializer`) y unión
  - `presupuestos/estructuras.py` — `fields_item_estructura`: arma el ítem, snapshots por módulo y recargo de renovación
  - `presupuestos/templates/presupuestos/_estructura_editor.html` — editor React en `{% verbatim %}` con form oculto y csrf
  - `static/js/estructura.js` — etiquetas, juntas, validación, envolvente, `svgEstructura`, `svgDibujo`
  - `pricing/fixtures_estructura_geometria.json` — 13 casos de geometría compartidos Python/JS
  - `audit_estructura.mjs` — auditoría con node del JS contra los fixtures
  - `presupuestos/test_estructura_ui.py` — tests de la UI
- Modificados:
  - `pricing/services/calculator.py` — kwarg `segmento` en `_calcular_tirantes_perfil` y wrapper público `precio_perfil_por_largo`
  - `pricing/views.py`, `pricing/urls.py` — `EstructuraCalculateView`, `api/pricing/estructura/calculate/` (`pricing-estructura-calculate`)
  - `usuarios/access_control.py` — registro de la ruta (`cotizador.view` / `presupuestos.view`)
  - `presupuestos/forms.py` — `EstructuraItemForm`
  - `presupuestos/views.py` — `_fields_item_desde_post` desvía con `estructura_json` (PVC rechaza); `editar_item` no deja pisar una estructura sin `estructura_json`; `_crear_orden` generalizada, `_crear_ordenes_desde_item`, `_texto_estructura_orden`; contador corrido en `_procesar_confirmacion`
  - `presupuestos/pdf_descriptions.py` — `describir_estructura`, `build_dibujo_estructura`, `texto_modulo_estructura`, desvío en `build_pdf_item_context`
  - `presupuestos/templates/presupuestos/detalle.html` — botones, modo módulo del `CotizadorModal` (`window.__cotizadorModulo`), `window.AkunUI`, miniaturas, desglose, `editarItemBtn` hacia `__estructuraEditar`, Escape con modales apilados, `elevacion.js?v=3`, encabezado con número de presupuesto sin cortes
  - `presupuestos/templates/presupuestos/pdf.html` — anexo con `svgDibujo`, figura de estructura a ancho completo (`max-height:440px`)
  - `static/js/elevacion.js` — se extrajo `dibujarAbertura(params, {ox, oy, size, apertura, composicion, idPrefijo})`; `svgElevacion` devuelve exactamente lo mismo (859/859 casos)
  - `pricing/tests.py`, `presupuestos/tests.py`

## Decisiones técnicas

Ver [ADR-022](../team/decisions.md). Resumen:

- Ítem con `resultado_json['tipo'] = 'estructura'` + `version`, sin modelo ni migración. Los lectores existentes (recargo de renovación) leen `precio_unitario_base` del primer nivel y siguen andando. `ItemPresupuesto.ancho_mm/alto_mm` = envolvente del conjunto.
- Lista blanca de config por módulo; medidas, tratamiento y margen los inyecta el servidor. Se ignora cualquier precio del navegador.
- Cada módulo pasa por el mismo serializer que el cotizador suelto (error "Módulo M2: ...").
- Geometría duplicada en Python y JS con fixtures compartidos.
- El `descripcion_manual` de cada módulo nunca lleva la palabra "estructura" (`pricing/tipologia.py` la clasificaría `no_dibujo`).
- Línea común obligatoria. Se reutiliza el cotizador en modo módulo en vez de duplicarlo.
- Numeración corrida de las órdenes de fabricación.

## Pruebas realizadas

- Suite `pricing presupuestos plantillas usuarios`: 424 tests; solo las 4 fallas preexistentes de baseline (3 `MarcoViewsTest` + 1 `OpcionalesListViewTest` premarcos).
- ~49 tests nuevos: geometría con fixtures, cálculo, unión con fórmula y prorrateo, validaciones, payloads mal formados, endpoint 200/400/403/302, alta, renovación, PVC rechaza, editar, bloqueado, ítem ajeno 404, PDF, confirmar 1 ítem + 1 estructura de 3 módulos = 4 órdenes consecutivas, UI.
- `audit_cotas.mjs` y `audit_estructura.mjs` OK.
- Chrome real (SQLite local con catálogo inventado): 14 escenarios OK (armado, arrastre con imán, junta con perfil, solape bloquea guardar, guardar, desglose, editar sin duplicar, renovación +30.000 una vez, Escape apilado, PDF, confirmar con órdenes M1..M3 consecutivas, celular 390 px sin scroll horizontal, SweetAlert al eliminar abertura, cotizador normal sin cambios).
- Reviewer: aprobado sin bloqueantes; se corrigieron sus 2 observaciones (test de permisos exacto y validación de tirantes/opcionales mal formados que daban 500).
- **No probado aún con el catálogo real de producción** (el catálogo legacy solo existe allá).

## Pendiente / Etapa 2

- Cotas encadenadas y antepechos, flechas del teclado, duplicar abertura, aviso de separaciones menores a 5 mm.
- Fuera de alcance: 3D, PVC, terciarizados, esquineros/L, plantillas reutilizables, estructuras en el cotizador suelto, croquis en el PDF de la orden.
- Prueba manual con el catálogo real tras el deploy.
- Deuda detectada (ver backlog): rutas sin registrar en `access_control.py`, ícono `fa-arrow-up-arrow-down` inexistente, `ast.Num` en `formula_parser.py`.
