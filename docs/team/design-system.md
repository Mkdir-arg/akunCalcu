# Design System — AkunCalcu («Taller»)

> Referencia obligatoria para cualquier cambio en el frontend. Reescrito el 2026-10-29 (REQ-064 / FEAT-046 / ADR-023);
> reemplaza al sistema anterior (degradé azul-violeta, cabeceras de tabla oscuras).
> Mockups de cada pantalla: [`design/*.dc.html`](./design/). El sistema visual completo está en `design/Main.dc.html`.
> Brief para implementar pantallas: [brief-rediseno-taller.md](./brief-rediseno-taller.md).

---

## Base template

```django
{% extends 'core/base.html' %}
{% load static %}
{% block title %}Presupuestos{% endblock %}   {# se muestra como «Presupuestos · AKUN» #}

{% block content %}
...
{% endblock %}

{% block extra_js %}
{% endblock %}
```

**Nunca** crear un template sin extender `core/base.html` (salvo email o PDF). Los `<select>` ya tienen Select2
automático desde `base.html`: no se duplica.

---

## Tokens

Definidos como variables CSS `--t-*` en `static/css/taller.css` y como colores de Tailwind en el `tailwind.config` inline de `base.html`.

| Token (Tailwind) | Valor | Uso |
|---|---|---|
| `bg-ground` | `#F4F5F7` | fondo de página |
| `text-ink` | `#101828` | texto principal y títulos |
| `text-ink-2` / `text-ink-3` | `#475467` / `#667085` | texto secundario / ayudas |
| `border-line` | `#E4E7EC` | bordes (`line-soft` `#F2F4F7`, `line-strong` `#D0D5DD`) |
| `bg-accent` / `text-accent` | `#1F4FD8` | **único color de acción** (hover `#163BA6`, `accent-soft` `#EEF3FF`) |
| `text-ok` / `bg-ok-soft` | `#067647` / `#ECFDF3` | éxito / estado positivo |
| `text-warn` / `bg-warn-soft` | `#B54708` / `#FFFAEB` | pendiente / atención |
| `text-danger` / `bg-danger-soft` | `#B42318` / `#FEF3F2` | error / eliminación |
| violeta | `#5925DC` / `#F4F3FF` | solo estados (badge `b-violet`) |

Tipografía: Inter (Google Fonts). No se inventan colores ni se usa degradé.

---

## Componentes (`static/css/taller.css`)

- **Botones:** `.btn` + `.btn-primary | .btn-secondary | .btn-ghost | .btn-danger`; `.btn-sm`, `.btn-icon`.
- **Superficies:** `.card` (`.card-pad`), `.page-head`, `.page-title`, `.page-sub`, `.page-actions`, `.sec-label`, `.muted`, `.strong`, `.num` (cifras alineadas a la derecha).
- **Estados:** `.badge` + `.b-gray | .b-blue | .b-violet | .b-green | .b-amber | .b-red` (con `<span class="dot"></span>`), `.chip` (filtro activo), `.tabs` + `.tab` (`.on`, `<span class="cnt">`).
- **Tablas:** `.tbl` dentro de `.table-wrap`; barra de filtros `.toolbar`; pie `.pager`. Cabecera clara, sin fondo oscuro.
- **Campos:** `.field` (label + input/select/textarea), `.input`, `.field-hint`, `.field-error`.
- **Menú de fila:** `.kebab`, `.kebab-menu`, `.kebab-item`. Vacío: `.empty`. Notificación: `.toast`.

## Includes (`core/templates/core/ui/`, usar SIEMPRE con `only`)

| Include | Parámetros |
|---|---|
| `page_header.html` | `title` (obligatorio), `subtitle`, `action_url`, `action_label`, `action_icon` (FA, default `fas fa-plus`), `secondary_url/label/icon`, `back_url`, `back_label` |
| `badge.html` | `label` (obligatorio), `tone` (gray\|blue\|violet\|green\|amber\|red), `dot`, `icon` |
| `empty_state.html` | `title` (obligatorio), `text`, `icon`, `action_url`, `action_label` |
| `kebab_menu.html` | `kebab_label`, `view_url`, `edit_url`, `extra_url` + `extra_label` + `extra_icon`, `delete_url` + `delete_name`, y `delete_label` / `delete_verb` / `delete_icon` (default «Eliminar» / «eliminar» / `fa-trash`; p. ej. «Desactivar» cuando no se borra) |
| `pagination.html` | `page_obj` (obligatorio), `query` (querystring SIN `page`), `page_param`, `total_label` |

**Filas dinámicas de formsets** (ej. franjas y zonas en `agente/tecnico_form.html`): la fila vacía va en un
`<template>` con `empty_form`, se clona reemplazando `__prefix__`, se incrementa `TOTAL_FORMS` y se llama
`window.AkunSelect2.init(filaNueva)` para que sus `<select>` tengan el mismo Select2 que el resto.

Los filtros de listado usan `core/includes/table_filters.html` (`table_filter_id`, `show_status_filter`, `compact_filters`, …).

