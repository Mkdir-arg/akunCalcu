# FEAT-058 — Sección «Agente»: configuración del asistente de clientes

**Estado:** Implementado
**Fecha:** 2026-11-11
**Requerimiento:** [REQ-075](../requerimientos/REQ-075-atencion-automatica-clientes-omnicanal.md) — Etapa 1a
**ADR:** [ADR-032](../team/decisions.md)

## Qué hace

Agrega al menú, en el grupo **Operación** debajo de Solicitudes, la sección **Agente**. Desde
ahí dirección configura cómo va a trabajar el asistente que atiende a los clientes por WhatsApp,
email e Instagram. Esta feature solo deja lista la configuración: el asistente todavía no
conversa (eso llega en la Etapa 1b).

| Opción | Qué se configura |
|---|---|
| **Configuración general** | Nombre con el que firma, indicaciones de tono, modelo de IA de OpenAI, canales prendidos o apagados, modo prueba con los números permitidos, y a quién se derivan los casos que el asistente no resuelve |
| **Horario de atención** | Franjas por día de la semana (varias por día) y días cerrados (feriados, vacaciones) |
| **Visitas técnicas** | Técnicos que hacen la medición: franjas disponibles, zonas que cubren, duración de la visita, cupo por franja y costo (0 = sin costo) |
| **Base de conocimiento** | Temas y textos que el asistente puede afirmar (zonas, plazos, garantía, formas de pago), con buscador y paginación |

Valores iniciales de la configuración general: firma **Matías Fariña**, modelo **`gpt-5-mini`**,
**los tres canales apagados** y **modo prueba activado**. Nada se prende solo.

## Criterios de aceptación

| Criterio | Estado |
|---|---|
| Menú «Agente» con 4 opciones, cada una con su permiso propio y asignable por rol | ✅ |
| Sin sesión redirige al login; sin permiso redirige con el mensaje «No tiene permisos» (como el resto del sistema) | ✅ |
| Configuración general única con valores por defecto (firma, modelo, canales apagados, modo prueba) | ✅ |
| Horario: franjas con inicio menor que fin y sin superponerse el mismo día; días cerrados con fecha y motivo | ✅ |
| Visitas: solo usuarios activos como técnicos, con franjas, zonas, duración, cupo y costo | ✅ |
| Base de conocimiento: buscador, paginación cada 20, alta, edición, desactivación y borrado con SweetAlert2 | ✅ |
| Pantallas con el design system «Taller», extendiendo `core/base.html` | ✅ |
| Modelos con migración, `verbose_name` y `__str__`; tests de modelos, vistas y permisos | ✅ |
| No cambia nada de lo existente | ✅ |

## Archivos

**Nuevos — `akuna_calc/agente/`**
- `models.py`: `ConfiguracionAgente` (registro único pk=1, `obtener()`), `FranjaAtencion`, `DiaCerrado`,
  `TecnicoVisita`, `FranjaTecnico`, `ZonaTecnico`, `EntradaConocimiento` y `normalizar_numeros()`.
- `migrations/0001_initial.py`.
- `forms.py`: formularios y formsets de franjas y zonas del técnico, con validación de superposición y de
  localidades repetidas.
- `views.py`, `urls.py` (namespace `agente`, prefijo `/agente/`), `admin.py`, `apps.py`, `tests.py` (23 tests).
- `templates/agente/`: `configuracion.html`, `horario.html`, `franja_form.html`, `tecnico_list.html`,
  `tecnico_form.html`, `conocimiento_list.html`, `conocimiento_form.html` y los parciales `_campo.html` y `_check.html`.

**Modificados**
- `akuna_calc/akuna_calc/settings.py`: `agente` en `INSTALLED_APPS`.
- `akuna_calc/akuna_calc/urls.py`: ruta `/agente/`.
- `akuna_calc/usuarios/access_control.py`: módulo `agente` en `ACCESS_MODULES` y `SIDEBAR_GRUPOS`, con los
  códigos `agente.configuracion`, `agente.horario`, `agente.visitas` y `agente.conocimiento`, y el registro de
  las rutas secundarias.

## Decisiones técnicas

- **App propia `agente`**, separada de `solicitudes`: el asistente va a crecer (conversaciones, APIs para n8n,
  cotización) y mezclarlo con el reparto de solicitudes complicaría las dos cosas.
- **Configuración en la base, no en variables de entorno**: dirección cambia firma, tono, modelo, canales y
  horarios desde el sistema, sin tocar n8n ni hacer un deploy. Ver ADR-032.
- **El modelo de IA es un campo de texto**: si OpenAI saca un modelo mejor, o las pruebas muestran que conviene
  otro, se cambia desde la pantalla.
- **Superposición de franjas del técnico**: la valida el formset sobre todas las filas juntas (incluidas las que
  se borran o se cambian en el mismo guardado). Las franjas del horario general la validan contra la base.
- **Zonas como texto**: el sistema no tiene una tabla de localidades (en `Cliente` también es texto). Se
  normalizan los espacios y se comparan sin distinguir mayúsculas.
- **Sin permiso se redirige con mensaje** en lugar de devolver 403, para comportarse igual que el resto del
  sistema (`usuarios.middleware.RouteAccessMiddleware`).

## Puesta en marcha

1. `python manage.py migrate agente`
2. Los usuarios con acceso total ven el menú automáticamente. Al resto hay que asignarles los permisos de
   «Agente» desde Configuración → Usuarios.
3. Cargar el horario de atención, el técnico con sus franjas y zonas, y la base de conocimiento.

## Pendiente

- Probar las pantallas en el navegador: los tests confirman que cargan y guardan, no cómo se ven.
- Etapa 1b de REQ-075: conversaciones, APIs para n8n, separación de números del equipo y de clientes en el
  webhook de Meta, y el asistente respondiendo en modo prueba.
