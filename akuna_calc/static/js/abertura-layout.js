/**
 * Layout de cotas de una abertura — módulo puro, sin Three.js ni DOM.
 *
 * Calcula, en milímetros, la geometría que necesitan las COTAS: el hueco, los
 * paños, las secciones divididas por tirantes y el mosquitero. NO calcula las
 * mallas 3D: eso sigue en `viewer3d.js`. La idea es que la elevación 2D y el
 * overlay del visor midan lo mismo sin duplicar la aritmética.
 *
 * Origen de coordenadas: esquina superior izquierda del marco, `y` hacia abajo
 * (cómodo para SVG). El visor 3D convierte a su sistema centrado con y hacia
 * arriba al proyectar.
 *
 * Las constantes de perfil replican las de `viewer3d.js` (ahí están en metros).
 */

export const TIPOS_LAYOUT = {
  ventana_corrediza:   { hojas: [2, 3, 4], modo: 'slide',  puerta: false },
  ventana_batiente:    { hojas: [1, 2],    modo: 'swing',  puerta: false },
  ventana_oscilo:      { hojas: [1],       modo: 'tilt',   puerta: false },
  ventana_proyectante: { hojas: [1],       modo: 'project', puerta: false },
  pano_fijo:           { hojas: [1],       modo: 'none',   puerta: false },
  puerta_batiente:     { hojas: [1, 2],    modo: 'swing',  puerta: true },
  puerta_corrediza:    { hojas: [2, 3],    modo: 'slide',  puerta: true },
};

const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
const medidaSeccion = s => parseInt(s && s.medida_mm != null ? s.medida_mm : (s && s.alto_mm), 10) || 0;

/** Reparte `total` en proporción a las medidas declaradas de cada sección. */
function repartirSecciones(secs, total) {
  const suma = secs.reduce((a, s) => a + medidaSeccion(s), 0);
  if (suma <= 0) return null;
  let cursor = 0;
  return secs.map(s => {
    const largo = (medidaSeccion(s) / suma) * total;
    const desde = cursor;
    cursor += largo;
    return { desde, largo, ciego: !!s.ciego, medida_mm: medidaSeccion(s), codigo: s.codigo || null };
  });
}

/**
 * @param {object} p
 *   tipo, ancho, alto, hojas, mosquitero, premarco
 *   tirantes: [{ medida_mm, ciego }] | null · tirantes_orientacion: 'horizontal' | 'vertical'
 *   sentidos: ['int','ext',...] | null — sentido de apertura por paño; si falta
 *             se usa una convención (ver `sentidoPorConvencion`).
 *   vidrio_composicion: string | null — ej. "3+3/9/3+3", para la etiqueta del paño.
 */
