/**
 * Elevación técnica 2D de una abertura, en SVG.
 *
 * Plano visto de frente: marco y hojas con el color de la terminación, cota de
 * alto a la izquierda, cotas de paño y total abajo, composición del vidrio,
 * mosquitero rayado y el símbolo de apertura de cada paño (REQ-047): flechas por
 * hoja en corredizas, diagonales al lado opuesto a la bisagra en paños de abrir y
 * puertas, triángulos en banderola y brazo de empuje, rombo en proyectante con
 * tijera, y la superposición lateral + basculante en oscilobatientes.
 *
 * Devuelve un string SVG: no toca el DOM ni depende de Three.js. Sirve para el
 * cotizador, la página del presupuesto y el PDF (que imprime por window.print()).
 */
import { computarLayout } from './abertura-layout.js?v=2';

const TXT = 'font-family:Arial,Helvetica,sans-serif';
const esc = s => String(s == null ? '' : s)
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

const M = { izq: 210, der: 60, arriba: 60, abajo: 220 };

const COLOR = {
  cota: '#1d4ed8',
  contorno: '#111418',   // siempre oscuro: un perfil blanco se lee por su contorno
  simbolo: '#334155',
  vidrio: '#dbe6ee',
  ciego: '#9aa3ab',
  malla: '#1d4ed8',
  texto: '#111418',
};

const linea = (x1, y1, x2, y2, stroke, sw, extra) =>
  `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${stroke}" stroke-width="${sw}"${extra || ''}/>`;

/** Perfil: trazo grueso del color de la terminación + contornos finos oscuros. */
function perfilRect(x, y, w, h, grosor, fill, size) {
  const fino = size * 0.1;
  return `<rect x="${x + grosor / 2}" y="${y + grosor / 2}" width="${w - grosor}" height="${h - grosor}"`
    + ` fill="none" stroke="${fill}" stroke-width="${grosor}"/>`
    + `<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="none" stroke="${COLOR.contorno}" stroke-width="${fino}"/>`
    + `<rect x="${x + grosor}" y="${y + grosor}" width="${Math.max(w - 2 * grosor, 1)}" height="${Math.max(h - 2 * grosor, 1)}"`
    + ` fill="none" stroke="${COLOR.contorno}" stroke-width="${fino}"/>`;
}

function cotaH(x1, x2, y, valor, size) {
  if (x2 - x1 <= 0) return '';
  const t = size * 0.9, sw = size * 0.09;
  return linea(x1, y, x2, y, COLOR.cota, sw) + linea(x1, y - t, x1, y + t, COLOR.cota, sw)
    + linea(x2, y - t, x2, y + t, COLOR.cota, sw)
    + `<text x="${(x1 + x2) / 2}" y="${y - t * 1.4}" fill="${COLOR.cota}" font-size="${size * 2.1}"`
    + ` text-anchor="middle" style="${TXT}">${valor}</text>`;
}

function cotaV(y1, y2, x, valor, size) {
  if (y2 - y1 <= 0) return '';
  const t = size * 0.9, sw = size * 0.09, yc = (y1 + y2) / 2, tx = x - t * 1.5;
  return linea(x, y1, x, y2, COLOR.cota, sw) + linea(x - t, y1, x + t, y1, COLOR.cota, sw)
    + linea(x - t, y2, x + t, y2, COLOR.cota, sw)
    + `<text x="${tx}" y="${yc}" fill="${COLOR.cota}" font-size="${size * 2.1}" text-anchor="middle"`
    + ` dominant-baseline="central" transform="rotate(-90 ${tx} ${yc})" style="${TXT}">${valor}</text>`;
}

function flecha(cx, cy, dir, largo, size) {
  const h = size * 1.1, half = largo / 2;
  const x1 = cx - half, x2 = cx + half;
  const px = dir === 'der' ? x2 : x1, s = dir === 'der' ? -1 : 1;
  const punta = `${px},${cy} ${px + s * h},${cy - h * 0.62} ${px + s * h},${cy + h * 0.62}`;
  return linea(x1, cy, x2, cy, COLOR.cota, size * 0.16) + `<polygon points="${punta}" fill="${COLOR.cota}"/>`;
}

function etiqueta(x, y, texto, size) {
  const w = String(texto).length * size * 0.82 + size * 1.1, h = size * 1.9;
  return `<rect x="${x}" y="${y - h / 2}" width="${w}" height="${h}" rx="${size * 0.25}"`
    + ` fill="#ffffff" stroke="${COLOR.contorno}" stroke-width="${size * 0.06}"/>`
    + `<text x="${x + w / 2}" y="${y}" fill="${COLOR.texto}" font-size="${size * 1.25}"`
    + ` text-anchor="middle" dominant-baseline="central" style="${TXT}">${esc(texto)}</text>`;
}

