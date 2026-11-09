# REQ-066 — Animación de bienvenida en el login: la ventana se abre y sale una persona

- **Estado:** En desarrollo
- **Fecha:** 2026-11-09
- **Complejidad:** Pequeño
- **Apps afectadas:** `core` (login)

## User Story

Como **usuario del sistema** quiero que **al ingresar con las credenciales correctas se abra la ventana
del login y salga una persona diciendo «¡Quiero plata, plata, plata!»** para que **el ingreso tenga un
toque de humor de la casa**.

## Decisiones tomadas (usuario)

- **Frecuencia:** en cada login correcto.
- **Celular:** sí, a pantalla completa (hoy el panel de la ventana se oculta en pantallas chicas).
- **Consentimiento:** la persona de la foto está de acuerdo en aparecer.
- **Personaje:** el logo ilustrado que pasó el usuario (persona con campera azul y brazos cruzados), sin el
  círculo celeste de fondo. Se descartaron la foto literal y una mascota dibujada en SVG.
- **Técnica:** animación CSS (no GIF), sin librerías JS/CSS nuevas.
- **Maqueta aprobada (2026-11-09):** https://claude.ai/artifact/RzGxWFZTmj6w8CHYriodyB

## Criterios de Aceptación

- [ ] Con credenciales correctas, las dos hojas de la ventana del login se abren hacia afuera
- [ ] De adentro de la ventana se asoma el personaje del logo, de la cintura para arriba
- [ ] Aparece un globo de diálogo que escribe «¡Quiero plata, plata, plata!»
- [ ] Al terminar (3 a 4 s) entra solo a la pantalla que le corresponde al usuario (`next` o su módulo por defecto)
- [ ] Un clic o una tecla saltea la animación y entra al instante
- [ ] En celular la animación se ve a pantalla completa
- [ ] Con credenciales incorrectas, usuario bloqueado o sin módulos asignados, NO hay animación (comportamiento actual)
- [ ] Con «reducir movimiento» activado en el sistema operativo, se muestra la frase sin animar y entra igual
- [ ] Tests: login correcto muestra la animación con la URL de destino; login incorrecto no la muestra
