/* Tiempo real por polling (ver docs/team/brief-rediseno-taller.md).
   - data-live="key[,key2]"         : fuente(s) registradas en <app>/live.py
   - data-live-partial              : en el mismo elemento, recarga su contenido con ?partial=1
   - data-live-edit="app.model:pk"  : avisa si otra persona tiene abierta la misma pantalla
   Consulta cada 20 s, se pausa con la pestaña oculta. */
(function () {
    'use strict';
    var cfg = document.getElementById('live-config');
    if (!cfg) { return; }

    var POLL_MS = 20000, MAX_BACKOFF_MS = 120000;
    var pollUrl = cfg.dataset.pollUrl, readUrl = cfg.dataset.readUrl, csrf = cfg.dataset.csrf;
    var baseline = {};          // key -> "stamp|count" de la primera respuesta
    var lastAvisoId = null;
    var delay = POLL_MS, timer = null, inflight = false;
    var bannerShown = false;

    function qsAll(sel) { return Array.prototype.slice.call(document.querySelectorAll(sel)); }

    function liveKeys() {
        var keys = [];
        qsAll('[data-live]').forEach(function (el) {
            el.getAttribute('data-live').split(',').forEach(function (k) {
                k = k.trim();
                if (k && keys.indexOf(k) === -1) { keys.push(k); }
            });
        });
        return keys;
    }

    function editTarget() {
        var el = document.querySelector('[data-live-edit]');
        return el ? el.getAttribute('data-live-edit') : '';
    }

    function poll() {
        if (document.hidden || inflight) { schedule(); return; }
        inflight = true;
        var params = new URLSearchParams();
        var keys = liveKeys();
        if (keys.length) { params.set('keys', keys.join(',')); }
        var edit = editTarget();
        if (edit) { params.set('edit', edit); }
        fetch(pollUrl + '?' + params.toString(), {
            credentials: 'same-origin',
            headers: { 'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest' }
        }).then(function (r) {
            var type = r.headers.get('content-type') || '';
            if (!r.ok || type.indexOf('json') === -1) { throw new Error('poll ' + r.status); }
            return r.json();
        }).then(function (data) {
            delay = POLL_MS;
            handle(data);
        }).catch(function () {
            delay = Math.min(delay * 2, MAX_BACKOFF_MS);
        }).then(function () {
            inflight = false;
            schedule();
        });
    }

    function schedule() {
        clearTimeout(timer);
        timer = setTimeout(poll, delay + Math.floor(Math.random() * 2000));
    }

    function handle(data) {
        handleSources(data.sources || {});
        handleAvisos(data.avisos || { count: 0, items: [] });
        handleDolar(data.dolar);
        handleEdit(data.edit);
        document.dispatchEvent(new CustomEvent('live:data', { detail: data }));
    }

    // ---- listados y tableros ----
    function handleSources(sources) {
        Object.keys(sources).forEach(function (key) {
            var s = sources[key], sig = s.stamp + '|' + s.count;
            if (!(key in baseline)) { baseline[key] = sig; return; }
            if (baseline[key] === sig) { return; }
            baseline[key] = sig;
            qsAll('[data-live]').forEach(function (el) {
                var keys = el.getAttribute('data-live').split(',').map(function (k) { return k.trim(); });
                if (keys.indexOf(key) === -1) { return; }
                if (el.hasAttribute('data-live-partial') && !el.contains(document.activeElement)) {
                    refreshPartial(el);
                } else {
                    showBanner();
                }
            });
        });
    }

    function refreshPartial(el) {
        var u = new URL(window.location.href);
        u.searchParams.set('partial', '1');
        fetch(u.toString(), { credentials: 'same-origin', headers: { 'X-Requested-With': 'XMLHttpRequest' } })
            .then(function (r) { if (!r.ok) { throw new Error(r.status); } return r.text(); })
            .then(function (html) {
                el.innerHTML = html;
                if (window.AkunSelect2) { window.AkunSelect2.init(el); }
                el.dispatchEvent(new CustomEvent('live:updated', { bubbles: true }));
            })
            .catch(showBanner);
    }

    function showBanner() {
        if (bannerShown) { return; }
        bannerShown = true;
        var main = document.querySelector('main') || document.body;
        var b = document.createElement('div');
        b.className = 'live-banner live-banner-info';
        b.setAttribute('role', 'status');
        b.innerHTML = '<i class="fas fa-rotate"></i><span>Hay cambios</span><span>·</span>';
        var btn = document.createElement('button');
        btn.type = 'button';
        btn.textContent = 'Actualizar';
        btn.addEventListener('click', function () { window.location.reload(); });
        b.appendChild(btn);
        main.insertBefore(b, main.firstChild);
    }

    // ---- campanita ----
    function fmtFecha(iso) {
        try { return new Date(iso).toLocaleString('es-AR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }); }
        catch (e) { return ''; }
    }

    function handleAvisos(av) {
        var badge = document.getElementById('live-bell-count');
        var list = document.getElementById('live-avisos-list');
        if (badge) {
            badge.textContent = av.count > 99 ? '99+' : av.count;
            badge.classList.toggle('hidden', !av.count);
        }
        if (list) {
            list.textContent = '';
            if (!av.items.length) {
                var p = document.createElement('p');
                p.className = 'px-4 py-6 text-sm text-ink-3 text-center';
                p.textContent = 'No tenés avisos nuevos.';
                list.appendChild(p);
            }
            av.items.forEach(function (a) {
                var b = document.createElement('button');
                b.type = 'button';
                b.className = 'aviso-item';
                b.textContent = a.texto;
                var t = document.createElement('time');
                t.textContent = fmtFecha(a.fecha);
                b.appendChild(t);
                b.addEventListener('click', function () {
                    markRead(a.id).then(function () { if (a.url) { window.location.href = a.url; } else { poll(); } });
                });
                list.appendChild(b);
            });
        }
        var maxId = av.items.reduce(function (m, a) { return Math.max(m, a.id); }, 0);
        if (lastAvisoId !== null && maxId > lastAvisoId && window.AkunToast) {
            av.items.filter(function (a) { return a.id > lastAvisoId; }).slice(0, 3).forEach(function (a) {
                window.AkunToast.show(a.texto, a.tipo === 'exito' ? 'success' : a.tipo === 'alerta' ? 'warning' : a.tipo === 'error' ? 'error' : 'info');
            });
        }
        if (lastAvisoId === null || maxId > lastAvisoId) { lastAvisoId = maxId; }
    }

    function markRead(id) {
        var body = new URLSearchParams();
        body.set('id', id);
        return fetch(readUrl, {
            method: 'POST', credentials: 'same-origin',
            headers: { 'X-CSRFToken': csrf, 'X-Requested-With': 'XMLHttpRequest' },
            body: body
        }).catch(function () {});
    }

    var readAll = document.getElementById('live-read-all');
    if (readAll) { readAll.addEventListener('click', function () { markRead('all').then(poll); }); }

    // ---- dólar BNA ----
    function fmtDolar(v) {
        return '$ ' + Number(v).toLocaleString('es-AR', { maximumFractionDigits: 0 });
    }

    function setDolar(v) {
        var el = document.getElementById('live-dolar-value');
        if (el && v) { el.textContent = fmtDolar(v); }
    }

    function handleDolar(d) {
        if (d && d.venta) { setDolar(d.venta); return; }
        // Sin fuente en servidor: mismo origen que ya usa el home (dolarapi.com), cacheado 10 min.
        var cached = null;
        try { cached = JSON.parse(localStorage.getItem('akunDolar') || 'null'); } catch (e) {}
        if (cached && Date.now() - cached.t < 600000) { setDolar(cached.v); return; }
        if (handleDolar.pending) { return; }
        handleDolar.pending = true;
        fetch('https://dolarapi.com/v1/dolares/oficial')
            .then(function (r) { return r.json(); })
            .then(function (j) {
                if (j && j.venta) {
                    setDolar(j.venta);
                    try { localStorage.setItem('akunDolar', JSON.stringify({ t: Date.now(), v: j.venta })); } catch (e) {}
                }
            })
            .catch(function () {})
            .then(function () { handleDolar.pending = false; });
    }

    // ---- edición simultánea ----
    function handleEdit(edit) {
        var el = document.querySelector('[data-live-edit]');
        if (!el) { return; }
        var prev = el.querySelector(':scope > .live-edit-banner');
        var otros = edit && edit.otros ? edit.otros.map(function (o) { return o.usuario; }) : [];
        if (!otros.length) { if (prev) { prev.remove(); } return; }
        var label = el.getAttribute('data-live-edit-label') || 'esto';
        var txt = otros.join(', ') + (otros.length > 1 ? ' también están' : ' también está') + ' editando ' + (label === 'esto' ? label : 'este ' + label) + '.';
        if (!prev) {
            prev = document.createElement('div');
            prev.className = 'live-banner live-banner-warn live-edit-banner';
            prev.setAttribute('role', 'alert');
            el.insertBefore(prev, el.firstChild);
        }
        prev.textContent = '';
        var i = document.createElement('i');
        i.className = 'fas fa-user-pen';
        var s = document.createElement('span');
        s.textContent = txt;
        prev.append(i, s);
    }

    document.addEventListener('visibilitychange', function () {
        if (!document.hidden) { delay = POLL_MS; clearTimeout(timer); poll(); }
    });

    poll();
    window.AkunLive = { poll: poll, markRead: markRead };
})();
