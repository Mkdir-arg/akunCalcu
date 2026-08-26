/**
 * Elevación técnica 2D de una abertura, en SVG — opción C del análisis de cotas.
 *
 * Reproduce el plano de referencia: cota de alto a la izquierda, cotas de paño y
 * cota total abajo, etiqueta de composición del vidrio dentro de cada paño,
 * sentido de apertura (Int./Ext. + flecha) y mosquitero rayado.
 *
 * Devuelve un string SVG: no toca el DOM ni depende de Three.js. Sirve tanto
 * para el cotizador como para el PDF, que imprime por window.print().
 */
import { computarLayout } from './abertura-layout.js';

const TXT = 'font-family:Arial,Helvetica,sans-serif';
const esc = s => String(s == null ? '' : s)
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

/** Margen para las cotas, en mm de dibujo (el SVG escala por viewBox). */
const M = { izq: 210, der: 60, arriba: 60, abajo: 220 };

const COLOR = {
  cota: '#1d4ed8',
  perfil: '#111418',
  vidrio: '#dbe6ee',
  ciego: '#9aa3ab',
  malla: '#1d4ed8',
  texto: '#111418',
};

function cotaH(x1, x2, y, valor, size) {
  if (x2 - x1 <= 0) return '';
  const t = size * 0.9;
  const sw = size * 0.09;
  return `<line x1="${x1}" y1="${y}" x2="${x2}" y2="${y}" stroke="${COLOR.cota}" stroke-width="${sw}"/>`
    + `<line x1="${x1}" y1="${y - t}" x2="${x1}" y2="${y + t}" stroke="${COLOR.cota}" stroke-width="${sw}"/>`
    + `<line x1="${x2}" y1="${y - t}" x2="${x2}" y2="${y + t}" stroke="${COLOR.cota}" stroke-width="${sw}"/>`
    + `<text x="${(x1 + x2) / 2}" y="${y - t * 1.4}" fill="${COLOR.cota}" font-size="${size * 2.1}"`
    + ` text-anchor="middle" style="${TXT}">${valor}</text>`;
}

function cotaV(y1, y2, x, valor, size) {
  if (y2 - y1 <= 0) return '';
  const t = size * 0.9;
  const sw = size * 0.09;
  const yc = (y1 + y2) / 2;
  const tx = x - t * 1.5;
  return `<line x1="${x}" y1="${y1}" x2="${x}" y2="${y2}" stroke="${COLOR.cota}" stroke-width="${sw}"/>`
    + `<line x1="${x - t}" y1="${y1}" x2="${x + t}" y2="${y1}" stroke="${COLOR.cota}" stroke-width="${sw}"/>`
    + `<line x1="${x - t}" y1="${y2}" x2="${x + t}" y2="${y2}" stroke="${COLOR.cota}" stroke-width="${sw}"/>`
    + `<text x="${tx}" y="${yc}" fill="${COLOR.cota}" font-size="${size * 2.1}"`
    + ` text-anchor="middle" dominant-baseline="central" transform="rotate(-90 ${tx} ${yc})" style="${TXT}">${valor}</text>`;
}

function flecha(cx, cy, dir, largo, size) {
  const h = size * 1.1;
  const half = largo / 2;
  let x1, x2, y1, y2, punta;
  if (dir === 'izq' || dir === 'der') {
    y1 = y2 = cy;
    x1 = cx - half; x2 = cx + half;
    const px = dir === 'der' ? x2 : x1;
    const s = dir === 'der' ? -1 : 1;
    punta = `${px},${cy} ${px + s * h},${cy - h * 0.62} ${px + s * h},${cy + h * 0.62}`;
  } else {
    x1 = x2 = cx;
    y1 = cy - half; y2 = cy + half;
    const py = dir === 'abajo' ? y2 : y1;
    const s = dir === 'abajo' ? -1 : 1;
    punta = `${cx},${py} ${cx - h * 0.62},${py + s * h} ${cx + h * 0.62},${py + s * h}`;
  }
  return `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${COLOR.cota}" stroke-width="${size * 0.16}"/>`
    + `<polygon points="${punta}" fill="${COLOR.cota}"/>`;
}

function etiqueta(x, y, texto, size) {
  const w = String(texto).length * size * 0.82 + size * 1.1;
  const h = size * 1.9;
  return `<rect x="${x}" y="${y - h / 2}" width="${w}" height="${h}" rx="${size * 0.25}"`
    + ` fill="#ffffff" stroke="${COLOR.perfil}" stroke-width="${size * 0.06}"/>`
    + `<text x="${x + w / 2}" y="${y}" fill="${COLOR.texto}" font-size="${size * 1.25}"`
    + ` text-anchor="middle" dominant-baseline="central" style="${TXT}">${esc(texto)}</text>`;
}

