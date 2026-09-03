/**
 * Auditoría de la elevación técnica: cotas, símbolos de apertura (REQ-047) y color.
 * Mismo espíritu que audit_tirantes.py. El proyecto no tiene runner de JS:
 *   node audit_cotas.mjs
 */
import { computarLayout, normalizarApertura, mapColor, APERTURAS } from './static/js/abertura-layout.js';
import { svgElevacion } from './static/js/elevacion.js';

let fallas = 0;
const ok = (cond, msg) => { if (!cond) fallas++; console.log((cond ? 'OK   ' : 'FALLA') + '  ' + msg); };
const cuenta = (s, re) => (s.match(re) || []).length;
const lineasSimbolo = s => cuenta(s, /stroke="#334155"/g);   // color exclusivo de los símbolos

// --- Cotas: las parciales cierran contra el total ---
for (const [w, n] of [[1790, 2], [3630, 2], [2400, 3], [2401, 3], [3200, 4], [901, 3]]) {
  const L = computarLayout({ tipo: 'ventana_corrediza', ancho: w, alto: 1050, hojas: n });
  ok(L.cotas.anchos.reduce((a, c) => a + c.valor, 0) === w, `cotas de ${w}/${n} suman ${w}`);
}
ok(JSON.stringify(computarLayout({ tipo: 'ventana_corrediza', ancho: 1790, alto: 1050, hojas: 2 }).cotas.anchos.map(c => c.valor)) === '[895,895]', 'plano 1: 895 + 895');

// --- Secciones por tirantes llenan el vidrio ---
for (const orient of ['horizontal', 'vertical']) {
  const L = computarLayout({ tipo: 'pano_fijo', ancho: 1200, alto: 1600, hojas: 1,
    tirantes: [{ medida_mm: 700 }, { medida_mm: 500, ciego: true }, { medida_mm: 400 }], tirantes_orientacion: orient });
  const eje = orient === 'vertical' ? 'w' : 'h';
  const suma = L.panos[0].secciones.reduce((a, s) => a + s[eje], 0);
  ok(Math.abs(suma - L.panos[0].vidrio[eje]) < 0.01, `secciones ${orient} llenan el vidrio`);
}

// --- Aperturas: los 11 tipos producen su símbolo ---
const base = { ancho: 1500, alto: 1200, vidrio_composicion: '4mm' };
const casos = [
  ['pano_fijo',          'pano_fijo',           1, 0],  // sin símbolo
  ['corrediza',          'ventana_corrediza',   2, 0],  // flechas: no usan el color de símbolo
  ['abrir_1',            'ventana_batiente',    1, 2],
  ['abrir_2',            'ventana_batiente',    2, 4],
  ['oscilobatiente',     'ventana_oscilo',      1, 4],
  ['banderola',          'ventana_proyectante', 1, 2],
  ['brazo_empuje',       'ventana_proyectante', 1, 2],
  ['proyectante_tijera', 'ventana_proyectante', 1, 4],
  ['puerta',             'puerta_batiente',     1, 2],
  ['puerta_doble',       'puerta_batiente',     2, 4],
  ['puerta_corrediza',   'puerta_corrediza',    2, 0],
];
ok(APERTURAS.length === 11 && casos.length === 11, 'catálogo de 11 aperturas cubierto');
for (const [codigo, tipo, hojas, lineas] of casos) {
  const svg = svgElevacion({ ...base, tipo, hojas, apertura: { codigo } });
  ok(svg.startsWith('<svg') && !/NaN|undefined/.test(svg), `${codigo}: SVG válido`);
  ok(lineasSimbolo(svg) === lineas, `${codigo}: ${lineas} línea(s) de símbolo (hay ${lineasSimbolo(svg)})`);
}

// --- Flechas y carril en corredizas ---
const corr = svgElevacion({ ...base, tipo: 'ventana_corrediza', hojas: 2,
  apertura: { codigo: 'corrediza', hojas: [{ movimiento: 'der', carril: 'int' }, { movimiento: 'izq', carril: 'ext' }] } });
