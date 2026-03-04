# Design System — AkunCalcu

> Referencia obligatoria para cualquier cambio en el frontend.
> Todo template nuevo debe seguir estos patrones sin excepción.

---

## Base template

```html
{% extends 'core/base.html' %}
{% load static %}

{% block content %}
<!-- tu contenido acá -->
{% endblock %}

{% block extra_js %}
<!-- JS específico de la página -->
{% endblock %}
```

**Nunca** crear un template sin extender `core/base.html` (a menos que sea un template de email o PDF).

---

## Paleta de colores

| Uso | Clases Tailwind |
|-----|----------------|
| Botón primario | `bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white` |
| Botón editar | `bg-indigo-600 hover:bg-indigo-700 text-white` |
| Botón eliminar | `bg-gray-600 hover:bg-gray-700 text-white` |
| Botón filtrar/buscar | `bg-blue-600 hover:bg-blue-700 text-white` |
| Botón cancelar/limpiar | `bg-gray-500 hover:bg-gray-600 text-white` |
| Botón guardar en forms | `bg-green-600 hover:bg-green-700 text-white` |
| Fondo de página | `bg-gray-50` (ya definido en base) |
| Cabecera de tablas | `bg-gradient-to-r from-slate-700 to-slate-800 text-white` |
| Texto título | `text-slate-800` |
| Texto subtítulo | `text-slate-500` |
| Texto de celda | `text-slate-700` |

---

## Tipografía

```html
<!-- Título de página -->
<h1 class="text-3xl lg:text-4xl font-bold text-slate-800 tracking-tight">Título</h1>
<p class="text-slate-500 font-medium mt-1">Subtítulo descriptivo</p>

<!-- Título de sección dentro de página -->
<h2 class="text-xl font-bold text-slate-800 mb-4">Sección</h2>
```

---

## Layout de página estándar

```html
<div class="max-w-full mx-auto px-4">
    <!-- Header de página -->
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 gap-4">
        <div>
            <h1 class="text-3xl lg:text-4xl font-bold text-slate-800 tracking-tight">Título</h1>
            <p class="text-slate-500 font-medium mt-1">Descripción</p>
        </div>
        <!-- Botón de acción principal (si aplica) -->
        <a href="..." class="btn-primary inline-flex items-center text-white px-6 py-3 rounded-2xl font-semibold shadow-xl">
            <i class="fas fa-plus mr-2"></i>Nuevo
        </a>
    </div>

    <!-- Contenido -->
</div>
```

---

## Cards / Contenedores

```html
<!-- Card estándar -->
<div class="bg-white rounded-2xl shadow-lg p-6 mb-6">
    <!-- contenido -->
</div>

<!-- Card de tabla -->
<div class="bg-white rounded-3xl shadow-xl overflow-hidden">
    <!-- tabla acá -->
</div>

<!-- Card de filtros -->
<div class="bg-white rounded-2xl shadow-lg p-4 mb-6">
    <!-- form de búsqueda -->
</div>
```

---

## Botones

```html
<!-- Primario (acción principal, crear) -->
<button class="btn-primary inline-flex items-center text-white px-6 py-3 rounded-2xl font-semibold shadow-xl">
    <i class="fas fa-plus mr-2"></i>Texto
</button>

<!-- Editar (en tablas, compacto) -->
<a href="..." class="inline-flex items-center bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-2 rounded-lg font-semibold transition-all text-xs">
    <i class="fas fa-edit"></i>
</a>

<!-- Eliminar (en tablas, compacto) -->
<button onclick="confirmarEliminacion(...)" class="inline-flex items-center bg-gray-600 hover:bg-gray-700 text-white px-3 py-2 rounded-lg font-semibold transition-all text-xs">
    <i class="fas fa-trash"></i>
</button>

<!-- Submit de formulario -->
<button type="submit" class="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white px-6 py-3 rounded-2xl font-semibold">
    <i class="fas fa-save mr-2"></i>Guardar
</button>

<!-- Cancelar -->
<a href="..." class="bg-gray-500 hover:bg-gray-600 text-white px-6 py-3 rounded-2xl font-semibold">
    Cancelar
</a>
```

---

## Tablas

