# REQ-026 — Estandarizar selectores buscables en todo el sistema

- **Estado:** Implementado
- **Fecha:** 2026-05-17
- **Derivó en:** FEAT-011

## Idea original
Tomar como referencia el selector buscador **Tipo de Factura** del reporte de cobranzas (`/comercial/reportes/cobranzas/`) y hacer que todos los selectores del sistema usen ese mismo patrón visual y de interacción.

## Contexto
- Hoy el sistema mezcla selects nativos con selects buscables, lo que genera una experiencia inconsistente entre pantallas.
- En varias vistas existen listas largas donde el patrón buscable reduce tiempo operativo y errores de selección.
- El proyecto ya usa Select2 en la base visual, por lo que la mejora debería consolidarse como estándar reutilizable en lugar de resolverse pantalla por pantalla con variantes.

## User Story
> Como **usuario de AkunCalcu**, quiero **que todos los selectores del sistema se vean y funcionen como el buscador de Tipo de Factura** para **tener una experiencia consistente y encontrar opciones más rápido en cualquier pantalla**.

## Criterios de aceptación
- [x] Los campos `<select>` visibles al usuario en formularios, filtros y pantallas operativas usan el mismo patrón visual e interactivo que el selector de **Tipo de Factura** del reporte de cobranzas, salvo micro-selects inline donde el buscador degrada la legibilidad y quedan excluidos explícitamente.
- [x] El usuario puede buscar escribiendo dentro del selector en los casos operativos generales donde hoy se elige una opción desde un `<select>`.
- [x] La estandarización aplica tanto a selects renderizados al cargar la página como a selects agregados dinámicamente mediante JavaScript.
- [x] Los selects conservan el comportamiento funcional actual: valor seleccionado, validaciones, guardado, filtros y envíos de formularios.
- [x] Los placeholders, estados deshabilitados, ancho visual y limpieza de selección mantienen un criterio uniforme en todo el sistema.
- [x] No se introducen librerías nuevas si el patrón puede resolverse con los componentes ya presentes en el proyecto.
- [x] Existe una forma centralizada o reutilizable de aplicar este comportamiento para evitar implementaciones distintas por módulo.
- [x] Se agregan tests o validaciones automatizadas representativas sobre el patrón común y sobre pantallas con selects dinámicos.

## Complejidad estimada
**Grande** — Afecta múltiples apps, templates, formularios y comportamiento JS transversal, por lo que requiere relevamiento de impacto y una estrategia de adopción consistente.

## Relación con backlog
No estaba en el backlog. Se agrega como US-026 al activarse `/feature`.

## Fuera de alcance
- No incluye rediseñar otros controles que no sean selects, como radios, checkboxes o inputs autocompletables que no dependan de un `<select>`.
- No incluye cambiar catálogos, datos o lógica de negocio detrás de las opciones disponibles.
- No incluye introducir una librería de UI nueva salvo que el análisis técnico demuestre una limitación real del stack actual.
- No incluye convertir micro-selects inline de 2 a 4 opciones cuando el buscador rompe una UI compacta; esos casos deben quedar marcados con `no-select2` de forma explícita.