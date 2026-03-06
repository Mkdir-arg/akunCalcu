# Comando /hotfix

Activa el equipo para un parche urgente en producción. Flujo mínimo: sin análisis extendido, máxima velocidad.

Flujo: Desarrollador → Reviewer → Documentador

---

## Instrucciones para el agente

Cuando el usuario ejecuta `/hotfix [descripción del problema en producción]`, seguir este proceso:

---

### PASO 1 — Desarrollador diagnostica e implementa

Leer el código afectado. Identificar la causa raíz y aplicar el fix mínimo necesario.

**NO refactorizar. NO mejorar código cercano. Solo resolver el problema puntual.**

Presentar al usuario:
- Causa raíz identificada
- Cambio aplicado (diff o descripción)
- Archivos modificados

Terminar con: "¿Procedemos con la revisión?"

**ESPERAR RESPUESTA DEL USUARIO ANTES DE CONTINUAR.**

---

### PASO 2 — Reviewer verifica (solo si Paso 1 aprobado)

- [ ] El fix resuelve el problema reportado
- [ ] No introduce regresiones obvias
- [ ] Es el cambio mínimo necesario (no hay efectos colaterales)

Si todo está bien → avanzar al Paso 3.
Si hay problemas → volver al Paso 1.

---

### PASO 3 — Documentador registra (solo si Paso 2 aprobado)

1. Agregar entrada en `docs/hotfix/_LOG.md` con formato:
   ```
   ### HFX-XXX — Título
   **Fecha**: YYYY-MM-DD
   **Urgencia**: [por qué no podía esperar]
   **Feature afectada**: FEAT-XXX o módulo

   **Síntoma en producción**: [qué estaba roto]
   **Causa raíz**: [por qué ocurría]
   **Solución aplicada**: [qué se cambió]
   **Archivos modificados**: [lista]
   **Seguimiento**: ¿Requiere fix más profundo en el próximo sprint? Sí/No
   ```

Terminar con: "Hotfix **HFX-XXX** registrado. Si requiere seguimiento, agendarlo en el backlog."