/**
 * @param {object} params  los mismos que recibe el visor 3D, más
 *   `vidrio_composicion` (ej. "3+3/9/3+3") y `sentidos` (['int','ext']).
 * @param {object} [opts]  { cotas, apertura, composicion } — todo true por defecto.
 */
export function svgElevacion(params, opts) {
  const o = Object.assign({ cotas: true, apertura: true, composicion: true }, opts || {});
  const L = computarLayout(params || {});
  const W = L.ancho_mm, H = L.alto_mm;

  // Trazo y texto proporcionales a la pieza: se lee igual en 600 mm y en 3600.
  const size = Math.max(W, H) / 52;

  const mIzq = o.cotas ? M.izq : 20;
  const mAbajo = o.cotas ? M.abajo : 20;
  const vbW = W + mIzq + M.der;
  const vbH = H + M.arriba + mAbajo;
  const ox = mIzq, oy = M.arriba;

  const partes = [];

  // Marco: un trazo grueso centrado en el espesor del perfil + el contorno fino
  partes.push(`<rect x="${ox + L.pw / 2}" y="${oy + L.pw / 2}" width="${W - L.pw}" height="${H - L.pw}"`
    + ` fill="none" stroke="${COLOR.perfil}" stroke-width="${L.pw}"/>`);
  partes.push(`<rect x="${ox}" y="${oy}" width="${W}" height="${H}"`
    + ` fill="none" stroke="${COLOR.perfil}" stroke-width="${size * 0.12}"/>`);

  L.panos.forEach(pano => {
    const px = ox + pano.x, py = oy + pano.y;
    if (L.modo !== 'none') {
      partes.push(`<rect x="${px + L.lf / 2}" y="${py + L.lf / 2}" width="${pano.w - L.lf}" height="${pano.h - L.lf}"`
        + ` fill="none" stroke="${COLOR.perfil}" stroke-width="${L.lf}"/>`);
    }
    const v = pano.vidrio;
    if (pano.secciones) {
      pano.secciones.forEach(s => {
        partes.push(`<rect x="${ox + s.x}" y="${oy + s.y}" width="${s.w}" height="${s.h}"`
          + ` fill="${s.ciego ? COLOR.ciego : COLOR.vidrio}" stroke="${COLOR.perfil}" stroke-width="${size * 0.08}"/>`);
      });
    } else {
      partes.push(`<rect x="${ox + v.x}" y="${oy + v.y}" width="${v.w}" height="${v.h}"`
        + ` fill="${COLOR.vidrio}" stroke="${COLOR.perfil}" stroke-width="${size * 0.08}"/>`);
    }

    if (o.apertura && pano.flecha) {
      partes.push(flecha(ox + v.x + v.w / 2, oy + v.y + v.h * 0.42, pano.flecha, Math.min(v.w * 0.42, 420), size));
      const lbl = pano.sentido === 'ext' ? 'Ext.' : 'Int.';
      partes.push(`<text x="${ox + v.x + v.w / 2}" y="${oy + v.y + v.h * 0.62}" fill="${COLOR.cota}"`
        + ` font-size="${size * 2.6}" font-weight="bold" text-anchor="middle" style="${TXT}">${lbl}</text>`);
    }

    if (o.composicion && pano.composicion) {
      partes.push(etiqueta(ox + v.x + size * 0.6, oy + v.y + v.h - size * 1.8, pano.composicion, size));
    }
  });

  if (L.mosquitero) {
    const m = L.mosquitero;
    const paso = Math.max(size * 0.7, 14);
    const id = 'malla' + Math.round(W) + 'x' + Math.round(H);
    partes.push(`<defs><pattern id="${id}" width="${paso}" height="${paso}" patternUnits="userSpaceOnUse">`
      + `<line x1="0" y1="0" x2="0" y2="${paso}" stroke="${COLOR.malla}" stroke-width="${size * 0.16}"/></pattern></defs>`);
    partes.push(`<rect x="${ox + m.x}" y="${oy + m.y}" width="${m.w}" height="${m.h}"`
      + ` fill="url(#${id})" stroke="${COLOR.perfil}" stroke-width="${size * 0.1}"/>`);
  }

  if (o.cotas) {
    partes.push(cotaV(oy, oy + H, ox - size * 3.2, L.cotas.alto, size));
    const y1 = oy + H + size * 4.2;
    L.cotas.anchos.forEach(c => partes.push(cotaH(ox + c.desde, ox + c.hasta, y1, c.valor, size)));
    const y2 = L.cotas.anchos.length ? y1 + size * 4.6 : y1;
    partes.push(cotaH(ox, ox + W, y2, L.cotas.ancho_total, size));
  }

  return `<svg viewBox="0 0 ${Math.round(vbW)} ${Math.round(vbH)}" width="100%" height="100%"`
    + ` preserveAspectRatio="xMidYMid meet" role="img"`
    + ` aria-label="Elevacion tecnica ${W} x ${H} mm">${partes.join('')}</svg>`;
}

export default { svgElevacion };
