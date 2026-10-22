/**
 * Plano de una estructura (REQ-062): varias aberturas ubicadas sobre una pared.
 *
 * Geometría (etiquetas M1..Mn, juntas, validación, envolvente) idéntica a la de
 * `pricing/services/estructura.py`; ambas se prueban contra
 * `pricing/fixtures_estructura_geometria.json`. Cada abertura se dibuja con
 * `dibujarAbertura` de elevacion.js, así que el plano de la estructura y el de una
 * abertura suelta salen del mismo código.
 *
 * Unidades en mm. `x` = desde el borde izquierdo de la pared, `y` = desde el piso
 * (NPT) hasta el borde inferior de la abertura. El SVG usa `y` hacia abajo:
 * y_svg = pared.alto - (y + alto).
 *
 * Devuelve strings SVG: no toca el DOM. Sirve para el editor, la miniatura del
 * presupuesto y el anexo del PDF.
 */
import { svgElevacion, dibujarAbertura } from './elevacion.js?v=3';

const TXT = 'font-family:Arial,Helvetica,sans-serif';
const esc = s => String(s == null ? '' : s)
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const num = v => { const n = Number(v); return Number.isFinite(n) ? n : 0; };
const idSeguro = s => String(s == null ? '' : s).replace(/[^A-Za-z0-9_-]/g, '');

const MAX_MODULOS = 12, LADO_MIN = 200, PARED_MIN = 500;

const COL = {
  cota: '#1d4ed8', contorno: '#111418', vidrio: '#dbe6ee', texto: '#111418',
  sel: '#4f46e5', err: '#dc2626', junta: '#d97706', juntaSin: '#64748b', guia: '#2563eb',
};

// ---------------------------------------------------------------- geometría

const normMod = m => ({
  x: num(m && m.x), y: num(m && m.y), ancho: num(m && m.ancho), alto: num(m && m.alto),
});
const solapan = (a, b) => a.x < b.x + b.ancho && a.x + a.ancho > b.x && a.y < b.y + b.alto && a.y + a.alto > b.y;

/** Índices de `modulos` en orden de etiqueta: x, luego y (de abajo hacia arriba), luego índice. */
function ordenIndices(modulos) {
  const ms = (modulos || []).map(normMod);
  return ms.map((_, i) => i).sort((i, j) => ms[i].x - ms[j].x || ms[i].y - ms[j].y || i - j);
}

/** Etiquetas 'M1'..'Mn' alineadas al índice de entrada. */
export function etiquetarModulos(modulos) {
  const out = new Array((modulos || []).length);
  ordenIndices(modulos).forEach((idx, pos) => { out[idx] = 'M' + (pos + 1); });
  return out;
}

/**
 * Juntas: bordes que coinciden y se solapan en un largo > 0 (tocarse en una esquina no cuenta).
 * Tolerancia 0. Los pares salen en orden de etiqueta; `a` y `b` son índices de entrada.
 */
export function detectarJuntas(modulos) {
  const ms = (modulos || []).map(normMod), orden = ordenIndices(modulos), out = [];
  for (let i = 0; i < orden.length; i++) {
    for (let j = i + 1; j < orden.length; j++) {
      const ia = orden[i], ib = orden[j], a = ms[ia], b = ms[ib];
      const solapeY = Math.min(a.y + a.alto, b.y + b.alto) - Math.max(a.y, b.y);
      if (solapeY > 0 && (a.x + a.ancho === b.x || b.x + b.ancho === a.x)) {
        const xj = a.x + a.ancho === b.x ? b.x : a.x, y1 = Math.max(a.y, b.y);
        out.push({ a: ia, b: ib, orientacion: 'vertical', largo: solapeY, x1: xj, y1, x2: xj, y2: y1 + solapeY });
      }
      const solapeX = Math.min(a.x + a.ancho, b.x + b.ancho) - Math.max(a.x, b.x);
      if (solapeX > 0 && (a.y + a.alto === b.y || b.y + b.alto === a.y)) {
        const yj = a.y + a.alto === b.y ? b.y : a.y, x1 = Math.max(a.x, b.x);
        out.push({ a: ia, b: ib, orientacion: 'horizontal', largo: solapeX, x1, y1: yj, x2: x1 + solapeX, y2: yj });
      }
    }
  }
  return out;
}

