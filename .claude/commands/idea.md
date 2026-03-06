# Comando /idea

Activa el equipo funcional (Product Owner + Arquitecto) para explorar una idea en profundidad y documentarla como requerimiento. No se escribe código.

---

## Instrucciones para el agente

Cuando el usuario ejecuta `/idea [descripción libre]`, seguir este proceso:

---

### FASE 1 — Product Owner analiza el valor

Leer primero:
- `docs/requerimientos/_INDEX.md` — para asignar el próximo número REQ
- `docs/team/backlog.md` — para ver si ya existe algo relacionado

Presentar al usuario:

**Entendimiento de la idea:**
Reformular la idea en una o dos oraciones claras.

**Problema que resuelve:**
¿Qué dolor o ineficiencia elimina?

**Usuarios beneficiados:**
¿Quién lo usa? ¿Con qué frecuencia?

**Valor para el negocio:**
¿Qué impacto tiene si se implementa? ¿Y si no se implementa?

**Preguntas abiertas (si las hay):**
Cosas que necesitamos definir antes de poder diseñar la solución.

---

### FASE 2 — Arquitecto evalúa la viabilidad

Antes de opinar, leer el código de las apps que podrían verse afectadas.

Presentar al usuario:

**Viabilidad técnica:**
¿Es posible con el stack actual? ¿Requiere algo nuevo?

**Apps / módulos afectados:**
¿Qué partes del sistema tocaría?

**Complejidad estimada:** Pequeño / Mediano / Grande

**Dependencias o riesgos:**
¿Hay algo que podría complicar la implementación?

**Alternativas técnicas (si aplica):**
Si hay más de una forma de hacerlo, describirlas brevemente.

---

### FASE 3 — Documentador crea el requerimiento

Con la información de las dos fases anteriores, crear el archivo:
`docs/requerimientos/REQ-XXX-nombre-corto.md`

Usar este formato:
```markdown
# REQ-XXX — Nombre del requerimiento
**Estado**: Aprobado
**Fecha**: YYYY-MM-DD
**Solicitante**: [rol/área]

## Descripción de la idea
[Descripción funcional clara]

## Problema que resuelve
[Del análisis del PO]

## Usuarios beneficiados
[Del análisis del PO]

## Valor para el negocio
[Del análisis del PO]

## Viabilidad técnica
[Del análisis del Arq]

## Apps / módulos afectados
[Del análisis del Arq]

## Complejidad estimada
[Pequeño / Mediano / Grande]

## Preguntas abiertas
[Las que quedaron sin resolver, si las hay]

## Derivó en
_Pendiente — usar /feature REQ-XXX para iniciar el desarrollo_
```

Luego actualizar `docs/requerimientos/_INDEX.md` agregando la fila del nuevo REQ.

---

### Cierre

Terminar con:
"Requerimiento **REQ-XXX** documentado en `docs/requerimientos/`. Cuando quieras arrancar el desarrollo, usá `/feature REQ-XXX`."
