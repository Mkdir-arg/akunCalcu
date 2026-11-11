# REQ-072 — Módulo de tareas para empleados
**Estado**: Aprobado
**Fecha**: 2026-11-10
**Solicitante**: Dirección

## Descripción de la idea
Un módulo para asignar tareas a los empleados. Cada tarea tiene responsable, fecha límite y estado
(pendiente → en curso → hecha, o cancelada). Cada empleado ve sus tareas en una pantalla «Mis
tareas» y las marca como hechas. La dirección ve todas.

Cuando el módulo exista, el resumen por WhatsApp (REQ-071) suma un bloque de tareas: hechas,
vencidas y pendientes por responsable.

## Problema que resuelve
Hoy los encargos a los empleados se hacen de palabra o por WhatsApp. No queda registro de qué se
pidió, a quién, para cuándo ni si se hizo. La dirección no puede medir el trabajo de cada empleado
más allá de lo que queda cargado en ventas y presupuestos.

## Usuarios beneficiados
- Dirección: asigna y controla, todos los días.
- Empleados (vendedores, administración, taller, colocadores): ven qué tienen pendiente.

## Valor para el negocio
- Nada encargado se pierde: todo queda con responsable y fecha.
- Se ve quién cumple y quién acumula tareas vencidas, en el sistema y en el resumen del sábado.
- Si no se implementa, el resumen de REQ-071 solo muestra la actividad en el sistema, no los encargos.

## Viabilidad técnica
Se puede con el stack actual, sin librerías nuevas.

Diseño preliminar:
- **App nueva `tareas`**, modelo `Tarea`: título, descripción, responsable (FK `User`), fecha
  límite, estado, prioridad, creada por, fechas de creación y cierre. Vínculo opcional con un
  presupuesto, un cliente o un pedido de fábrica.
- **Vistas (CBV)**: listado general con filtros (responsable, estado, vencidas), «Mis tareas»,
  alta, edición, marcar como hecha.
- **Permisos**: un código nuevo en `usuarios/access_control.py`. Crear y asignar: dirección.
  Ver y cerrar las propias: cualquier usuario con login.
- **Resumen**: el servicio de REQ-071 suma el bloque de tareas.

## Apps / módulos afectados
- Nueva: `tareas` (modelo, migración `tareas/0001`, forms, vistas, urls, templates, tests).
- `usuarios/access_control.py`: permiso nuevo.
- Menú lateral en `core/base.html`.
- `resumenes` (REQ-071): bloque nuevo.

## Complejidad estimada
**Mediano**: unos 5 días de trabajo.

## Dependencias y riesgos
1. **Se superpone con la agenda.** `EventoAgenda` ya tiene los tipos «Pendientes» y «Llamar», que
   funcionan como tareas con fecha. Hay que decidir si se reemplazan, si conviven o si la agenda
   pasa a ser la vista de calendario de las tareas.
2. **Adopción.** Si los empleados no cierran sus tareas, el resumen va a mostrar todo vencido. Hace
   falta que cerrar una tarea sea un solo clic.
3. Conviene implementar REQ-071 primero: el resumen funciona sin este módulo.

## Alternativas técnicas
- **A) App nueva `tareas`** (recomendada): modelo propio, limpio, sin tocar la agenda.
- **B) Extender `EventoAgenda`**: agregar responsable general y el estado «hecho» a los tipos
  «Pendientes» y «Llamar». Sale más rápido (2 a 3 días), pero mezcla tareas internas con visitas a
  clientes y hereda los recordatorios de la agenda.

## Preguntas abiertas
1. ¿Quién puede crear tareas: solo la dirección, o también un empleado para otro?
2. ¿El empleado recibe un aviso por WhatsApp cuando se le asigna una tarea? Eso necesita otra
   plantilla de Meta.
3. ¿Hay tareas que se repiten (todos los lunes, fin de mes)?
4. ¿Qué pasa con los tipos «Pendientes» y «Llamar» de la agenda (riesgo 1)?
5. ¿Hace falta adjuntar archivos o fotos, por ejemplo una foto de la colocación terminada?

## Derivó en
_Pendiente — usar /feature REQ-072 para iniciar el desarrollo (después de REQ-071)_
