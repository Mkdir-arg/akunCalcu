/**
 * Layout de cotas y aperturas de una abertura — módulo puro, sin Three.js ni DOM.
 *
 * Calcula, en milímetros, lo que necesitan los dibujos: hueco, paños, secciones
 * por tirantes, mosquitero, cotas, y por cada paño el símbolo de apertura
 * (REQ-047). NO calcula mallas 3D: eso sigue en `viewer3d.js`.
 *
 * Origen: esquina superior izquierda del marco, `y` hacia abajo (cómodo para SVG).
 *
 * Convención única: izquierda y derecha son de la abertura VISTA DE FRENTE.
 * "Int./Ext." es otro eje (carril interior/exterior de una corrediza).
 *
 * El catálogo `APERTURAS` es espejo de `pricing/aperturas.py`: mismos códigos.
 */

export const TIPOS_LAYOUT = {
  ventana_corrediza:   { hojas: [2, 3, 4, 6], modo: 'slide',   puerta: false },
  ventana_batiente:    { hojas: [1, 2],       modo: 'swing',   puerta: false },
  ventana_oscilo:      { hojas: [1],          modo: 'tilt',    puerta: false },
  ventana_proyectante: { hojas: [1],          modo: 'project', puerta: false },
  pano_fijo:           { hojas: [1],          modo: 'none',    puerta: false },
  puerta_batiente:     { hojas: [1, 2],       modo: 'swing',   puerta: true },
  puerta_corrediza:    { hojas: [2, 3],       modo: 'slide',   puerta: true },
};

export const APERTURAS = [
  { codigo: 'pano_fijo',          nombre: 'Paño fijo',               simbolo: 'ninguno',        hojas: [1],          lado: false, porHoja: false },
  { codigo: 'corrediza',          nombre: 'Corrediza',               simbolo: 'flechas',        hojas: [2, 3, 4, 6], lado: false, porHoja: true },
  { codigo: 'abrir_1',            nombre: 'Paño de abrir 1 hoja',    simbolo: 'lateral',        hojas: [1],          lado: true,  porHoja: false },
  { codigo: 'abrir_2',            nombre: 'Paño de abrir 2 hojas',   simbolo: 'lateral_doble',  hojas: [2],          lado: false, porHoja: false },
  { codigo: 'oscilobatiente',     nombre: 'Oscilobatiente',          simbolo: 'oscilo',         hojas: [1],          lado: true,  porHoja: false },
  { codigo: 'banderola',          nombre: 'Banderola',               simbolo: 'vertice_arriba', hojas: [1],          lado: false, porHoja: false },
  { codigo: 'brazo_empuje',       nombre: 'Brazo de empuje',         simbolo: 'vertice_abajo',  hojas: [1],          lado: false, porHoja: false },
  { codigo: 'proyectante_tijera', nombre: 'Proyectante con tijera',  simbolo: 'rombo',          hojas: [1],          lado: false, porHoja: false },
  { codigo: 'puerta',             nombre: 'Puerta 1 hoja',           simbolo: 'lateral',        hojas: [1],          lado: true,  porHoja: false },
  { codigo: 'puerta_doble',       nombre: 'Puerta 2 hojas',          simbolo: 'lateral_doble',  hojas: [2],          lado: false, porHoja: false },
  { codigo: 'puerta_corrediza',   nombre: 'Puerta corrediza',        simbolo: 'flechas',        hojas: [2, 3],       lado: false, porHoja: true },
];
export const APERTURA_POR_CODIGO = Object.fromEntries(APERTURAS.map(a => [a.codigo, a]));

/** Colores del perfil por terminación (mismos hex que PERFILES del visor 3D). */
export const PERFIL_COLORES = {
  blanco: '#f3f4f4', negro: '#1b1d1f', antracita: '#373b3f',
  bronce: '#54422e', madera: '#6a4526', aluminio: '#bfc3c8',
};

/** Descripción del tratamiento ("ANODIZADO BRONCE") → clave de PERFIL_COLORES. */
export function mapColor(desc) {
  const d = String(desc || '').toLowerCase();
  if (d.includes('negro') || d.includes('negra')) return 'negro';
  if (d.includes('bronce')) return 'bronce';
  if (d.includes('antracita') || d.includes('grafito') || d.includes('gris')) return 'antracita';
  if (d.includes('madera') || d.includes('roble') || d.includes('cedro') || d.includes('nogal') || d.includes('simil')) return 'madera';
  if (d.includes('anod') || d.includes('natural') || d.includes('aluminio') || d.includes('plata') || d.includes('crudo')) return 'aluminio';
  return 'blanco';
}

const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
const medidaSeccion = s => parseInt(s && s.medida_mm != null ? s.medida_mm : (s && s.alto_mm), 10) || 0;

/** Default por hoja de una corrediza (igual que pricing/aperturas.py y el 3D). */
export function hojaDefault(i, n) {
  if (i === n - 1) return { movimiento: 'izq', carril: i % 2 ? 'ext' : 'int' };
  return { movimiento: i % 2 === 0 ? 'der' : 'izq', carril: i % 2 === 0 ? 'int' : 'ext' };
}

