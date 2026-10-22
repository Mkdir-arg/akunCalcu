/**
 * Auditoría del plano de estructuras (REQ-062): geometría contra los fixtures
 * compartidos con pricing/tests.py, y SVG sin NaN, con ids únicos y texto escapado.
 *   node audit_estructura.mjs
 */
import fs from 'node:fs';
import { svgElevacion } from './static/js/elevacion.js?v=3';
import {
  etiquetarModulos, detectarJuntas, validarEstructura, envolvente, svgEstructura, svgDibujo,
} from './static/js/estructura.js';

let fallas = 0;
const ok = (cond, msg) => { if (!cond) fallas++; console.log((cond ? 'OK   ' : 'FALLA') + '  ' + msg); };
const cuenta = (s, re) => (s.match(re) || []).length;
const ids = s => [...s.matchAll(/\sid="([^"]*)"/g)].map(m => m[1]);
const unicos = a => new Set(a).size === a.length;

// --- Geometría contra los fixtures compartidos ---
const fixtures = JSON.parse(fs.readFileSync(new URL('./pricing/fixtures_estructura_geometria.json', import.meta.url), 'utf8'));
for (const c of fixtures) {
  const lb = etiquetarModulos(c.modulos);
  ok(JSON.stringify(lb) === JSON.stringify(c.etiquetas), `${c.nombre}: etiquetas ${lb.join(',')}`);
  if (c.modulos.length <= 12) {
    const js = detectarJuntas(c.modulos).map(j => ({ a: lb[j.a], b: lb[j.b], orientacion: j.orientacion, largo_mm: j.largo }));
    ok(JSON.stringify(js) === JSON.stringify(c.juntas), `${c.nombre}: juntas ${JSON.stringify(js)}`);
  }
  const v = validarEstructura({ pared: c.pared, modulos: c.modulos });
  ok(v.errores.length === c.errores_count, `${c.nombre}: ${c.errores_count} error(es) (hay ${v.errores.length})`);
}
ok(JSON.stringify(envolvente([{ x: 600, y: 0, ancho: 900, alto: 2050 }, { x: 1800, y: 900, ancho: 1500, alto: 1100 }, { x: 3300, y: 900, ancho: 700, alto: 1100 }]))
  === '{"x":600,"y":0,"ancho":3400,"alto":2050}', 'envolvente de la maqueta: 600,0 3400x2050');
ok(JSON.stringify(envolvente([])) === '{"x":0,"y":0,"ancho":0,"alto":0}', 'envolvente vacía');
const inv = validarEstructura({ pared: { ancho: 5000, alto: 2600 }, modulos: [{ x: 0, y: 0, ancho: 1000, alto: 1000 }, { x: 500, y: 500, ancho: 1000, alto: 1000 }, { x: 3000, y: 0, ancho: 800, alto: 900 }] });
ok(JSON.stringify(inv.indices) === '[0,1]' && /^M1 y M2 se superponen/.test(inv.errores[0]), 'superposición marca los dos módulos y nombra las etiquetas');
ok(/^M1 se sale de la pared/.test(validarEstructura({ pared: { ancho: 3000, alto: 2600 }, modulos: [{ x: 2500, y: 0, ancho: 1000, alto: 1000 }] }).errores[0]), 'mensaje de fuera de la pared');

// --- Casos de dibujo ---
const dib = (tipo, apertura, hojas, extra) => ({ tipo, ancho: 0, alto: 0, hojas, vidrio_composicion: '4mm', apertura: { codigo: apertura, ...(extra || {}) } });
const base = {
  tipo: 'estructura', pared: { ancho: 5000, alto: 2600 }, perfil_union: true, color_terminacion: 'Blanco',
  modulos: [
    { etiqueta: 'M1', x: 600, y: 0, ancho: 900, alto: 2050, dibujo: dib('puerta_batiente', 'puerta', 1, { lado: 'izq' }) },
    { etiqueta: 'M2', x: 1800, y: 900, ancho: 1500, alto: 1100, dibujo: { ...dib('ventana_corrediza', 'corrediza', 2), mosquitero: true } },
    { etiqueta: 'M3', x: 3300, y: 900, ancho: 700, alto: 1100, dibujo: dib('pano_fijo', 'pano_fijo', 1) },
  ],
};
const sinConfigurar = { ...base, modulos: [...base.modulos, { x: 100, y: 2100, ancho: 400, alto: 400, dibujo: null }] };
const hostil = { ...base, color_terminacion: '"><script>x</script>',
  modulos: base.modulos.map((m, i) => i === 1 ? { ...m, etiqueta: '<b>x</b>' } : m) };

