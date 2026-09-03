# REQ-047 — Aperturas configurables por producto y por ítem

- **Estado:** Implementado
- **Fecha:** 2026-09-03
- **Complejidad:** Grande
- **Feature:** [FEAT-037](../features/FEAT-037-aperturas-configurables.md)
- **Apps afectadas:** `pricing`, `presupuestos`

## User Story

Como **vendedor que cotiza aberturas** quiero **elegir, para cada ítem, cómo abre la abertura
(tipo de apertura, lado de bisagra, sentido de cada hoja)** entre las aperturas que el producto
admite, para **que el 3D del cotizador, el plano del PDF y la ficha del ítem muestren el
símbolo técnico correcto y el cliente lea sin ambigüedad cómo va a abrir lo que compra**.

Como **administrador del catálogo** quiero **marcar en cada producto qué aperturas admite**
para **que el cotizador solo ofrezca las posibles y no haya que corregir a mano**.

## Contexto

Hoy el sistema conoce la *familia* de la abertura (`Producto.tipo_dibujo` + heurística en
`pricing/tipologia.py`) pero no cómo abre cada ítem: no está guardado el lado de la bisagra,
el sentido de cada hoja corrediza ni en qué carril corre. Por eso la elevación 2D del PDF va
sin flechas de apertura (`apertura: false`) y el 3D usa siempre bisagra izquierda.

Los planos de referencia del usuario muestran que el sentido **varía por ítem** (la misma
corrediza aparece con "Int." a la izquierda en un plano y "Ext." en otro), así que no es una
convención: es un dato del ítem.

## Catálogo de aperturas (completo)

| Código | Nombre | Símbolo 2D | Hojas | Dato extra |
|---|---|---|---|---|
| `pano_fijo` | Paño fijo | ninguno | 1 | — |
| `corrediza` | Corrediza | flecha por hoja | 2, 3, 4, 6 | movimiento y carril (int/ext) por hoja |
| `abrir_1` | Paño de abrir 1 hoja | diagonales al lado opuesto a la bisagra | 1 | lado de bisagra (izq/der) |
| `abrir_2` | Paño de abrir 2 hojas | diagonales convergiendo al centro | 2 | — |
| `oscilobatiente` | Oscilobatiente | triángulo lateral + triángulo vertical superpuestos | 1 | lado de bisagra |
| `banderola` | Banderola | triángulo con vértice arriba | 1 | — |
| `brazo_empuje` | Brazo de empuje | triángulo con vértice abajo | 1 | — |
| `proyectante_tijera` | Proyectante con tijera | rombo | 1 | — |
| `puerta` | Puerta 1 hoja | diagonales al lado opuesto a la bisagra | 1 | lado de bisagra |
| `puerta_doble` | Puerta 2 hojas | diagonales convergiendo al centro | 2 | — |
| `puerta_corrediza` | Puerta corrediza | flecha por hoja | 2, 3 | movimiento y carril por hoja |

Convención única en todo el sistema (documentada en ADR-019): **izquierda y derecha son de la
abertura vista de frente, tal como se dibuja**. "Int./Ext." es otro eje (carril interior o
exterior de una corrediza) y no se mezcla con izquierda/derecha.

## Criterios de Aceptación

- [x] En el ABM de productos hay un **selector múltiple "Aperturas admitidas"** con el catálogo completo
- [x] Un producto sin aperturas configuradas sigue funcionando: el cotizador ofrece todas las compatibles con su tipología
- [x] En el cotizador aparece un campo **Apertura** que ofrece solo las aperturas admitidas por el producto elegido
- [x] Para aperturas con bisagra, el cotizador pide el **lado** (izquierda/derecha)
- [x] Para corredizas, el cotizador permite definir **el movimiento y el carril de cada hoja**, con un default razonable
- [x] La apertura elegida se guarda en el snapshot del ítem y **se restaura al editarlo**
- [x] El **3D** refleja la apertura: bisagra del lado elegido, hojas móviles según el movimiento
- [x] La **elevación 2D** dibuja el símbolo técnico de cada apertura (los 11 del catálogo)
- [x] El **PDF** muestra el símbolo en el plano de cada ítem, y **el color del perfil según la terminación**
- [x] Los ítems anteriores (sin apertura guardada) siguen imprimiendo igual que hoy, sin símbolo
- [x] Tests por cada tipo de apertura y por cada lado (izq/der), en Python y en la auditoría JS

## Fuera de alcance

- Combinaciones (fijo + abrir, fijo + corrediza): el catálogo queda preparado por propiedades, se agregan después
- Cambiar el precio según la apertura: la apertura es dato de dibujo y de fabricación, no de cálculo