/** Símbolo técnico de apertura de un paño, dibujado sobre su vidrio. */
function simbolo(pano, v, size) {
  const sw = size * 0.14, c = COLOR.simbolo;
  const L = v.x, R = v.x + v.w, T = v.y, B = v.y + v.h;
  const midY = T + v.h / 2, midX = L + v.w / 2;

  // Diagonales desde las esquinas de la bisagra hacia el centro del lado opuesto.
  const lateral = (bisagra) => bisagra === 'der'
    ? linea(R, T, L, midY, c, sw) + linea(R, B, L, midY, c, sw)
    : linea(L, T, R, midY, c, sw) + linea(L, B, R, midY, c, sw);
  // Basculante: bisagra abajo, abre por arriba → vértice arriba.
  const verticeArriba = () => linea(L, B, midX, T, c, sw) + linea(R, B, midX, T, c, sw);
  const verticeAbajo  = () => linea(L, T, midX, B, c, sw) + linea(R, T, midX, B, c, sw);
  const rombo = () => linea(midX, T, R, midY, c, sw) + linea(R, midY, midX, B, c, sw)
                    + linea(midX, B, L, midY, c, sw) + linea(L, midY, midX, T, c, sw);

  switch (pano.simbolo) {
    case 'lateral':        return lateral(pano.bisagra);
    case 'oscilo':         return lateral(pano.bisagra) + verticeArriba();
    case 'vertice_arriba': return verticeArriba();
    case 'vertice_abajo':  return verticeAbajo();
    case 'rombo':          return rombo();
    case 'flechas': {
      const dir = pano.movimiento === 'der' ? 'der' : 'izq';
      const lbl = pano.carril === 'ext' ? 'Ext.' : 'Int.';
      return flecha(midX, T + v.h * 0.42, dir, Math.min(v.w * 0.42, 420), size)
        + `<text x="${midX}" y="${T + v.h * 0.62}" fill="${COLOR.cota}" font-size="${size * 2.6}"`
        + ` font-weight="bold" text-anchor="middle" style="${TXT}">${lbl}</text>`;
    }
    default: return '';
  }
}

/**
 * @param {object} params  los del visor 3D, más `apertura`, `color` /
 *   `color_terminacion` y `vidrio_composicion`.
 * @param {object} [opts]  { cotas, apertura, composicion } — todo true por defecto.
 */
export function svgElevacion(params, opts) {
  const o = Object.assign({ cotas: true, apertura: true, composicion: true }, opts || {});
  const L = computarLayout(params || {});
  const W = L.ancho_mm, H = L.alto_mm;
  const size = Math.max(W, H) / 52;
  const perfil = L.colorPerfil;

  const mIzq = o.cotas ? M.izq : 20, mAbajo = o.cotas ? M.abajo : 20;
  const vbW = W + mIzq + M.der, vbH = H + M.arriba + mAbajo;
  const ox = mIzq, oy = M.arriba;
  const partes = [];

  partes.push(perfilRect(ox, oy, W, H, L.pw, perfil, size));

  L.panos.forEach(pano => {
    const px = ox + pano.x, py = oy + pano.y;
    const v = { x: ox + pano.vidrio.x, y: oy + pano.vidrio.y, w: pano.vidrio.w, h: pano.vidrio.h };

    if (pano.secciones) {
      pano.secciones.forEach(s => {
        partes.push(`<rect x="${ox + s.x}" y="${oy + s.y}" width="${s.w}" height="${s.h}"`
          + ` fill="${s.ciego ? COLOR.ciego : COLOR.vidrio}" stroke="${COLOR.contorno}" stroke-width="${size * 0.08}"/>`);
      });
    } else {
      partes.push(`<rect x="${v.x}" y="${v.y}" width="${v.w}" height="${v.h}"`
        + ` fill="${COLOR.vidrio}" stroke="${COLOR.contorno}" stroke-width="${size * 0.08}"/>`);
    }
    if (L.modo !== 'none') partes.push(perfilRect(px, py, pano.w, pano.h, L.lf, perfil, size));

    if (o.apertura && pano.simbolo) partes.push(simbolo(pano, v, size));

    if (o.composicion && pano.composicion) {
      partes.push(etiqueta(v.x + size * 0.6, v.y + v.h - size * 1.8, pano.composicion, size));
    }
  });

  if (L.mosquitero) {
    const m = L.mosquitero, paso = Math.max(size * 0.7, 14);
    const id = 'malla' + Math.round(W) + 'x' + Math.round(H);
    partes.push(`<defs><pattern id="${id}" width="${paso}" height="${paso}" patternUnits="userSpaceOnUse">`
      + linea(0, 0, 0, paso, COLOR.malla, size * 0.16) + `</pattern></defs>`);
    partes.push(`<rect x="${ox + m.x}" y="${oy + m.y}" width="${m.w}" height="${m.h}"`
      + ` fill="url(#${id})" stroke="${COLOR.contorno}" stroke-width="${size * 0.1}"/>`);
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