export function computarLayout(p) {
  const tipo = TIPOS_LAYOUT[p.tipo] ? p.tipo : 'pano_fijo';
  const T = TIPOS_LAYOUT[tipo];
  const W = Math.max(parseInt(p.ancho, 10) || 0, 1);
  const H = Math.max(parseInt(p.alto, 10) || 0, 1);

  const pw = T.puerta ? 60 : 55;   // perfil del marco
  const lf = T.puerta ? 55 : 40;   // perfil de la hoja

  const nH = T.hojas.includes(parseInt(p.hojas, 10))
    ? parseInt(p.hojas, 10)
    : T.hojas[0];

  const hueco = { x: pw, y: pw, w: Math.max(W - 2 * pw, 1), h: Math.max(H - 2 * pw, 1) };

  // --- Paños ---
  const panos = [];
  if (T.modo === 'none') {
    panos.push({ x: hueco.x, y: hueco.y, w: hueco.w, h: hueco.h, movil: false, indice: 0 });
  } else {
    const colW = hueco.w / nH;
    for (let i = 0; i < nH; i++) {
      panos.push({
        x: hueco.x + colW * i,
        y: hueco.y,
        w: colW,
        h: hueco.h,
        // En corredizas las hojas pares son las móviles (igual que en el visor).
        movil: T.modo === 'slide' ? (i % 2 === 0) : true,
        indice: i,
      });
    }
  }

  // Sentido de apertura por paño (dato que hoy no viaja: ver README de la feature)
  const sentidosDados = Array.isArray(p.sentidos) ? p.sentidos : null;
  panos.forEach((pano, i) => {
    pano.sentido = sentidosDados && sentidosDados[i]
      ? sentidosDados[i]
      : sentidoPorConvencion(T.modo, i, nH);
    pano.flecha = flechaPorSentido(T.modo, i, nH);
  });

  // --- Secciones por tirantes ---
  // Se aplican sobre el vidrio del paño, descontando el perfil de la hoja.
  const secsIn = Array.isArray(p.tirantes) && p.tirantes.length >= 2 ? p.tirantes : null;
  const vertical = p.tirantes_orientacion === 'vertical';
  panos.forEach(pano => {
    const vidrio = {
      x: pano.x + (T.modo === 'none' ? 0 : lf),
      y: pano.y + (T.modo === 'none' ? 0 : lf),
      w: Math.max(pano.w - (T.modo === 'none' ? 0 : 2 * lf), 1),
      h: Math.max(pano.h - (T.modo === 'none' ? 0 : 2 * lf), 1),
    };
    pano.vidrio = vidrio;
    pano.composicion = p.vidrio_composicion || null;
    if (!secsIn) { pano.secciones = null; return; }
    const reparto = repartirSecciones(secsIn, vertical ? vidrio.w : vidrio.h);
    pano.secciones = reparto && reparto.map(r => ({
      ...r,
      x: vertical ? vidrio.x + r.desde : vidrio.x,
      y: vertical ? vidrio.y : vidrio.y + r.desde,
      w: vertical ? r.largo : vidrio.w,
      h: vertical ? vidrio.h : r.largo,
    }));
  });

  // --- Mosquitero: comparte columna con el último paño ---
  const mosquitero = p.mosquitero && panos.length
    ? (() => {
        const ult = panos[panos.length - 1];
        const ancho = clamp(ult.w * 0.42, 60, ult.w);
        return { x: ult.x + ult.w - ancho, y: ult.y, w: ancho, h: ult.h };
      })()
    : null;

  // --- Cotas ---
  // Las cotas de paño PARTEN EL ANCHO TOTAL, no el hueco: se miden de borde
  // exterior a eje del travesaño, y de eje a borde exterior. En los planos de
  // referencia una corrediza de 1790 con 2 hojas cota 895 + 895 = 1790, no el
  // 840 + 840 del hueco interior.
  const ejes = panos.slice(1).map(x => x.x);          // eje de cada travesaño vertical
  const bordes = [0, ...ejes, W];
  // El último segmento absorbe el redondeo: la suma de las cotas parciales
  // tiene que dar exactamente el total, o el plano se lee como equivocado.
  const anchos = panos.length > 1
    ? (() => {
        const segs = bordes.slice(0, -1).map((desde, i) => ({
          desde, hasta: bordes[i + 1], valor: Math.round(bordes[i + 1] - desde),
        }));
        const parcial = segs.slice(0, -1).reduce((a, s) => a + s.valor, 0);
        segs[segs.length - 1].valor = W - parcial;
        return segs;
      })()
    : [];

  const cotas = {
    alto: H,
    ancho_total: W,
    anchos,
    // Con tirantes, la medida declarada de cada sección sobre el eje dividido.
    secciones: secsIn ? secsIn.map(medidaSeccion) : [],
    secciones_orientacion: vertical ? 'vertical' : 'horizontal',
  };

  return { tipo, modo: T.modo, puerta: T.puerta, ancho_mm: W, alto_mm: H, pw, lf, nH, hueco, panos, mosquitero, cotas };
}

/**
 * Convención cuando el ítem no trae el sentido cargado.
 * OJO: en los dibujos de referencia el sentido varía por ítem (una misma
 * corrediza de 2 hojas aparece con "Int." a la izquierda en un plano y con
 * "Ext." en otro), así que esto es solo un default razonable, no la verdad.
 */
export function sentidoPorConvencion(modo, i, nH) {
  if (modo === 'none') return null;
  if (modo === 'slide') return (i % 2 === 0) ? 'int' : 'ext';
  if (nH === 2) return i === 0 ? 'int' : 'ext';
  return 'int';
}

/** Dirección de la flecha: la hoja móvil corre hacia la hoja vecina. */
export function flechaPorSentido(modo, i, nH) {
  if (modo === 'none') return null;
  if (modo === 'slide') return i === nH - 1 ? 'izq' : 'der';
  if (modo === 'tilt') return 'abajo';
  if (modo === 'project') return 'arriba';
  if (nH === 2) return i === 0 ? 'der' : 'izq';
  return 'der';
}

export default { computarLayout, sentidoPorConvencion, flechaPorSentido, TIPOS_LAYOUT };