/** Limpia una apertura (del cotizador o del snapshot). Null si no es dibujable. */
export function normalizarApertura(data, hojas) {
  if (!data || typeof data !== 'object') return null;
  const def = APERTURA_POR_CODIGO[String(data.codigo || '')];
  if (!def) return null;
  const out = { codigo: def.codigo };
  if (def.lado) out.lado = data.lado === 'der' ? 'der' : 'izq';
  if (def.porHoja) {
    const pedidas = Array.isArray(data.hojas) ? data.hojas : [];
    let n = parseInt(hojas != null ? hojas : pedidas.length, 10);
    if (!def.hojas.includes(n)) n = def.hojas[0];
    out.hojas = Array.from({ length: n }, (_, i) => {
      const base = hojaDefault(i, n);
      const h = pedidas[i] || {};
      return {
        movimiento: h.movimiento === 'izq' || h.movimiento === 'der' ? h.movimiento : base.movimiento,
        carril: h.carril === 'int' || h.carril === 'ext' ? h.carril : base.carril,
      };
    });
  }
  return out;
}

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
 *   apertura: { codigo, lado?, hojas?: [{movimiento, carril}] } | null  (REQ-047)
 *   color: clave de PERFIL_COLORES · color_terminacion: descripción cruda del tratamiento
 *   vidrio_composicion: string | null
 */
export function computarLayout(p) {
  const tipo = TIPOS_LAYOUT[p.tipo] ? p.tipo : 'pano_fijo';
  const T = TIPOS_LAYOUT[tipo];
  const W = Math.max(parseInt(p.ancho, 10) || 0, 1);
  const H = Math.max(parseInt(p.alto, 10) || 0, 1);

  const pw = T.puerta ? 60 : 55;
  const lf = T.puerta ? 55 : 40;

  const nH = T.hojas.includes(parseInt(p.hojas, 10)) ? parseInt(p.hojas, 10) : T.hojas[0];
  const hueco = { x: pw, y: pw, w: Math.max(W - 2 * pw, 1), h: Math.max(H - 2 * pw, 1) };

  const panos = [];
  if (T.modo === 'none') {
    panos.push({ x: hueco.x, y: hueco.y, w: hueco.w, h: hueco.h, movil: false, indice: 0 });
  } else {
    const colW = hueco.w / nH;
    for (let i = 0; i < nH; i++) {
      panos.push({ x: hueco.x + colW * i, y: hueco.y, w: colW, h: hueco.h,
                   movil: T.modo === 'slide' ? (i % 2 === 0) : true, indice: i });
    }
  }

  // --- Apertura → símbolo por paño ---
  const apertura = normalizarApertura(p.apertura, nH);
  const defAp = apertura ? APERTURA_POR_CODIGO[apertura.codigo] : null;
  panos.forEach((pano, i) => {
    pano.simbolo = null; pano.bisagra = null; pano.movimiento = null; pano.carril = null;
    if (!defAp) return;
    switch (defAp.simbolo) {
      case 'flechas': {
        const h = (apertura.hojas && apertura.hojas[i]) || hojaDefault(i, nH);
        pano.simbolo = 'flechas'; pano.movimiento = h.movimiento; pano.carril = h.carril;
        break;
      }
      case 'lateral':       pano.simbolo = 'lateral'; pano.bisagra = apertura.lado || 'izq'; break;
      case 'lateral_doble': pano.simbolo = 'lateral'; pano.bisagra = i === 0 ? 'izq' : 'der'; break;
      case 'oscilo':        pano.simbolo = 'oscilo';  pano.bisagra = apertura.lado || 'izq'; break;
      case 'vertice_arriba':
      case 'vertice_abajo':
      case 'rombo':         pano.simbolo = defAp.simbolo; break;
      default:              pano.simbolo = null;
    }
  });

  // --- Secciones por tirantes (sobre el vidrio del paño) ---
  const secsIn = Array.isArray(p.tirantes) && p.tirantes.length >= 2 ? p.tirantes : null;
  const vertical = p.tirantes_orientacion === 'vertical';
  panos.forEach(pano => {
    const inset = T.modo === 'none' ? 0 : lf;
    const vidrio = { x: pano.x + inset, y: pano.y + inset,
                     w: Math.max(pano.w - 2 * inset, 1), h: Math.max(pano.h - 2 * inset, 1) };
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
    ? (() => { const u = panos[panos.length - 1]; const a = clamp(u.w * 0.42, 60, u.w);
               return { x: u.x + u.w - a, y: u.y, w: a, h: u.h }; })()
    : null;

  // --- Cotas: parten el ancho TOTAL en los ejes de los travesaños ---
  const ejes = panos.slice(1).map(x => x.x);
  const bordes = [0, ...ejes, W];
  const anchos = panos.length > 1
    ? (() => {
        const segs = bordes.slice(0, -1).map((desde, i) => ({
          desde, hasta: bordes[i + 1], valor: Math.round(bordes[i + 1] - desde) }));
        const parcial = segs.slice(0, -1).reduce((a, s) => a + s.valor, 0);
        segs[segs.length - 1].valor = W - parcial;   // el último absorbe el redondeo
        return segs;
      })()
    : [];

  const cotas = { alto: H, ancho_total: W, anchos,
                  secciones: secsIn ? secsIn.map(medidaSeccion) : [],
                  secciones_orientacion: vertical ? 'vertical' : 'horizontal' };

  // --- Color del perfil ---
  const color = p.color && PERFIL_COLORES[p.color] ? p.color : mapColor(p.color_terminacion);

  return { tipo, modo: T.modo, puerta: T.puerta, ancho_mm: W, alto_mm: H, pw, lf, nH,
           hueco, panos, mosquitero, cotas, apertura, color, colorPerfil: PERFIL_COLORES[color] };
}

export default { computarLayout, normalizarApertura, hojaDefault, mapColor,
                 APERTURAS, APERTURA_POR_CODIGO, PERFIL_COLORES, TIPOS_LAYOUT };
