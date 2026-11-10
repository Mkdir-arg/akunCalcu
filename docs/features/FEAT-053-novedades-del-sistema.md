# FEAT-053 — Novedades del sistema generadas desde GitHub

**Estado:** Implementado (en `development`, sin commitear)
**Fecha:** 2026-11-10
**Requerimiento:** [REQ-069](../requerimientos/REQ-069-novedades-del-sistema.md)
**ADR:** ADR-029
**Maqueta:** https://claude.ai/artifact/DzPNvjaUNwRdqF1vjN6yoG

## Qué hace

Cada cambio que llega a `main`, sea por push o por merge de un PR, deja un **borrador de noticia** en el
sistema. Un administrador lo revisa, lo reescribe para el equipo y lo publica, o lo descarta si es interno.
El equipo ve lo publicado de tres formas:

- **Ventana al entrar:** «Hay N novedades desde tu última visita», con hasta 5 noticias y los botones «Ver todas»
  y «Entendido». «Entendido» las marca como leídas y vuelve a la misma página.
- **Contador en el menú:** el grupo «Sistema AKUN» → «Novedades» muestra cuántas hay sin leer.
- **Página Novedades** (`/novedades/`): agrupa por mes, filtra por tipo (Nuevo, Mejora o Arreglo), pagina de a 20 y
  tiene un enlace «Ir a [módulo]». Al abrirla sin filtro, en la primera página, marca todo como leído.

Cada persona ve las noticias **generales** y las de los **módulos a los que tiene acceso**.

### De dónde sale el borrador

1. La GitHub Action `.github/workflows/novedades.yml` corre en cada push a `main`.
2. El script `.github/scripts/novedad_borrador.py` junta los commits del push. Si el push agregó entradas
   nuevas a `docs/team/changelog.md`, usa su título (sin la fecha ni el `FEAT-XXX:`) y su texto, que ya
   están escritos para el equipo. Si no hay entradas nuevas, usa el asunto del commit y deja el texto vacío.
3. Lo manda a `POST /novedades/api/borrador/` con el header `X-Bot-Secret`.
4. Django crea la noticia en **Borrador**. Si llega dos veces el mismo commit, no la duplica.

### Bandeja del admin (`/novedades/bandeja/`)

Pestañas Borrador / Publicada / Descartada / Todas. Al revisar una noticia se ve a la izquierda lo que
llegó de GitHub y a la derecha el formulario con título, texto, tipo y módulo, más los botones Guardar,
Publicar y Descartar. Hay un botón para crear una noticia a mano. Solo entra quien tiene **acceso total**
(superusuario o rol con acceso total).

## Criterios de aceptación

- [x] Cuando llega un cambio a `main`, sea por push o por PR, se crea un borrador.
- [x] Si se reenvía el mismo SHA, no se duplica.
- [x] Si el push trae entradas nuevas del changelog, el borrador usa ese texto. Si no, queda el texto técnico.
- [x] Una llamada sin secreto o con un secreto incorrecto recibe 403 y no crea nada. Un secreto con caracteres raros también recibe 403, no 500.
- [x] La bandeja muestra borradores, publicadas y descartadas con su origen (PR o push y SHA).
- [x] El admin edita título, texto, módulo y tipo, publica o descarta, y crea noticias a mano.
- [x] Solo entra quien tiene acceso total. Los demás reciben 403. *Cambio respecto del Paso 1, que decía staff: ver Decisiones.*
- [x] Ventana al entrar después de una publicación nueva. «Entendido» la marca como leída y no vuelve a aparecer.
- [x] El contador del menú muestra las no leídas.
- [x] La página Novedades agrupa por mes, filtra por tipo y pagina.
- [x] Cada persona ve solo las noticias de sus módulos y las generales.

## Archivos

| Archivo | Cambio |
|---|---|
| `akuna_calc/novedades/` | App nueva. Models `Noticia` y `LecturaNovedades`, migración `0001_initial`, `services.py` (visibilidad, no leídas, publicar), `context_processors.py`, forms, views, urls, admin, 3 templates y tests |
| `.github/workflows/novedades.yml` | Action en push a `main` (primera Action del repo) |
| `.github/scripts/novedad_borrador.py` | Arma el borrador con los commits y el changelog y lo envía. Reintenta 3 veces |
| `akuna_calc/akuna_calc/settings.py` | App en `INSTALLED_APPS` y context processor |
| `akuna_calc/akuna_calc/urls.py` | Ruta `novedades/` |
| `akuna_calc/usuarios/access_control.py` | `novedades:api_borrador` en `PUBLIC_ROUTE_KEYS` |
| `akuna_calc/security/middleware.py` | `/novedades/api/` exenta de seguridad y auditoría, como backups |
| `akuna_calc/core/templates/core/base.html` | Grupo «Sistema AKUN» en el menú y ventana de aviso |

## Decisiones técnicas

- **ADR-029:** el texto para el equipo lo extrae la Action del changelog, porque el contenedor no tiene `docs/`.
  La publicación siempre pasa por revisión.
- **Disparador = push a `main`**, no apertura de PR: el repo casi no usa PRs (8 en total).
- **Lo no leído se calcula por fecha**: cada usuario guarda una sola fecha de última visita, en vez de una fila
  por noticia leída. Un usuario sin registro cuenta desde su alta, así no recibe todo el historial.
- **La bandeja exige acceso total, no `is_staff`.** El Paso 1 decía staff, pero `usuarios/forms.py` pone
  `is_staff` a cualquiera que tenga un permiso heredado, como «Vidrios». Con `is_staff`, un operario podría
  publicar avisos para toda la empresa. Lo encontró el Reviewer.
- **El context processor no puede romper ninguna página**: ante cualquier error devuelve 0 y lo registra en el log.
  No muestra la ventana en respuestas a un POST, para no perder un formulario con errores.
- **Al volver a publicar una descartada se toma la fecha nueva**, así vuelve a avisar.

## Tests

43 en `novedades`: `tests.py` (modelos, API, visibilidad por módulo, context processor, vistas del
equipo y del admin, y las correcciones del Reviewer) y `tests_script.py` (parseo del changelog, erratas,
número de PR, force-push). `tests_script.py` se saltea si `.github/` no está, como en el contenedor.
Junto con core, usuarios, security, solicitudes, presupuestos, agenda y gastos_diarios: **580 tests OK**.

## Configuración pendiente (la hace el dueño)

1. Railway → servicio `web` → variable `NOVEDADES_BOT_SECRET` (un valor largo al azar).
2. GitHub → Settings → Secrets and variables → Actions:
   - `NOVEDADES_BOT_SECRET`: el mismo valor.
   - `NOVEDADES_URL`: `https://<dominio de prod>/novedades/api/borrador/`.

Sin esos secrets, la Action termina en verde y no envía nada.

## Pendientes

- No se probó en el navegador.
- Primera Action del repo: confirmar en GitHub → Actions que corre en el primer push a `main`.