ok(cuenta(corr, /<polygon/g) === 2, 'corrediza 2 hojas: 2 flechas');
ok(cuenta(corr, />Int\.</g) === 1 && cuenta(corr, />Ext\.</g) === 1, 'corrediza: Int. y Ext. según el carril de cada hoja');
const corrDefault = normalizarApertura({ codigo: 'corrediza' }, 4);
ok(corrDefault.hojas.map(h => h.movimiento).join() === 'der,izq,der,izq', 'default 4 hojas: der,izq,der,izq');

// --- Lado de la bisagra espeja las diagonales ---
const L1 = computarLayout({ ...base, tipo: 'ventana_batiente', hojas: 1, apertura: { codigo: 'abrir_1', lado: 'izq' } });
const L2 = computarLayout({ ...base, tipo: 'ventana_batiente', hojas: 1, apertura: { codigo: 'abrir_1', lado: 'der' } });
ok(L1.panos[0].bisagra === 'izq' && L2.panos[0].bisagra === 'der', 'abrir_1: el lado llega al paño');
const D1 = computarLayout({ ...base, tipo: 'ventana_batiente', hojas: 2, apertura: { codigo: 'abrir_2' } });
ok(D1.panos[0].bisagra === 'izq' && D1.panos[1].bisagra === 'der', 'abrir_2: bisagras exteriores, convergen al centro');

// --- Sin apertura (ítems viejos): sin símbolo, sin romper ---
const viejo = svgElevacion({ ...base, tipo: 'ventana_batiente', hojas: 1 });
ok(lineasSimbolo(viejo) === 0 && cuenta(viejo, /<polygon/g) === 0, 'sin apertura: ningún símbolo');
ok(svgElevacion({ ...base, tipo: 'pano_fijo', hojas: 1, apertura: { codigo: 'inexistente' } }).startsWith('<svg'), 'apertura inválida: no rompe');
ok(svgElevacion({ ...base, tipo: 'ventana_batiente', hojas: 1, apertura: { codigo: 'abrir_1' } }, { apertura: false }) &&
   lineasSimbolo(svgElevacion({ ...base, tipo: 'ventana_batiente', hojas: 1, apertura: { codigo: 'abrir_1' } }, { apertura: false })) === 0,
   'opts.apertura=false apaga los símbolos');

// --- Color del perfil por terminación ---
ok(mapColor('ANODIZADO BRONCE') === 'bronce' && mapColor('NEGRO') === 'negro' && mapColor('') === 'blanco', 'mapColor por descripción');
const negro = svgElevacion({ ...base, tipo: 'pano_fijo', hojas: 1, color_terminacion: 'NEGRO' });
const blanco = svgElevacion({ ...base, tipo: 'pano_fijo', hojas: 1, color_terminacion: 'BLANCO' });
ok(negro.includes('stroke="#1b1d1f"'), 'terminación NEGRO pinta el perfil #1b1d1f');
ok(blanco.includes('stroke="#f3f4f4"') && blanco.includes('stroke="#111418"'), 'BLANCO: perfil blanco con contorno oscuro (se ve sobre papel)');
ok(svgElevacion({ ...base, tipo: 'pano_fijo', hojas: 1, color: 'madera' }).includes('stroke="#6a4526"'), 'color por clave directa (cotizador)');

// --- Datos basura no rompen ---
for (const p of [{ tipo: 'inexistente', ancho: 0, alto: 0, hojas: 99 }, {}, { tipo: 'pano_fijo', ancho: 300, alto: 300, tirantes: [{ medida_mm: 0 }, { medida_mm: 0 }] }]) {
  const svg = svgElevacion(p);
  ok(!/NaN|undefined/.test(svg) && svg.startsWith('<svg'), 'no rompe con ' + JSON.stringify(p).slice(0, 40));
}
ok(!svgElevacion({ ...base, tipo: 'pano_fijo', hojas: 1, vidrio_composicion: '<script>x</script>' }).includes('<script>'), 'escapa la composición');

console.log('\n' + (fallas ? fallas + ' falla(s)' : 'todo OK'));
process.exit(fallas ? 1 : 0);