const variantes = {
  'pared + cotas': [base, {}],
  'sin pared (miniatura)': [base, { pared: false, cotas: false, etiquetas: false }],
  'sin pared con cotas': [base, { pared: false, cotas: true }],
  'interactivo con selección e inválidos': [base, { interactivo: true, seleccion: 1, invalidos: [0], guias: { gx: [1500, 1800], gy: [900] } }],
  'soloContorno': [base, { soloContorno: true, interactivo: true, seleccion: 2 }],
  'módulo sin configurar': [sinConfigurar, { interactivo: true }],
  'sin perfil de unión': [{ ...base, perfil_union: false }, {}],
  'sin aperturas dibujadas': [base, { apertura: false }],
  'sin etiquetas ni cotas': [base, { etiquetas: false, cotas: false }],
  'sin módulos': [{ ...base, modulos: [] }, {}],
  'p vacío': [{ tipo: 'estructura' }, {}],
  'dibujo antes de guardar (sin juntas, sin pared)': [{ tipo: 'estructura', modulos: base.modulos }, { pared: false }],
  'con juntas explícitas': [{ ...base, juntas: [{ x1: 3300, y1: 900, x2: 3300, y2: 2000, orientacion: 'vertical', largo_mm: 1100 }] }, {}],
};
for (const [nombre, [p, o]] of Object.entries(variantes)) {
  const svg = svgEstructura(p, o);
  ok(svg.startsWith('<svg') && svg.endsWith('</svg>'), `${nombre}: SVG`);
  ok(!/NaN|undefined|Infinity/.test(svg), `${nombre}: sin NaN ni undefined`);
  ok(unicos(ids(svg)), `${nombre}: ids únicos (${ids(svg).length})`);
}

// --- idPrefijo: dos SVG en la misma página no comparten ids ---
const a = svgEstructura(base, { idPrefijo: 'a-' }), b = svgEstructura(base, { idPrefijo: 'b-' });
const idsA = ids(a), idsB = ids(b);
ok(idsA.length >= 2 && !idsA.some(i => idsB.includes(i)), `idPrefijo distinto: ids sin choque (${idsA.length} + ${idsB.length})`);
ok(idsA.every(i => i.startsWith('a-')), 'todos los ids llevan el prefijo');
ok(a.includes('url(#a-hatch)') && a.includes('url(#a-m1-malla'), 'las referencias url(#...) usan el prefijo');

// --- Interactivo ---
const it = svgEstructura(base, { interactivo: true, seleccion: 1, invalidos: [2] });
ok(cuenta(it, /<g class="mod" data-idx="\d"/g) === 3 && it.includes('tabindex="0"'), 'interactivo: un <g class="mod" data-idx> por módulo');
ok(it.includes('stroke="#4f46e5"') && it.includes('stroke="#dc2626"'), 'selección en índigo e inválidos en rojo');
ok(!svgEstructura(base, {}).includes('class="mod"'), 'no interactivo: sin grupos');
ok(cuenta(svgEstructura(base, { soloContorno: true }), /<rect/g) < cuenta(svgEstructura(base, {}), /<rect/g), 'soloContorno dibuja menos que el plano completo');

// --- Juntas: ámbar con perfil, punteada sin perfil ---
ok(svgEstructura(base, {}).includes('stroke="#d97706"'), 'junta con perfil: ámbar');
const sinPerfil = svgEstructura({ ...base, perfil_union: false }, {});
ok(!sinPerfil.includes('stroke="#d97706"') && sinPerfil.includes('stroke="#64748b"'), 'junta sin perfil: punteada gris');
ok(svgEstructura(sinConfigurar, {}).includes('Sin configurar'), 'módulo sin dibujo: "Sin configurar"');

// --- Despachador ---
const comun = dib('ventana_corrediza', 'corrediza', 2);
comun.ancho = 1500; comun.alto = 1100;
ok(svgDibujo(comun) === svgElevacion(comun), 'svgDibujo de un ítem común = svgElevacion');
ok(svgDibujo(comun, { cotas: false }) === svgElevacion(comun, { cotas: false }), 'svgDibujo pasa las opts a svgElevacion');
ok(svgDibujo(base, { idPrefijo: 'q-' }) === svgEstructura(base, { idPrefijo: 'q-' }), 'svgDibujo de una estructura = svgEstructura');

// --- Escape ---
const h = svgEstructura(hostil, { interactivo: true, idPrefijo: '"><x' });
ok(!h.includes('<script>') && !h.includes('<b>') && !h.includes('<x'), 'escapa etiqueta, color e idPrefijo');
ok(unicos(ids(h)), 'ids únicos con prefijo hostil');

console.log('\n' + (fallas ? fallas + ' falla(s)' : 'todo OK'));
process.exit(fallas ? 1 : 0);
