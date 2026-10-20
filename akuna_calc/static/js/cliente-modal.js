(function () {
    function modal() { return document.getElementById('clienteModal'); }

    function limpiarErrores(m) {
        m.querySelectorAll('[data-error-for]').forEach(function (el) { el.textContent = ''; });
    }

    function open() {
        var m = modal();
        if (!m) return;
        m.classList.remove('hidden');
        m.querySelector('form').reset();
        limpiarErrores(m);
        if (typeof window.initAkunSelect2 === 'function') window.initAkunSelect2(m);
    }

    function close() {
        var m = modal();
        if (!m) return;
        m.classList.add('hidden');
        if (typeof window.destroyAkunSelect2 === 'function') window.destroyAkunSelect2(m);
    }

    function toast(icon, title) {
        if (window.Swal) {
            Swal.fire({ toast: true, position: 'top-end', icon: icon, titleText: title, showConfirmButton: false, timer: 3000 });
        } else {
            alert(title);
        }
    }

    function mostrarErrores(m, errors) {
        limpiarErrores(m);
        Object.keys(errors || {}).forEach(function (campo) {
            var el = m.querySelector('[data-error-for="' + campo + '"]') || m.querySelector('[data-error-for="__all__"]');
            if (!el) return;
            var msgs = errors[campo];
            var txt = Array.isArray(msgs) ? msgs.join(' ') : String(msgs);
            el.textContent = el.textContent ? el.textContent + ' ' + txt : txt;
        });
    }

    async function submit(e) {
        e.preventDefault();
        var m = modal();
        var form = e.target;
        var btn = form.querySelector('button[type="submit"]');
        var html = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Guardando...';
        var fd = new FormData(form);
        try {
            var response = await fetch(m.dataset.url, {
                method: 'POST',
                body: fd,
                headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': fd.get('csrfmiddlewaretoken') }
            });
            var data = null;
            try { data = await response.json(); } catch (err) { data = null; }
            if (response.status === 403 && data && data.detail) {
                toast('error', 'No tiene permisos para crear clientes.');
            } else if (response.ok && data && data.success) {
                var select = document.querySelector(m.dataset.target);
                if (select) {
                    var option = new Option(data.cliente.etiqueta || data.cliente.nombre, data.cliente.id, true, true);
                    select.add(option);
                    window.jQuery(select).trigger('change');
                }
                close();
                toast('success', 'Cliente creado: ' + (data.cliente.nombre || ''));
            } else if (data && data.errors) {
                mostrarErrores(m, data.errors);
            } else {
                toast('error', 'No se pudo crear el cliente. Intente nuevamente.');
            }
        } catch (err) {
            toast('error', 'No se pudo crear el cliente. Intente nuevamente.');
        } finally {
            btn.disabled = false;
            btn.innerHTML = html;
        }
    }

    document.addEventListener('DOMContentLoaded', function () {
        var m = modal();
        if (!m) return;
        m.addEventListener('click', function (e) {
            if (e.target === m || e.target.closest('[data-cliente-modal-close]')) close();
        });
        m.querySelector('form').addEventListener('submit', submit);
    });

    window.AkunClienteModal = { open: open, close: close };
    window.openClienteModal = open;
    window.closeClienteModal = close;
})();
