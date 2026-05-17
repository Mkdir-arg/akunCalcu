# REQ-025 — Buscador de accesorios en configurador de hojas

- **Estado:** Implementado
- **Fecha:** 2026-05-17
- **Derivó en:** FEAT-010

## Idea original
En la pantalla de edición de hojas (`/pricing/config/hojas/<id>/editar/`), el campo **Accesorio** hoy se usa como un selector tradicional dentro del bloque de accesorios. Se necesita que funcione como un buscador para encontrar accesorios más rápido cuando la lista es larga.

## Contexto
- La mejora aplica al configurador de hojas dentro del módulo Fábrica.
- El problema es de usabilidad: la lista actual dificulta encontrar accesorios puntuales cuando hay muchos registros disponibles.
- El proyecto ya utiliza Select2 desde `core/base.html`, por lo que la mejora debería apoyarse en el patrón de UI existente.

## User Story
> Como **usuario del módulo Fábrica**, quiero **buscar accesorios escribiendo dentro del campo Accesorio al editar una hoja** para **encontrar y seleccionar más rápido el accesorio correcto**.

## Criterios de aceptación
- [ ] En `/pricing/config/hojas/<id>/editar/`, el campo **Accesorio** dentro de la sección de accesorios permite buscar escribiendo texto.
- [ ] La búsqueda filtra los accesorios disponibles por código y/o descripción para agilizar la selección.
- [ ] El usuario puede seguir seleccionando un accesorio existente sin cambiar el flujo actual de guardado.
- [ ] La mejora aplica tanto a filas existentes como a filas nuevas agregadas dinámicamente en la pantalla.
- [ ] No se modifica la lógica de guardado de accesorios de la hoja; solo mejora la interacción de selección.
- [ ] La interfaz mantiene el estilo y componentes ya usados por el sistema.
- [ ] Existe al menos un test que cubra la renderización o el comportamiento esperado de la vista afectada.

## Complejidad estimada
**Pequeño** — Es una mejora de experiencia de uso localizada en una pantalla existente y debería reutilizar componentes ya presentes.

## Relación con backlog
No estaba en el backlog. Se agrega como US-025 al activarse `/feature`.

## Fuera de alcance
- No incluye cambios en otras pantallas del configurador (por ejemplo marcos u otros ABM) salvo que se detecte dependencia técnica obligatoria.
- No incluye alta de accesorios nuevos desde esta pantalla.
- No incluye cambios en modelos ni estructura de base de datos salvo que el análisis técnico demuestre que son necesarios.