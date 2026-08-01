# REQ-044 — Orientación de los tirantes divisores (vertical u horizontal)

- **Estado:** Implementado
- **Fecha:** 2026-08-01
- **Derivó en:** [FEAT-034](../features/FEAT-034-orientacion-tirantes-divisores.md)
- **Origen:** Pedido del usuario sobre el cotizador de presupuestos
- **Antecedente:** [REQ-041](./REQ-041-tirantes-divisores-relleno-por-seccion.md) / [FEAT-031](../features/FEAT-031-tirantes-divisores-relleno-por-seccion.md) — la división **vertical** quedó explícitamente fuera del alcance de la v1 ("Fuera de alcance (posible v2)").

## Contexto

Hoy, al activar **"Dividir con tirantes"** en el cotizador, la abertura siempre se divide en **bandas horizontales**: se carga el *alto* de cada sección (arriba → abajo), la suma debe dar el alto de la abertura, y cada tirante es una barra horizontal de longitud = ancho.

Es el caso típico (puerta con vidrio arriba y chapa abajo), pero no cubre las aberturas divididas en **columnas** (por ejemplo un paño fijo partido en dos verticalmente, o un lateral ciego junto a un paño vidriado).

## User Story

> **Como** vendedor que cotiza una abertura con tirantes divisores,
> **quiero** elegir si los tirantes son **horizontales** o **verticales**,
> **para** cotizar y mostrar correctamente las aberturas divididas en columnas, y ver el diagrama 3D reflejando esa división real.

## Criterios de Aceptación

**Configuración**
- [ ] Al activar "Dividir con tirantes" aparece un selector de **orientación**: `Horizontal` (por defecto) / `Vertical`.
- [ ] Con orientación **horizontal** el comportamiento es idéntico al actual: se carga el **alto** de cada sección (arriba → abajo) y la suma debe ser igual al **alto** de la abertura.
- [ ] Con orientación **vertical** se carga el **ancho** de cada sección (izquierda → derecha) y la suma debe ser igual al **ancho** de la abertura.
- [ ] Los textos de ayuda, la unidad del input y el cartel de validación en vivo dicen la dimensión correcta según la orientación.
- [ ] Al cambiar la orientación, las secciones se reinicializan repartiendo la dimensión nueva (no queda una suma inconsistente arrastrada de la orientación anterior).
- [ ] Cada sección sigue eligiendo su material (vidrio del catálogo o material ciego), igual que hoy.

**Cálculo (precio)**
- [ ] El área de cada sección usa la dimensión correcta: horizontal = `ancho_abertura × alto_sección`; vertical = `ancho_sección × alto_abertura`.
- [ ] El perfil del tirante usa la longitud correcta: horizontal = ancho de la abertura; vertical = alto de la abertura.
- [ ] La suma de las áreas de las secciones sigue siendo igual al área total de la abertura en ambas orientaciones.
- [ ] La validación (suma de secciones == dimensión correspondiente, medidas > 0) corre en el cliente **y** en el servidor, igual que hoy.

**Visor 3D**
- [ ] Con orientación vertical el diagrama 3D dibuja las secciones como **columnas** y los tirantes como barras **verticales**; con horizontal se mantiene el dibujo actual (bandas y barras horizontales).
- [ ] Las secciones ciegas se siguen distinguiendo del vidrio en ambas orientaciones.

**Documentos y persistencia**
- [ ] La descripción narrativa del PDF indica la orientación (ej.: *"dividida por 1 tirante vertical en Float 6mm y Chapa"*).
- [ ] La orientación se guarda en el ítem y se reconstruye al editarlo.
- [ ] Los presupuestos e ítems ya guardados (sin orientación) se interpretan como **horizontales** y no cambian de precio ni de dibujo.

**Calidad**
- [ ] Tests de cálculo vertical (área y perfil del tirante), de validación por orientación y de no-regresión del caso horizontal.
- [ ] Los tests existentes de tirantes siguen pasando sin cambios de comportamiento.

## Complejidad estimada

**Mediano** — toca el editor React, el motor de cálculo, el serializer, el snapshot del PDF y el visor 3D, pero sin cambios de base de datos (la configuración de tirantes viaja en JSON, no en columnas).

## Fuera de alcance

- **Grilla** (dividir en filas *y* columnas a la vez): sigue siendo una sola orientación por abertura.
- Tirantes en presupuestos **PVC** (usan precio manual).
- Rebaje por sección.
- Bajar la orientación a la orden de fabricación como dato estructurado.
