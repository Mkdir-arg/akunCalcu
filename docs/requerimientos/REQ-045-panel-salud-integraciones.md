# REQ-045 — Panel de salud de las integraciones

- **Estado:** Implementado
- **Derivó en:** [FEAT-035](../features/FEAT-035-panel-salud-integraciones.md)
- **Fecha:** 2026-08-01
- **Origen:** Sesión del 31/07: se encontraron dos bugs y una caída de 25 horas, y los tres estaban invisibles.
- **App principal:** `security` · consume datos de `solicitudes` y de la API de n8n

## Problema

El sistema no tiene forma de decir *"hace X horas que no leo un mail"*. Tres casos reales, todos
descubiertos de casualidad:

| Qué pasó | Cuánto tardó en verse | Por qué nadie lo vio |
|---|---|---|
| La credencial OAuth de Gmail expiró y el reparto dejó de leer la casilla | **25 horas** | Un trigger que no puede leer **no genera ejecución**, así que en n8n no hay nada rojo |
| El backup diario dejó de subir a Google Drive | **9 días** (23/07 al 31/07) | La ejecución sí queda en rojo en n8n, pero nadie entra a mirarla |
| El reparto procesaba 1 mail de cada lote de 20 | Desde que se creó el workflow | Los nodos con `onError: continueRegularOutput` dejan la ejecución en **"success"** |

El costo es directo: en esas 25 horas entraron 7 formularios web, uno de ellos un pedido real de
una clienta que quedó sin atender.

## User Story

```
Como responsable del sistema
quiero ver en una sola pantalla el estado de las integraciones
para detectar en minutos una caída que hoy tarda días en descubrirse
```

## Criterios de aceptación

- [ ] Vista `/security/salud/` con un semáforo por integración: **OK** / **Atención** / **Falla**.
- [ ] Por cada workflow de n8n vigilado se muestra: si está activo, cuándo fue su última ejecución
      y si esa ejecución terminó en error.
- [ ] **Regla de silencio** (la que detecta la caída de Gmail): si un workflow que debería correr
      seguido no registra ejecuciones en más de N horas, el estado pasa a **Falla** con el texto
      "hace X h sin ejecuciones". El umbral N se configura por workflow, porque el reparto corre
      cada minuto y los recordatorios una vez por día.
- [ ] **Estado real del backup en Drive**: se muestra si el último backup llegó efectivamente a
      Drive y hace cuántos días. Hoy Django registra el `Backup` aunque la subida falle, así que
      el panel tiene que reflejar la realidad, no la intención.
- [ ] **Migraciones pendientes** de aplicar en producción, listadas por app. El panel las detecta
      sin aplicarlas.
- [ ] Si n8n no responde, tarda demasiado o falta la API key, el panel muestra esa integración
      como "sin datos" y **el resto de la página sigue funcionando**.
- [ ] Acceso restringido: solo usuarios con acceso total (mismo criterio que el resto de Seguridad).
- [ ] Endpoint JSON con el mismo estado del panel, para que después un workflow pueda consultarlo
      y avisar por WhatsApp sin duplicar la lógica.

## Fuera de alcance (y por qué)

- **"Credenciales por vencer"**: la API de n8n **no expone** el vencimiento ni el estado de una
  credencial OAuth, así que no se puede avisar *antes* de que caduque. Lo que sí se detecta —y es
  lo que importa— es el efecto: el silencio del trigger y el error de la ejecución. La causa de
  fondo ya se atacó publicando la app OAuth de Google, que era lo que hacía caducar los tokens
  cada 7 días.
- **El aviso automático por WhatsApp**: queda para una fase 2. Esta feature deja el endpoint JSON
  listo para que el workflow lo consuma.

## Riesgo que el propio requerimiento tiene que asumir

Un panel hay que ir a mirarlo. El backup a Drive falló 9 días **con el registro visible en n8n** y
nadie lo abrió. Si esta feature termina en un tablero que nadie visita, no resuelve el problema:
por eso el endpoint JSON es criterio de aceptación y no un extra. El aviso proactivo de la fase 2
es lo que realmente cierra el círculo.

## Complejidad estimada

**Grande** — cliente HTTP contra la API de n8n (con timeout y degradación), configuración de los
workflows vigilados y sus umbrales, detección de migraciones pendientes, vista + template, endpoint
JSON y tests.

## Relación con el backlog

No existía como ítem previo. Se agrega como **US-045**.
