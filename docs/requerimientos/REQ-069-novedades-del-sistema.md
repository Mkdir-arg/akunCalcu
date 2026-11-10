# REQ-069 — Novedades del sistema generadas desde GitHub
**Estado**: Implementado
**Fecha**: 2026-11-10
**Solicitante**: Dueño / desarrollo

## Descripción de la idea
Cada vez que un cambio llega a `main` (merge de un PR **o** push directo), se crea solo un **borrador de noticia**.
Un administrador lo revisa, corrige el texto y lo publica (o lo descarta si es algo interno). El equipo ve las
novedades publicadas al entrar al sistema y en una página «Novedades».

Maqueta aprobada: https://claude.ai/artifact/DzPNvjaUNwRdqF1vjN6yoG (aviso al entrar, página Novedades, bandeja
del admin, circuito).

## Decisiones tomadas (2026-11-10)
1. **Disparador = «llegó un cambio a `main`»**, no «se abrió un PR». El repo tiene solo 8 PRs en total (el último en
   julio de 2026); casi todo entra por push directo. Un disparador solo de PR casi nunca se activaría.
2. **Borrador con revisión obligatoria.** Nada se publica solo: el texto de un commit/PR es técnico («xhtml2pdf»,
   «tests») y hay cambios internos que el equipo no debe ver.
3. **Cada usuario ve solo las noticias de los módulos a los que tiene acceso** (según `usuarios/access_control.py`).
   Las noticias sin módulo («General») las ven todos.

## Problema que resuelve
Las funciones nuevas salen a producción y el equipo no se entera (ej. el botón «Medición» de FEAT-050). Hoy se avisa
por WhatsApp, a mano, o no se avisa. Lo que no se conoce no se usa.

## Usuarios beneficiados
- **Todo el equipo de Akuna:** lee las novedades al entrar, una vez por cada entrega (varias por semana).
- **Administrador:** revisa y publica los borradores (unos minutos por entrega).

## Valor para el negocio
Las funciones que se construyen se usan desde el día uno. Queda un historial legible de qué cambió y cuándo, útil
para capacitar y para responder «¿desde cuándo hace esto el sistema?». Sin esto, el esfuerzo de desarrollo se
desaprovecha hasta que alguien lo descubre por casualidad.

## Funcionalidad esperada
**A. Generación automática (GitHub → Django)**
- GitHub Action (`.github/workflows/novedades.yml`, nueva: el repo hoy no tiene `.github/`) en `push` a `main`.
- Envía a `POST /novedades/api/borrador/` con header secreto (env `NOVEDADES_BOT_SECRET`, patrón de
  `X-Bot-Secret` ya usado en pedidos y backups): SHA, rango de commits, mensajes, autor, fecha y número de PR si
  el push vino de un merge.
- Idempotente por SHA (reenvíos no duplican).
- Si los mensajes mencionan `FEAT-XXX` o `FIX-XXX`, el borrador toma el texto de usuario de esa entrada del
  `docs/team/changelog.md` (ya está escrito para el equipo). Si no, queda el texto técnico para reescribir.

**B. Bandeja del admin**
- Lista de borradores, publicadas y descartadas, con origen (PR/push/SHA).
- Vista lado a lado: lo que llegó de GitHub / título, texto, módulo y tipo (Nuevo · Mejora · Arreglo).
- Acciones: Publicar, Descartar (interno), Editar una publicada, Crear noticia a mano.
- Solo staff / permiso específico.

**C. Lectura para el equipo**
- Modal «Hay N novedades desde tu última visita» al entrar, una vez por persona; «Entendido» marca como leídas.
- Contador en el ítem «Novedades» del menú lateral.
- Página «Novedades»: agrupada por mes, filtro por tipo, link «Ir a [módulo]».
- Filtrado por módulos accesibles del usuario (decisión 3).

## Viabilidad técnica
Viable con el stack actual. Lo único nuevo es la GitHub Action (y el secreto en GitHub + Railway). El patrón del
endpoint con secreto ya existe (pedidos, backups, salud). El aviso al entrar se resuelve con un context processor
o un include en `core/base.html`.

## Apps / módulos afectados
- **Nueva app `novedades`**: models `Noticia` (estado, tipo, módulo, origen, sha único, textos) y `LecturaNoticia`
  (usuario + noticia, o «última visita» por usuario), vistas, API, templates.
- `core/base.html` (contador en el menú + modal).
- `usuarios/access_control.py` (mapear módulo → permiso para filtrar).
- `security` (eximir el path de la API en `SECURITY_EXEMPT_PREFIXES` / `AuditMiddleware.EXCLUDED_PATHS`, como
  backups).
- `.github/workflows/novedades.yml` (nuevo).
- Requiere migración: sí (app nueva).

## Complejidad estimada
**Mediano** — unos 2 a 3 días con tests.

## Riesgos
- **Secreto expuesto:** el historial del repo ya filtró un secreto antes (TELEGRAM_BOT_SECRET). El secreto va solo en
  GitHub Secrets y en Railway, nunca en el repo.
- **El changelog no está en el contenedor o cambia de formato:** el parseo de `FEAT-XXX` debe fallar suave (dejar el
  texto técnico) y no romper el endpoint.
- **Commits «asd» desde el IDE:** generan borradores vacíos de sentido → se descartan con un clic; considerar
  agrupar los pushes del mismo día en un solo borrador.
- **Railway caído o en deploy** cuando GitHub llama: la Action debe reintentar o registrar el fallo.

## Preguntas abiertas
- ¿Agrupar varios pushes del mismo día en un solo borrador, o uno por push?
- ¿Quién publica: solo superusuario, o un permiso «Publicar novedades» asignable?
- ¿Cargar de una vez las novedades históricas desde el changelog (FEAT-042 en adelante) o arrancar vacío?

## Derivó en
[FEAT-053](../features/FEAT-053-novedades-del-sistema.md) (2026-11-10). Respuestas a las preguntas abiertas: un borrador por push, la bandeja exige acceso total (no `is_staff`), se arranca vacío.