### Ejemplo de listado

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
      <tr><td colspan="4">{% include 'core/ui/empty_state.html' with title="Todavía no hay presupuestos" only %}</td></tr>
    {% endfor %}
    </tbody>
  </table></div>
  {% include 'core/ui/pagination.html' with page_obj=page_obj query=query_sin_page total_label="presupuestos" only %}
</section>
{% endblock %}
```

---

## Badges por estado

Siempre con texto (el color solo no alcanza). Convención de tonos:

| Tono | Cuándo |
|---|---|
| `gray` | borrador, inactivo, sin dato |
| `blue` | en curso, enviado, informativo |
| `violet` | en proceso intermedio (p. ej. fabricación) |
| `green` | confirmado, cobrado, completado |
| `amber` | pendiente, parcial, atención |
| `red` | cancelado, vencido, error, fallido |

---

## Reglas

1. **Un solo botón primario por pantalla** (`.btn-primary`); el resto `.btn-secondary` o `.btn-ghost`.
2. **Acciones de fila en el kebab** (`kebab_menu.html`), no una columna de botones sueltos.
3. **Éxito = toast.** Los mensajes de Django (`messages`) ya salen como toast.
4. **SweetAlert2 solo para confirmar borrados** (nunca `confirm()` nativo): el kebab lo hace con `data-taller-delete` y hace POST con CSRF, así que la vista debe aceptar POST.
5. Sin degradé azul-violeta, sin cabeceras de tabla oscuras, sin colores inventados.
6. Formularios: conservar `id`, `name`, `data-*` y `action`; `{% csrf_token %}` en todo POST; Django Forms, nunca POST raw.
7. Listados de más de 20 registros paginan con `pagination.html`.
8. **Los PDF y la impresión están fuera del sistema** y no se tocan: `presupuestos/pdf.html`, `presupuestos/recibo_blank.html`, `plantillas/orden_pdf.html`, `comercial/recibo_pdf.html`, el PDF de venta (reportlab), los `@media print` de `comercial/reportes/*.html` y los JS de dibujo `viewer3d.js`, `elevacion.js`, `estructura.js`.
9. No agregar librerías JS/CSS nuevas sin pasar por el Arquitecto y registrar ADR. Disponibles: Tailwind (CDN), Select2, SweetAlert2, FontAwesome 6.4, Chart.js (solo donde ya se usa).

---

## Tiempo real en una pantalla (FEAT-047)

- `data-live="clave[,clave2]"` en el contenedor del listado: ante un cambio aparece «Hay cambios · Actualizar».
- `data-live-partial` en el mismo elemento: recarga su contenido con `?partial=1`; la vista devuelve solo el fragmento (`_tabla.html`).
- `data-live-edit="app.modelo:pk"` en la pantalla de edición: avisa si otra persona la tiene abierta.
- La fuente se declara en `<app>/live.py` con `core.live.register(...)`. Avisos con `core.avisos.crear_aviso(...)` desde la vista o servicio.

---

## Visor 3D de aberturas (Three.js) — específico de página

El cotizador de presupuestos incluye un **visor 3D** de la abertura (FEAT-030 / ADR-015). **No** está en `base.html`: se carga **solo donde se usa** y **de forma perezosa**.

- **Módulo:** `static/js/viewer3d.js` (Three.js puro, ESM autocontenido). Expone `window.AkunViewer.mount(container, params) / setParams / dispose`.
- **Carga:** import map de `three` (jsdelivr) en el `extra_head` de la página + un `<script type="module">` que define `window.__loadAkunViewer` (hace `import()` recién al primer uso).
- **Uso desde React/Babel:** `window.__loadAkunViewer().then(v => v.mount(ref.current, params))`.
- **params:** `{ tipo, ancho, alto, hojas, mosquitero, premarco, vidrio }`.

**Regla:** dentro de un template Django, **no usar `style={{ }}` de JSX** (choca con `{{ }}` del motor de plantillas) → usar clases Tailwind (ej. `h-72` en vez de `style={{height:'300px'}}`).

---

## Modales apilados y editor de plano SVG interactivo (FEAT-045 / ADR-022)

**Modales apilados.** El editor de estructura `#modal-estructura` vive en `z-50`. Cuando se abre el cotizador `#modal-item` en "modo módulo" encima del editor, sube a `z-[60]`. **Escape cierra solo el modal de más arriba** (el handler de `detalle.html` mira cuál está abierto). Para otro modal sobre un modal, usar el mismo esquema: `z-50` el de abajo, `z-[60]` el de arriba.

**Editor de plano SVG interactivo** (`static/js/estructura.js` + `_estructura_editor.html`):
- Arrastre con **pointer events** y conversión a coordenadas del plano con `getScreenCTM().inverse()` (sirve con cualquier escala del SVG).
- **Grilla de 10 mm** e **imán de ~12 px** a bordes de la pared y de otras piezas, con **guías punteadas** mientras se arrastra.
- Mientras se arrastra se dibuja `soloContorno` (sin el detalle interno de cada abertura) para que el movimiento sea fluido.
- Si se suelta en una posición inválida (superpuesta) la pieza vuelve a su lugar.
- Los mismos campos se pueden cargar a mano en mm; el arrastre no es la única vía.

