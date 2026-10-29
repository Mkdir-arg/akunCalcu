# Brief: rediseño «Taller» (Fase 1, un agente por módulo)

La Fase 0 ya está en `development`: shell nuevo (`core/base.html`), `static/css/taller.css`, includes en
`core/templates/core/ui/` y la infraestructura de tiempo real. Tu trabajo es **solo visual**: llevar los
templates de tu módulo al estilo Taller, sin funciones nuevas.

## Mockups (la ley visual)
`C:\Users\mkdir\AppData\Local\Temp\claude\c--Users-mkdir-Proyectos-akunCalcu\bf4a3427-2d39-40e2-83d6-637d4daab678\scratchpad\design\project\`
(HTML estáticos `*.dc.html`). Empezá por `Main.dc.html` (sistema visual) y mirá el de tu pantalla.
Si una pantalla no tiene mockup, usá el patrón de listado de `Main.dc.html` §4.

## Reglas
- Tocá SOLO los templates, el `live.py` y los tests de tu app.
- NO toques `core/base.html`, `usuarios/access_control.py`, `static/css/taller.css`, `static/js/live.js`, ni otras apps.
- Conservá `id`, `name`, `data-*`, `action` y los selectores que use el JS de cada form/pantalla. Los forms POST llevan `{% csrf_token %}`.
- No cambies vistas ni lógica, salvo `?partial=1` y `crear_aviso()` donde esté indicado en tu tabla.
- **PDFs e impresión, prohibido tocar:** `presupuestos/pdf.html`, `presupuestos/recibo_blank.html`,
  `plantillas/orden_pdf.html`, `comercial/recibo_pdf.html`, los bloques `@media print` de
  `comercial/reportes/*.html` (la pantalla sí se rediseña) y `static/js/viewer3d.js`, `elevacion.js`, `estructura.js`.
- Un solo botón primario por pantalla; editar/eliminar van en el menú de fila (`kebab_menu`).
- Sin gradiente azul-violeta, sin cabeceras de tabla oscuras. Color solo para estados (siempre con texto).
- Los `<select>` ya tienen Select2 automático desde `base.html`. No lo dupliques.
- Los mensajes de Django ya salen como toast. Para confirmar borrados: `data-taller-delete` (ver kebab) o SweetAlert.
- Bloque nuevo disponible: `{% block title %}Presupuestos{% endblock %}` (se muestra como «Presupuestos · AKUN»).
- Tailwind sigue disponible con tokens: `bg-ground`, `text-ink`, `text-ink-2`, `text-ink-3`, `border-line`,
  `bg-accent`, `text-accent`, `bg-accent-soft`, `text-ok`, `bg-ok-soft`, `text-warn`, `text-danger`, etc.

## Clases de `taller.css`
- Botones: `.btn` + `.btn-primary | .btn-secondary | .btn-ghost | .btn-danger`; `.btn-sm`, `.btn-icon`.
- Superficies: `.card` (`.card-pad`), `.page-head`, `.page-title`, `.page-sub`, `.page-actions`, `.sec-label`, `.muted`, `.strong`, `.num`.
- Estados: `.badge` + `.b-gray | .b-blue | .b-violet | .b-green | .b-amber | .b-red` (con `<span class="dot"></span>`),
  `.chip` (filtro activo), `.tabs` + `.tab` (`.on`, `<span class="cnt">`).
- Tablas: `.tbl` dentro de `.table-wrap`; barra de filtros `.toolbar`; pie `.pager`.
- Campos: `.field` (label + input/select/textarea dentro), `.input`, `.field-hint`, `.field-error`.
- Menú de fila: `.kebab`, `.kebab-menu`, `.kebab-item`; vacío: `.empty`.

Ejemplo de listado:
```django
{% extends 'core/base.html' %}
{% block title %}Presupuestos{% endblock %}
{% block content %}
{% include 'core/ui/page_header.html' with title="Presupuestos" subtitle="Cotizaciones para clientes." action_url=url_crear action_label="Nuevo presupuesto" only %}
<section class="card overflow-hidden" data-live="presupuestos" data-live-partial>
  <div class="toolbar">...filtros...</div>
  <div class="table-wrap"><table class="tbl">
    <thead><tr><th>Número</th><th>Estado</th><th class="num">Total</th><th></th></tr></thead>
    <tbody>
    {% for p in page_obj %}
      <tr>
        <td><a class="strong" href="{{ p.get_absolute_url }}">{{ p.numero }}</a></td>
        <td>{% include 'core/ui/badge.html' with tone="green" label="Confirmado" dot=True only %}</td>
        <td class="num strong">$ {{ p.total }}</td>
        <td class="num">{% include 'core/ui/kebab_menu.html' with kebab_label="Acciones" edit_url=p.url_editar delete_url=p.url_borrar delete_name=p.numero only %}</td>
      </tr>
    {% empty %}
      <tr><td colspan="4">{% include 'core/ui/empty_state.html' with title="Todavía no hay presupuestos" action_url=url_crear action_label="Nuevo presupuesto" only %}</td></tr>
    {% endfor %}
    </tbody>
  </table></div>
  {% include 'core/ui/pagination.html' with page_obj=page_obj query=query_sin_page total_label="presupuestos" only %}
</section>
{% endblock %}
```

## Includes (`core/templates/core/ui/`, usar SIEMPRE con `only`)
- `page_header.html`: `title` (obligatorio), `subtitle`, `action_url`, `action_label`, `action_icon` (FA, default `fas fa-plus`),
  `secondary_url`, `secondary_label`, `secondary_icon`, `back_url`, `back_label`. Cabeceras con más botones: copiá el markup `.page-head`.
- `badge.html`: `label` (obligatorio), `tone` (gray|blue|violet|green|amber|red), `dot` (True), `icon` (FA).
- `empty_state.html`: `title` (obligatorio), `text`, `icon` (FA), `action_url`, `action_label`.
- `kebab_menu.html`: `kebab_label`, `view_url`, `edit_url`, `extra_url` + `extra_label` + `extra_icon`,
  `delete_url` + `delete_name` (confirma con SweetAlert y hace POST con CSRF a `delete_url`; la vista debe aceptar POST).
- `pagination.html`: `page_obj` (obligatorio), `query` (querystring SIN `page`, ej. `q=abc&estado=x`), `page_param` (default `page`), `total_label`.
- `core/includes/table_filters.html` conserva sus parámetros (`table_filter_id`, `show_status_filter`, `compact_filters`, etc.).

## Tiempo real
1. **Declarar la fuente** en `<app>/live.py` (se importa solo al arrancar; no hace falta tocar `core`):
```python
from core.live import register
from .models import Presupuesto

register(
    key='presupuestos',                                  # nombre único global
    queryset=lambda user: Presupuesto.objects.all(),     # f(user) -> QuerySet ya filtrado por lo que ese usuario puede ver
    date_field='updated_at',                             # campo fecha que cambia en cada alta/edición (default 'updated_at')
    permission='presupuestos.view',                      # código(s) de acceso; sin acceso la fuente no se devuelve
)
```
   Firma: `register(key, queryset, date_field='updated_at', permission=None)`. El endpoint hace UNA consulta agregada
   (`Max(date_field)` y `Count`) por fuente. Si el modelo no tiene un campo fecha de modificación, usá el de creación
   (las ediciones no se detectarían, solo altas/bajas por `count`). Agregá índice en el campo solo si la tabla es grande.
2. **Marcar el HTML**:
   - `data-live="presupuestos"` (admite varias: `data-live="a,b"`) en el contenedor. Ante un cambio aparece el banner «Hay cambios · Actualizar».
   - `data-live-partial` en ese mismo elemento: en vez del banner, se recarga su contenido con `fetch(<url actual>?partial=1)`.
     La vista debe devolver, con `?partial=1`, SOLO el HTML interno del contenedor (renderizá un `_tabla.html` y que el template completo lo incluya). No se actualiza si el foco está dentro del elemento.
   - `data-live-edit="presupuestos.presupuesto:{{ obj.pk }}"` (+ opcional `data-live-edit-label="presupuesto"`) en el contenedor de la pantalla de edición:
     muestra «Ramiro también está editando este presupuesto». Formato `app.modelo:pk`.
3. **Avisos (campanita)**: `from core.avisos import crear_aviso`
   `crear_aviso(usuarios, texto, tipo='info', url='')` — `usuarios` es un usuario o una lista/queryset; `tipo` ∈ `info|exito|alerta|error`; devuelve la lista de `Aviso`.
   Llamalo desde la vista o servicio (nunca signals), solo donde tu tabla de la Fase 1 lo pide.

## Tests
Corré los de tu app (y `core` si tocás algo compartido):
```
cd akuna_calc
DJANGO_SETTINGS_MODULE=akuna_calc.settings_test_sqlite ../.venv/Scripts/python.exe manage.py test <tu_app> --noinput
```
Fallas baseline de `main` que NO son tuyas: `comercial` (~24 failures + 6 errors, usuarios sin `PerfilAccesoUsuario`) y `pricing` (tablas legacy `managed=False`). Suite completa en la Fase 0: 25 failures + 9 errors, igual que `main`.

## Qué devolver
Lista de pantallas rediseñadas, lo que no pudiste igualar al mockup, tests agregados/resultado, y commit en tu rama de worktree.
