# FEAT-037 — Aperturas configurables por producto y por ítem

- **Estado:** Implementado
- **Fecha:** 2026-09-03
- **Requerimiento:** [REQ-047](../requerimientos/REQ-047-aperturas-configurables.md)
- **ADR:** [ADR-019](../team/decisions.md)
- **Apps:** `pricing` (catálogo, modelo, ABM, APIs) · `presupuestos` (cotizador, snapshot, PDF)
- **Commits:** `42c1fb9` (catálogo, modelo, migración, APIs, símbolos 2D, color) · `7a7d4bb` (campo Apertura en el cotizador) · `321bad3` (visor 3D)

## Qué hace

El sistema ya sabía la *familia* de una abertura (corrediza, batiente, paño fijo…) pero no **cómo
abre cada ítem**: lado de la bisagra, sentido de cada hoja, carril. Ahora:

1. En el **ABM de productos** hay un selector múltiple **"Aperturas admitidas"** con el catálogo
   completo de 11 aperturas. Un producto sin ninguna marcada sigue funcionando: el cotizador
   ofrece todas las compatibles con su tipología.
2. En el **cotizador** aparece el bloque **Apertura**: el tipo (solo las admitidas por el producto),
   el **lado de bisagra** cuando aplica, y para corredizas el **movimiento y el carril de cada hoja**,
   con un default razonable. Se guarda con el ítem y se restaura al editarlo.
3. El **visor 3D** sigue la apertura: bisagra del lado elegido, hojas móviles según su movimiento,
   y el modo de apertura (basculante, proyectante) según el tipo aunque la familia sea genérica.
4. La **elevación 2D** dibuja el símbolo técnico de cada apertura y pinta el perfil con el color
   de la **terminación**. El **PDF** muestra ambos en el plano de cada ítem.

## Catálogo

| Código | Nombre | Símbolo | Hojas | Dato extra |
|---|---|---|---|---|
| `pano_fijo` | Paño fijo | ninguno | 1 | — |
| `corrediza` | Corrediza | flecha por hoja + Int./Ext. | 2, 3, 4, 6 | movimiento y carril por hoja |
| `abrir_1` | Paño de abrir 1 hoja | diagonales al lado opuesto a la bisagra | 1 | lado |
| `abrir_2` | Paño de abrir 2 hojas | diagonales convergiendo al centro | 2 | — |
| `oscilobatiente` | Oscilobatiente | lateral + vértice arriba | 1 | lado |
| `banderola` | Banderola | triángulo, vértice arriba | 1 | — |
| `brazo_empuje` | Brazo de empuje | triángulo, vértice abajo | 1 | — |
| `proyectante_tijera` | Proyectante con tijera | rombo | 1 | — |
| `puerta` | Puerta 1 hoja | diagonales al lado opuesto a la bisagra | 1 | lado |
| `puerta_doble` | Puerta 2 hojas | diagonales convergiendo al centro | 2 | — |
| `puerta_corrediza` | Puerta corrediza | flecha por hoja + Int./Ext. | 2, 3 | movimiento y carril por hoja |

**Convención única:** izquierda y derecha son de la abertura **vista de frente**, tal como se
dibuja. "Int./Ext." es otro eje: el carril interior o exterior de una corrediza.

## Cómo está armado

- **`pricing/aperturas.py`** — el catálogo vive en código (son símbolos fijos, no un ABM), con
  `normalizar_apertura()` que limpia lo que viene del cotizador o del snapshot: completa el lado
  por defecto, arma las hojas de una corrediza con el default (pares al carril interior corriendo
  a la derecha, impares al exterior a la izquierda, la última a la izquierda) y devuelve `None`
  ante un código inexistente para que un dato roto no rompa nada. Espejo exacto en
  `static/js/abertura-layout.js`.
- **`ProductoApertura`** — tabla gestionada por Django, FK sin constraint a la tabla legacy
  `productos` (mismo patrón que `VidrioHoja`). Migración `pricing/0007`, `CreateModel` estándar.
- **APIs** — `ProductosListView` y `api_get_producto` devuelven `aperturas` como objetos
  (`codigo, nombre, simbolo, hojas, lado, por_hoja`), resueltas en una sola consulta.
- **Ítem** — `config['apertura']` viaja en `apertura_json`, se normaliza contra las hojas del
  producto en `build_item_snapshot` y queda en `snapshot_item.apertura`. **Sin migración.**
  El serializer de cálculo la acepta y la deja pasar: la apertura no afecta el precio.
- **Dibujo** — `build_dibujo_params` pasa `apertura` y `color_terminacion`; `elevacion.js` dibuja
  el símbolo sobre el vidrio de cada paño y usa la paleta `PERFIL_COLORES` (los mismos hex del
  3D) con un **contorno oscuro fijo** para que un perfil blanco se lea sobre papel.

## Decisiones

1. **No se partió la tipología.** Banderola, brazo de empuje y proyectante con tijera comparten
   familia (`ventana_proyectante`) y malla 3D; la *apertura* carga la distinción. Cero cambios
   en `tipologia.py`, cero productos a reclasificar.
2. **Tabla nueva, no columna en la legacy.** Agregar `aperturas` a `productos` exigía otro
   `ALTER TABLE` a mano (ADR-018). Una tabla gestionada migra sola y es una relación 1-a-N real.
3. **Ítems viejos sin apertura se dibujan sin símbolo**, igual que antes. Nada cambia hasta que
   se elige una apertura.

## Verificación

- 21 tests Django nuevos (catálogo, normalización, modelo, form, API de productos, params de dibujo).
  Suite completa: 370 tests, mismos 25 failures / 9 errors del baseline.
- `audit_cotas.mjs`: los 11 símbolos, espejo del lado de bisagra, Int./Ext. por carril, default
  de 4 hojas, ítems sin apertura, color por terminación y por clave.
- `makemigrations --check`: la migración cierra con el modelo.
- **El visor 3D no se puede probar sin navegador**: solo sintaxis. Primera verificación real en prod.

## Pendiente

- Combinaciones (fijo + abrir, fijo + corrediza): el catálogo queda preparado por propiedades.
- Cargar las aperturas admitidas en los productos del catálogo real.