/**
 * @param {{pared:{ancho:number,alto:number}, modulos:object[]}} p
 * @returns {{errores:string[], indices:number[]}} `indices` = módulos a marcar en rojo.
 *   El conteo de `errores` es el mismo que el del servidor: un mensaje por problema.
 */
export function validarEstructura(p) {
  const errores = [], marcados = new Set();
  const modulos = (p && p.modulos) || [];
  const pared = (p && p.pared) || {};
  const PW = num(pared.ancho), PH = num(pared.alto);

  if (PW < PARED_MIN || PH < PARED_MIN) errores.push(`La pared debe medir al menos ${PARED_MIN} mm de ancho y de alto.`);
  if (!modulos.length) { errores.push('Agregá al menos una abertura.'); return { errores, indices: [] }; }
  if (modulos.length > MAX_MODULOS) {
    errores.push(`Una estructura admite hasta ${MAX_MODULOS} aberturas.`);
    return { errores, indices: [] };
  }

  const ms = modulos.map(normMod), lb = etiquetarModulos(modulos), orden = ordenIndices(modulos);
  for (const i of orden) {
    const m = ms[i];
    if (m.ancho < LADO_MIN || m.alto < LADO_MIN) {
      errores.push(`${lb[i]}: el lado mínimo es ${LADO_MIN} mm.`); marcados.add(i);
    }
    if (m.x < 0 || m.y < 0 || m.x + m.ancho > PW || m.y + m.alto > PH) {
      errores.push(`${lb[i]} se sale de la pared. Movela o agrandá la pared.`); marcados.add(i);
    }
  }
  for (let i = 0; i < orden.length; i++) {
    for (let j = i + 1; j < orden.length; j++) {
      if (solapan(ms[orden[i]], ms[orden[j]])) {
        errores.push(`${lb[orden[i]]} y ${lb[orden[j]]} se superponen. Separalas o pegalas borde con borde.`);
        marcados.add(orden[i]); marcados.add(orden[j]);
      }
    }
  }
  return { errores, indices: [...marcados].sort((a, b) => a - b) };
}

/** Caja que contiene a todas las aberturas. */
export function envolvente(modulos) {
  const ms = (modulos || []).map(normMod);
  if (!ms.length) return { x: 0, y: 0, ancho: 0, alto: 0 };
  const x = Math.min(...ms.map(m => m.x)), y = Math.min(...ms.map(m => m.y));
  return {
    x, y,
    ancho: Math.max(...ms.map(m => m.x + m.ancho)) - x,
    alto: Math.max(...ms.map(m => m.y + m.alto)) - y,
  };
}

// ---------------------------------------------------------------- dibujo

const linea = (x1, y1, x2, y2, stroke, sw, extra) =>
  `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${stroke}" stroke-width="${sw}"${extra || ''}/>`;

const anchoTexto = (valor, fs) => String(valor).length * fs * 0.56 + fs * 0.4;

function cotaH(x1, x2, y, valor, size) {
  if (x2 - x1 <= 0) return '';
  const t = size * 0.9, sw = size * 0.09, fs = size * 1.6;
  return linea(x1, y, x2, y, COL.cota, sw) + linea(x1, y - t, x1, y + t, COL.cota, sw)
    + linea(x2, y - t, x2, y + t, COL.cota, sw)
    + `<text x="${(x1 + x2) / 2}" y="${y - t * 1.3}" fill="${COL.cota}" font-size="${fs}"`
    + ` text-anchor="middle" style="${TXT}">${esc(valor)}</text>`;
}

