/**
 * Auditoría de las cotas de la elevación técnica (mismo espíritu que audit_tirantes.py).
 *
 * El proyecto no tiene runner de JS, así que esto se corre a mano:
 *   node audit_cotas.mjs
 *
 * Verifica que las cotas parciales cierren contra el total, que los planos de
 * referencia den los valores esperados, que las secciones por tirantes llenen
 * el vidrio y que nada explote con datos basura.
 */
import { computarLayout } from './static/js/abertura-layout.js';
import { svgElevacion } from './static/js/elevacion.js';

let fallas = 0;
const ok = (cond, msg) => { if (!cond) { fallas++; console.log('FALLA  ' + msg); } else console.log('OK     ' + msg); };

// --- Las cotas parciales siempre cierran contra el total ---
for (const [w, n] of [[1790, 2], [3630, 2], [2400, 3], [2401, 3], [3200, 4], [901, 3]]) {
  const L = computarLayout({ tipo: 'ventana_corrediza', ancho: w, alto: 1050, hojas: n });
  const suma = L.cotas.anchos.reduce((a, c) => a + c.valor, 0);
  ok(suma === w, `cotas de ${w}/${n} suman ${suma}`);
}

// --- Los planos de referencia ---
const p1 = computarLayout({ tipo: 'ventana_corrediza', ancho: 1790, alto: 1050, hojas: 2 });
ok(JSON.stringify(p1.cotas.anchos.map(c => c.valor)) === '[895,895]', 'plano 1: 895 + 895');
const p2 = computarLayout({ tipo: 'ventana_corrediza', ancho: 3630, alto: 1050, hojas: 2 });
ok(JSON.stringify(p2.cotas.anchos.map(c => c.valor)) === '[1815,1815]', 'plano 2: 1815 + 1815');
const p3 = computarLayout({ tipo: 'pano_fijo', ancho: 950, alto: 1050, hojas: 1 });
ok(p3.cotas.anchos.length === 0 && p3.cotas.ancho_total === 950, 'plano 3: paño único sin cotas parciales');

// --- Las secciones por tirantes llenan el vidrio exactamente ---
for (const orient of ['horizontal', 'vertical']) {
  const L = computarLayout({ tipo: 'pano_fijo', ancho: 1200, alto: 1600, hojas: 1,
    tirantes: [{ medida_mm: 700, ciego: false }, { medida_mm: 500, ciego: true }, { medida_mm: 400, ciego: false }],
    tirantes_orientacion: orient });
  const secs = L.panos[0].secciones;
  const eje = orient === 'vertical' ? 'w' : 'h';
  const suma = secs.reduce((a, s) => a + s[eje], 0);
  const disp = orient === 'vertical' ? L.panos[0].vidrio.w : L.panos[0].vidrio.h;
  ok(Math.abs(suma - disp) < 0.01, `secciones ${orient} llenan el vidrio (${suma.toFixed(1)} vs ${disp.toFixed(1)})`);
  ok(secs.filter(s => s.ciego).length === 1, `secciones ${orient}: 1 ciega`);
}

// --- Degradados: no romper con datos basura ---
const raros = [
  { tipo: 'inexistente', ancho: 0, alto: 0, hojas: 99 },
  { tipo: 'ventana_corrediza', ancho: '1790', alto: '1050', hojas: '2' },
  { tipo: 'pano_fijo', ancho: 300, alto: 300, hojas: 1, tirantes: [{ medida_mm: 0 }, { medida_mm: 0 }] },
  {},
];
for (const p of raros) {
  try {
    const svg = svgElevacion(p);
    ok(!/NaN|undefined/.test(svg) && svg.startsWith('<svg'), 'no rompe con ' + JSON.stringify(p).slice(0, 46));
  } catch (e) { fallas++; console.log('FALLA  excepción con ' + JSON.stringify(p).slice(0, 40) + ': ' + e.message); }
}

// --- El SVG no se rompe con texto hostil en la composición ---
const svgEsc = svgElevacion({ tipo: 'pano_fijo', ancho: 900, alto: 900, hojas: 1,
  vidrio_composicion: '<script>alert(1)</script>' });
ok(!svgEsc.includes('<script>'), 'escapa la composición del vidrio');

console.log('\n' + (fallas ? fallas + ' falla(s)' : 'todo OK'));
process.exit(fallas ? 1 : 0);