```html
<div class="bg-white rounded-3xl shadow-xl overflow-hidden">
    <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gradient-to-r from-slate-700 to-slate-800">
                <tr>
                    <th class="px-6 py-4 text-left text-xs font-bold text-white uppercase tracking-wider">Columna</th>
                    <th class="px-6 py-4 text-center text-xs font-bold text-white uppercase tracking-wider">Acciones</th>
                </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
                {% for item in items %}
                <tr class="hover:bg-slate-50 transition-colors">
                    <td class="px-6 py-4 text-sm text-slate-700">{{ item.campo }}</td>
                    <td class="px-6 py-4 text-center">
                        <div class="flex items-center justify-center gap-2">
                            <!-- botones de acción -->
                        </div>
                    </td>
                </tr>
                {% empty %}
                <tr>
                    <td colspan="N" class="px-6 py-8 text-center">
                        <i class="fas fa-inbox text-slate-300 text-4xl mb-2"></i>
                        <p class="text-slate-500 font-medium">No hay registros</p>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
```

---

## Formularios

```html
<div class="bg-white rounded-2xl shadow-lg p-6">
    <form method="post">
        {% csrf_token %}
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Campo de texto -->
            <div>
                <label class="block text-sm font-semibold text-slate-700 mb-2">Etiqueta</label>
                <input type="text" name="campo" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
            </div>

            <!-- Select (Select2 se aplica automáticamente) -->
            <div>
                <label class="block text-sm font-semibold text-slate-700 mb-2">Etiqueta</label>
                <select name="campo" class="w-full px-4 py-2 border border-gray-300 rounded-lg">
                    <option value="">Seleccione...</option>
                </select>
            </div>
        </div>

        <!-- Botones de acción del form -->
        <div class="flex justify-end gap-3 mt-6 pt-4 border-t">
            <a href="..." class="bg-gray-500 hover:bg-gray-600 text-white px-6 py-3 rounded-2xl font-semibold">Cancelar</a>
            <button type="submit" class="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white px-6 py-3 rounded-2xl font-semibold">
                <i class="fas fa-save mr-2"></i>Guardar
            </button>
        </div>
    </form>
</div>
```

**Importante:** Los `<select>` tienen Select2 aplicado automáticamente desde `base.html`. No agregar Select2 manualmente. Para excluir un select, usar clase `no-select2`.

---

## Confirmaciones de eliminación

**Siempre usar SweetAlert2**, nunca `confirm()` nativo del browser.

```javascript
function confirmarEliminacion(url, nombre) {
    Swal.fire({
        title: '¿Eliminar [entidad]?',
        html: `<p>¿Estás seguro de eliminar <strong>${nombre}</strong>?</p>`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#dc2626',
        cancelButtonColor: '#6b7280',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = url;
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
            if (csrfToken) {
                form.innerHTML = `<input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken.value}">`;
            }
            document.body.appendChild(form);
            form.submit();
        }
    });
}
```

---

## Notificaciones / Mensajes

Los mensajes de Django (`messages.success(...)`, `messages.error(...)`, etc.) se muestran automáticamente como SweetAlert2 desde `base.html`. **No crear notificaciones manualmente** en templates individuales.

Para mensajes directos en JavaScript:
```javascript
Swal.fire({
    icon: 'success', // 'error', 'warning', 'info'
    title: 'Éxito',
    text: 'Mensaje aquí',
    confirmButtonColor: '#3b82f6',
    timer: 3000,
    timerProgressBar: true
});
```

---

## Íconos

Usar exclusivamente **FontAwesome 6.4.0** (ya incluido en base.html).

Íconos comunes del proyecto:
- Nuevo/Agregar: `fas fa-plus`
- Editar: `fas fa-edit`
- Eliminar: `fas fa-trash`
- Guardar: `fas fa-save`
- Buscar/Filtrar: `fas fa-filter` o `fas fa-search`
- Limpiar: `fas fa-times`
- Listado vacío: `fas fa-inbox`
- Usuario: `fas fa-user`
- Dinero/Ventas: `fas fa-dollar-sign`
- Productos: `fas fa-box`

---

## Librerías disponibles (ya en base.html)

| Librería | Versión | Uso |
|---------|---------|-----|
| Tailwind CSS | CDN | Estilos |
| FontAwesome | 6.4.0 | Íconos |
| jQuery | 3.6.0 | DOM y AJAX |
| Select2 | 4.1.0 | Selects mejorados |
| SweetAlert2 | 11 | Modales y alertas |

**No agregar nuevas librerías sin pasar por el Arquitecto y registrar un ADR.**