function cotaV(y1, y2, x, valor, size) {
  if (y2 - y1 <= 0) return '';
  const t = size * 0.9, sw = size * 0.09, fs = size * 1.6, yc = (y1 + y2) / 2, tx = x - t * 1.4;
  return linea(x, y1, x, y2, COL.cota, sw) + linea(x - t, y1, x + t, y1, COL.cota, sw)
    + linea(x - t, y2, x + t, y2, COL.cota, sw)
    + `<text x="${tx}" y="${yc}" fill="${COL.cota}" font-size="${fs}" text-anchor="middle"`
    + ` dominant-baseline="central" transform="rotate(-90 ${tx} ${yc})" style="${TXT}">${esc(valor)}</text>`;
}

/** Chip con la etiqueta del módulo (M1, M2…). */
function chip(x, y, texto, size) {
  const fs = size * 1.45, w = String(texto).length * fs * 0.56 + size * 1.1, h = fs * 1.45;
  return `<rect x="${x}" y="${y - h / 2}" width="${w}" height="${h}" rx="${size * 0.25}"`
    + ` fill="#ffffff" stroke="${COL.contorno}" stroke-width="${size * 0.06}"/>`
    + `<text x="${x + w / 2}" y="${y}" fill="${COL.texto}" font-size="${fs}"`
    + ` text-anchor="middle" dominant-baseline="central" style="${TXT}">${esc(texto)}</text>`;
}

/**
 * Reparte intervalos únicos en filas para que sus textos no se pisen.
 * Cada intervalo ocupa max(largo, ancho del texto) centrado en su punto medio.
 * @returns {{lo:number, hi:number, valor:number, fila:number}[]} y la cantidad de filas.
 */
function filasCotas(intervalos, size) {
  const fs = size * 1.6, vistos = new Set(), items = [];
  for (const [lo, hi] of intervalos) {
    const k = lo + ':' + hi;
    if (hi - lo <= 0 || vistos.has(k)) continue;
    vistos.add(k);
    const w = Math.max(hi - lo, anchoTexto(hi - lo, fs)), mid = (lo + hi) / 2;
    items.push({ lo, hi, valor: hi - lo, ocLo: mid - w / 2, ocHi: mid + w / 2 });
  }
  items.sort((a, b) => a.ocLo - b.ocLo);
  const finFila = [];
  for (const it of items) {
    let f = finFila.findIndex(fin => it.ocLo >= fin);
    if (f < 0) { f = finFila.length; finFila.push(0); }
    finFila[f] = it.ocHi + size * 0.5;
    it.fila = f;
  }
  return { items, filas: finFila.length };
}

const ROW = 5.5; // separación entre filas de cotas, en unidades de size

/**
 * @param {object} p  forma de la sección 4 del contrato: { pared, modulos:[{x,y,ancho,alto,dibujo}],
 *   juntas?, perfil_union, color_terminacion | color }.
 * @param {object} [opts] pared (true), cotas (true), etiquetas (true), apertura (true),
 *   interactivo, seleccion (idx), invalidos ([idx]), soloContorno, guias ({gx:[mm], gy:[mm]}), idPrefijo.
 */
