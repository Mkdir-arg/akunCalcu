# Comando /fix

Activa el equipo para corregir un bug en ciclo normal (dentro de sprint). Flujo liviano: sin Product Owner, sin sprint planning.

Flujo: Arquitecto → Desarrollador → Reviewer → Documentador

---

## Instrucciones para el agente

Cuando el usuario ejecuta `/fix [descripción del bug]`, seguir este proceso:

---

### PASO 1 — Arquitecto diagnostica

Leer el código relevante antes de opinar.

Presentar al usuario:

**Descripción del bug:**
Reformular el síntoma claramente.

**Causa raíz identificada:**
¿Dónde está el problema exactamente?

**Archivos a modificar:**
Lista de archivos afectados.

**Solución propuesta:**
Qué se va a cambiar y por qué.

**¿Requiere migración?** Sí/No

**Riesgos:** ¿Puede afectar algo más?

Terminar con: "¿Aprobamos este diagnóstico y procedemos con el fix?"

**ESPERAR RESPUESTA DEL USUARIO ANTES DE CONTINUAR.**

---

### PASO 2 — Desarrollador implementa (solo si Paso 1 aprobado)

Implementar el fix siguiendo las convenciones de `CLAUDE.md`.
No corregir nada más allá del bug reportado.

Escribir un test que reproduzca el bug y verifique que está corregido:
```python
def test_fix_nombre_del_bug(self):
    # Setup que reproduce el bug
    # Verificar que ya no ocurre
```
Correr: `docker-compose exec web python manage.py test nombre_app`

Mostrar lista de archivos modificados y resultado de los tests.

Terminar con: "¿Procedemos con la revisión?"

**ESPERAR RESPUESTA DEL USUARIO ANTES DE CONTINUAR.**

---

### PASO 3 — Reviewer verifica (solo si Paso 2 aprobado)

- [ ] El test escrito reproduce el bug y pasa con el fix aplicado
- [ ] `docker-compose exec web python manage.py test nombre_app` pasa sin errores
- [ ] El fix resuelve el síntoma sin introducir regresiones
- [ ] No se modificó código fuera del alcance del bug
- [ ] Si hubo migración → existe el archivo
- [ ] Seguridad: no se introdujeron vulnerabilidades

Si todo está bien → avanzar al Paso 4.
Si hay problemas → reportar y volver al Paso 2.

---

### PASO 4 — Documentador registra (solo si Paso 3 aprobado)

1. Agregar entrada en `docs/fixes/_LOG.md` con formato:
   ```
   ### FIX-XXX — Título
   **Fecha**: YYYY-MM-DD
   **Severidad**: Baja / Media / Alta
   **Feature afectada**: FEAT-XXX o módulo

   **Síntoma**: [qué veía el usuario]
   **Causa raíz**: [por qué ocurría]
   **Solución**: [qué se cambió]
   **Archivos modificados**: [lista]
   ```
2. Si el fix modifica comportamiento documentado en algún `docs/features/FEAT-XXX.md` → actualizar ese archivo.

Terminar con: "Fix **FIX-XXX** registrado en `docs/fixes/_LOG.md`."
