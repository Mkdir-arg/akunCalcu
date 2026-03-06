# REQ-004 — Sistema de Fórmulas para Marcos

> Estado: En desarrollo
> Fecha: 2026-03-06
> Derivó en: —

## Descripción

Al configurar un Marco, el administrador debe poder agregar múltiples fórmulas de perfiles que definan cómo calcular las dimensiones de los perfiles necesarios para fabricar ese marco.

## User Story

Como administrador, quiero agregar fórmulas de perfiles al configurar un Marco
para definir automáticamente las dimensiones de los perfiles necesarios para fabricar ese marco.

## Criterios de Aceptación

- [ ] CA-1: Al crear/editar un Marco, se muestran los campos Extrusora, Línea y Producto
- [ ] CA-2: Debajo de los campos del marco existe una sección "Fórmulas de Perfiles" con un botón "Agregar Fórmula"
- [ ] CA-3: Cada fórmula tiene los campos: Cantidad (entero), Variable (Alto/Ancho), Operador (+/-/*/÷), Valor (número), Ángulo (texto), Perfil (código), y botón Eliminar
- [ ] CA-4: La fórmula se construye y muestra visualmente como "Alto - 500" o "Ancho + 45"
- [ ] CA-5: El selector de Perfil muestra la lista completa de perfiles disponibles (vía API)
- [ ] CA-6: Al guardar el Marco, se persisten todas las fórmulas en `despiece_perfiles_marcos` con FK al marco
- [ ] CA-7: Al editar un Marco existente, las fórmulas guardadas se cargan en la tabla
- [ ] CA-8: Al guardar en modo edición, se eliminan las fórmulas anteriores y se insertan las nuevas
- [ ] CA-9: No hay errores silenciosos — si algo falla al guardar, el usuario recibe un mensaje claro

## Complejidad

Mediano

## Contexto técnico

- La tabla `despiece_perfiles_marcos` fue creada manualmente con SQL (no via migración Django)
- El modelo Django ya existe pero apunta a esa tabla — necesita verificarse
- La API `/pricing/api/pricing/perfiles/` debe retornar perfiles para el selector
- Al guardar, se hace delete + insert (no update por fórmula)

## Relacionado con

- US-003 / REQ-003 — CRUD Fábrica ABM (extiende la configuración de Marcos)