export function svgEstructura(p, opts) {
  const o = Object.assign({
    pared: true, cotas: true, etiquetas: true, apertura: true, interactivo: false,
    seleccion: null, invalidos: [], soloContorno: false, guias: null, idPrefijo: '',
  }, opts || {});
  p = p || {};
  const idp = idSeguro(o.idPrefijo);
  const modulos = Array.isArray(p.modulos) ? p.modulos : [];
  const ms = modulos.map(normMod);
  const lb = etiquetarModulos(modulos);
  const env = envolvente(modulos);
  const PW = Math.max(num(p.pared && p.pared.ancho), env.x + env.ancho);
  const PH = Math.max(num(p.pared && p.pared.alto), env.y + env.alto);
  const top = m => PH - (m.y + m.alto);
  const conPerfil = !!p.perfil_union;
  const invalidos = new Set(o.invalidos || []);
  const juntas = Array.isArray(p.juntas) ? p.juntas : detectarJuntas(modulos);

  // Marco de referencia de las cotas totales: la pared, o la envolvente en la miniatura.
  const ref = o.pared
    ? { x: 0, y: 0, ancho: PW, alto: PH }
    : { x: env.x, y: env.y, ancho: env.ancho, alto: env.alto };
  const size = o.pared
    ? Math.max(PW, PH, 1) / 75
    : Math.max(env.ancho, env.alto, 600) / 38;

  // Cotas: filas de ancho por abertura (abajo) y de alto por abertura (derecha), más el total.
  const bajoY = PH - ref.y;                 // y_svg del borde inferior de referencia
  const derX = ref.x + ref.ancho;           // x del borde derecho de referencia
  let filasH = { items: [], filas: 0 }, filasV = { items: [], filas: 0 };
  if (o.cotas && ms.length) {
    filasH = filasCotas(ms.map(m => [m.x, m.x + m.ancho]), size);
    filasV = filasCotas(ms.map(m => [m.y, m.y + m.alto]), size);
  }
  const nH = o.cotas ? filasH.filas + 1 : 0, nV = o.cotas ? filasV.filas + 1 : 0;

  let vb, s = '';
  if (o.pared) {
    const ml = size * 8, mt = size * 3;
    const mr = size * (o.cotas ? 5 + nV * ROW : 3), mb = size * (o.cotas ? 4.5 + nH * ROW : 4);
    vb = [-ml, -mt, PW + ml + mr, PH + mt + mb];
    const hp = size * 1.3, hid = idp + 'hatch';
    s += `<defs><pattern id="${hid}" width="${hp}" height="${hp}" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">`
      + `<rect width="${hp}" height="${hp}" fill="#eef0f3"/>${linea(0, 0, 0, hp, '#c5cbd4', size * 0.14)}</pattern></defs>`;
    s += `<rect x="0" y="0" width="${PW}" height="${PH}" fill="url(#${hid})" stroke="#9aa3ae" stroke-width="${size * 0.08}"/>`;
    s += linea(-size * 7.5, PH, PW + size * 2, PH, COL.contorno, size * 0.3);
    s += `<text x="${-size * 7.5}" y="${PH - size * 0.6}" fill="${COL.texto}" font-size="${size * 1.45}" style="${TXT}">NPT ±0,00</text>`;
  } else {
    const pad = size * 1.2;
    const ml = o.cotas ? size * 5 : pad, mr = o.cotas ? size * (5 + nV * ROW) : pad;
    const mb = o.cotas ? size * (4.5 + nH * ROW) : pad;
    vb = [env.x - ml, PH - (env.y + env.alto) - pad, env.ancho + ml + mr, env.alto + pad + mb];
  }

  // Aberturas: de la última a la primera no importa el orden; en orden de etiqueta se lee mejor el DOM.
  for (const i of ordenIndices(modulos)) {
    const m = ms[i], src = modulos[i], X = m.x, Y = top(m);
    let g = '';
    if (o.soloContorno) {
      g += `<rect x="${X}" y="${Y}" width="${m.ancho}" height="${m.alto}" fill="${COL.vidrio}"`
        + ` stroke="${COL.contorno}" stroke-width="${size * 0.14}"/>`;
    } else if (src && src.dibujo) {
      const params = Object.assign({}, src.dibujo, { ancho: m.ancho, alto: m.alto });
      if (!params.color && !params.color_terminacion) {
        if (p.color_terminacion) params.color_terminacion = p.color_terminacion;
        if (p.color) params.color = p.color;
      }
      g += dibujarAbertura(params, {
        ox: X, oy: Y, size, apertura: o.apertura, composicion: false, idPrefijo: idp + 'm' + i + '-',
      });
    } else {
      const fs = Math.max(Math.min(size * 1.6, m.ancho / 9), 1);
      g += `<rect x="${X}" y="${Y}" width="${m.ancho}" height="${m.alto}" fill="#f1f5f9"`
        + ` stroke="#94a3b8" stroke-width="${size * 0.2}" stroke-dasharray="${size} ${size * 0.6}"/>`
        + `<text x="${X + m.ancho / 2}" y="${Y + m.alto / 2}" fill="#64748b" font-size="${fs}"`
        + ` text-anchor="middle" dominant-baseline="central" style="${TXT}">Sin configurar</text>`;
    }
    if (o.etiquetas) g += chip(X + size * 0.9, Y + size * 2.1, lb[i], size);
    if (invalidos.has(i)) {
      g += `<rect x="${X}" y="${Y}" width="${m.ancho}" height="${m.alto}" fill="rgba(220,38,38,.14)"`
        + ` stroke="${COL.err}" stroke-width="${size * 0.35}" stroke-dasharray="${size} ${size * 0.6}"/>`;
    } else if (o.seleccion === i) {
      g += `<rect x="${X}" y="${Y}" width="${m.ancho}" height="${m.alto}" fill="rgba(79,70,229,.10)"`
        + ` stroke="${COL.sel}" stroke-width="${size * 0.35}"/>`;
    }
    s += o.interactivo
      ? `<g class="mod" data-idx="${i}" data-etiqueta="${esc(lb[i])}" tabindex="0" role="button" aria-label="${esc(lb[i])}">${g}</g>`
      : g;
  }

  for (const j of juntas) {
    const x1 = num(j.x1), y1 = PH - num(j.y1), x2 = num(j.x2), y2 = PH - num(j.y2);
    s += conPerfil
      ? linea(x1, y1, x2, y2, COL.junta, size * 0.55)
      : linea(x1, y1, x2, y2, COL.juntaSin, size * 0.22, ` stroke-dasharray="${size * 0.7} ${size * 0.5}"`);
  }

  if (o.guias) {
    const ex = ` stroke-dasharray="${size * 0.6} ${size * 0.4}"`;
    (o.guias.gx || []).forEach(x => { s += linea(num(x), -size * 2, num(x), PH + size * 2, COL.guia, size * 0.14, ex); });
    (o.guias.gy || []).forEach(y => { s += linea(-size * 2, PH - num(y), PW + size * 2, PH - num(y), COL.guia, size * 0.14, ex); });
  }

  if (o.cotas) {
    const ext = ` stroke-opacity="0.35" stroke-dasharray="${size * 0.5} ${size * 0.4}"`;
    const rowY = f => bajoY + size * (4.5 + f * ROW);
    filasH.items.forEach(it => {
      const y = rowY(it.fila);
      s += linea(it.lo, bajoY, it.lo, y, COL.cota, size * 0.05, ext) + linea(it.hi, bajoY, it.hi, y, COL.cota, size * 0.05, ext);
      s += cotaH(it.lo, it.hi, y, it.valor, size);
    });
    s += cotaH(ref.x, ref.x + ref.ancho, rowY(filasH.filas), Math.round(ref.ancho), size);

    const rowX = f => derX + size * (4.5 + f * ROW);
    filasV.items.forEach(it => {
      const x = rowX(it.fila), a = PH - it.hi, b = PH - it.lo;
      s += linea(derX, a, x, a, COL.cota, size * 0.05, ext) + linea(derX, b, x, b, COL.cota, size * 0.05, ext);
      s += cotaV(a, b, x, it.valor, size);
    });
    s += cotaV(PH - (ref.y + ref.alto), PH - ref.y, rowX(filasV.filas), Math.round(ref.alto), size);
  }

  const nombre = `Plano de estructura de ${ms.length} abertura${ms.length === 1 ? '' : 's'}, pared ${Math.round(PW)} x ${Math.round(PH)} mm`;
  return `<svg viewBox="${vb.map(v => Math.round(v * 100) / 100).join(' ')}" width="100%" height="100%"`
    + ` preserveAspectRatio="xMidYMid meet" role="img" aria-label="${esc(nombre)}">${s}</svg>`;
}

/** Despachador: estructura → plano de la pared; cualquier otro → elevación de una abertura. */
export function svgDibujo(p, opts) {
  return p && p.tipo === 'estructura' ? svgEstructura(p, opts) : svgElevacion(p, opts);
}

export default { etiquetarModulos, detectarJuntas, validarEstructura, envolvente, svgEstructura, svgDibujo };
