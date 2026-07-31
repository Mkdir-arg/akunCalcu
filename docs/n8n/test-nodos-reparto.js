// Reproduce FIX-020: el workflow procesaba 1 mail por lote y descartaba el resto.
// Los jsCode "nuevos" se leen del JSON versionado -> se testea lo que se despliega.
const fs = require('fs');
const assert = require('assert');

const WF = JSON.parse(fs.readFileSync('docs/n8n/n8n-solicitudes-reparto.json', 'utf8'));
const code = (name) => WF.nodes.find((n) => n.name === name).parameters.jsCode;
const mode = (name) => WF.nodes.find((n) => n.name === name).parameters.mode;

// --- jsCode ANTERIOR al fix (copiado del workflow en vivo, para reproducir el bug) ---
const VIEJO_EXTRAER = `const msg = $input.first().json;
let from='';
if(msg.from){ from = (typeof msg.from==='string') ? msg.from : (msg.from.text || (msg.from.value && msg.from.value[0] && msg.from.value[0].address) || ''); }
let body = msg.text || '';
if(!body && msg.html) body = String(msg.html).replace(/<[^>]+>/g,' ');
if(!body) body = msg.snippet || '';
body = body.replace(/\\s+/g,' ').trim().slice(0,4000);
return [{ json:{ gmail_id: msg.id||'', gmail_thread_id: msg.threadId||msg.id||'', subject: msg.subject||'', from: from, body: body } }];`;

const VIEJO_IA = `let r={};
try{ r=JSON.parse($input.first().json.choices[0].message.content); }catch(e){ r={es_presupuesto:false}; }
r.gmail_thread_id=($('Extraer mail').first().json.gmail_thread_id)||'';
return [{ json:r }];`;

// --- Runtime mínimo de n8n ---
function runAllItems(jsCode, items, refs = {}) {
  const $input = { first: () => items[0], all: () => items };
  const $ = (name) => ({ first: () => refs[name][0], all: () => refs[name] });
  return new Function('$input', '$', '$json', jsCode)($input, $, items[0] ? items[0].json : {});
}

function runEachItem(jsCode, items, refs = {}) {
  return items.map((item, idx) => {
    const $ = (name) => {
      const src = refs[name];
      if (!src) throw new Error(`nodo inexistente: ${name}`);
      const paired = item.pairedItem ? item.pairedItem.item : idx;
      if (!src[paired]) throw new Error('pairing roto');
      return { item: src[paired], first: () => src[0], all: () => src };
    };
    return new Function('$json', '$', jsCode)(item.json, $);
  });
}

// --- Lote de prueba: 5 mails (3 formularios + 2 de ruido), como los polls reales ---
const form = (nombre, email, tel, loc, msg) =>
  `Nombre ${nombre} E-mail ${email} [${email}] Teléfono ${tel} Barrio / Localidad ${loc} ` +
  `Escribí acá tu consulta o mensaje ${msg} Enviado desde AKUN Aberturas [https://akunaberturas.com.ar]`;

// Datos de contacto ficticios a proposito: lo que este test verifica es el ruteo del
// lote, no la heuristica anti-spam (esa se testea con casos reales en solicitudes/tests.py).
const LOTE = [
  { json: { id: 'm0', threadId: 't0', subject: 'Nuevo formulario web', from: { text: '"AKUN" <akunaberturas@gmail.com>' },
      text: form('Cliente Uno', 'uno@ejemplo.com', '01122223333', 'Ciudad Evita', 'Hola queria saber si hacen ventanas a medida') } },
  { json: { id: 'm1', threadId: 't1', subject: '¡Alerta de seguridad: tu antivirus finalizó!', from: { text: '"McAfee" <mcafee@email.mcafee.com>' }, text: 'Renueva tu proteccion' } },
  { json: { id: 'm2', threadId: 't2', subject: 'Nuevo formulario web', from: { text: '"AKUN" <akunaberturas@gmail.com>' },
      text: form('Cliente Dos', 'dos@ejemplo.com', '1144445555', 'Moreno', 'Presupuesto Linea Modena con mosquiteros 180x150') } },
  { json: { id: 'm3', threadId: 't3', subject: 'Alerta de seguridad', from: { text: '"Google" <no-reply@accounts.google.com>' }, text: 'Un nuevo acceso en el dispositivo Motorola' } },
  { json: { id: 'm4', threadId: 't4', subject: 'Nuevo formulario web', from: { text: '"AKUN" <akunaberturas@gmail.com>' },
      text: form('Cliente Tres', 'tres@ejemplo.com', '161651', 'TABLADA', 'asfa') } },
];

let fallos = 0;
const check = (nombre, fn) => {
  try { fn(); console.log(`  OK   ${nombre}`); }
  catch (e) { fallos++; console.log(`  FALLA ${nombre}\n        ${e.message}`); }
};

console.log('\n== 1. El bug (codigo anterior) ==');
check('Extraer mail viejo: de 5 mails devuelve solo 1', () => {
  assert.strictEqual(runAllItems(VIEJO_EXTRAER, LOTE).length, 1);
});
check('Extraer mail viejo: los mails m1..m4 se pierden', () => {
  const ids = runAllItems(VIEJO_EXTRAER, LOTE).map((i) => i.json.gmail_id);
  assert.deepStrictEqual(ids, ['m0']);
});

console.log('\n== 2. El fix: no se pierde ningun mail ==');
check('los 3 nodos Code quedaron en runOnceForEachItem', () => {
  for (const n of ['Extraer mail', 'Parsear Formulario', 'Parsear IA']) {
    assert.strictEqual(mode(n), 'runOnceForEachItem', `${n} sigue en modo all-items`);
  }
});

const extraidos = runEachItem(code('Extraer mail'), LOTE);
check('Extraer mail: 5 entran -> 5 salen', () => {
  assert.strictEqual(extraidos.length, 5);
});
check('Extraer mail: cada item conserva su propio id/thread/subject', () => {
  assert.deepStrictEqual(extraidos.map((i) => i.json.gmail_id), ['m0', 'm1', 'm2', 'm3', 'm4']);
  assert.deepStrictEqual(extraidos.map((i) => i.json.gmail_thread_id), ['t0', 't1', 't2', 't3', 't4']);
});
check('Extraer mail: normaliza el from y aplana el body', () => {
  assert.strictEqual(extraidos[1].json.from, '"McAfee" <mcafee@email.mcafee.com>');
  assert.ok(!/\s\s/.test(extraidos[0].json.body));
});

console.log('\n== 3. Rama formulario web (3 de los 5) ==');
// El IF "Es Formulario Web" manda a esta rama los indices 0, 2 y 4.
const aForm = [0, 2, 4].map((i) => ({ ...extraidos[i], pairedItem: { item: i } }));
const parseados = runEachItem(code('Parsear Formulario'), aForm, { 'Extraer mail': extraidos });
check('Parsear Formulario: 3 entran -> 3 salen', () => {
  assert.strictEqual(parseados.length, 3);
});
check('Parsear Formulario: extrae los datos de cada formulario, no del primero', () => {
  assert.deepStrictEqual(parseados.map((i) => i.json.nombre_cliente), ['Cliente Uno', 'Cliente Dos', 'Cliente Tres']);
  assert.deepStrictEqual(parseados.map((i) => i.json.telefono), ['01122223333', '1144445555', '161651']);
  assert.deepStrictEqual(parseados.map((i) => i.json.email), ['uno@ejemplo.com', 'dos@ejemplo.com', 'tres@ejemplo.com']);
  assert.deepStrictEqual(parseados.map((i) => i.json.gmail_thread_id), ['t0', 't2', 't4']);
});
check('Parsear Formulario: el primer formulario conserva localidad y consulta', () => {
  assert.match(parseados[0].json.mensaje, /^Localidad: Ciudad Evita\. .*ventanas a medida/);
});

console.log('\n== 4. Rama IA: el thread_id no se cruza entre mails ==');
// El IF manda a la rama IA los indices 1 y 3. La respuesta de OpenAI llega pareada a ellos.
const aIA = [1, 3].map((i) => ({
  json: { choices: [{ message: { content: JSON.stringify({ es_presupuesto: false }) } }] },
  pairedItem: { item: i },
}));

check('BUG viejo: los 2 items reciben el thread del mail #1 (t0), que no es el suyo', () => {
  const viejo = runAllItems(VIEJO_IA, aIA, { 'Extraer mail': extraidos });
  assert.strictEqual(viejo.length, 1);            // ademas pierde uno
  assert.strictEqual(viejo[0].json.gmail_thread_id, 't0');  // y t0 no corresponde a m1 ni a m3
});
check('fix: cada item recibe SU thread (t1 y t3) via .item', () => {
  const nuevo = runEachItem(code('Parsear IA'), aIA, { 'Extraer mail': extraidos });
  assert.strictEqual(nuevo.length, 2);
  assert.deepStrictEqual(nuevo.map((i) => i.json.gmail_thread_id), ['t1', 't3']);
});
check('fix: cae al thread del trigger si el pairing con Extraer mail se rompe', () => {
  const refs = { 'Nuevo mail': LOTE };  // sin 'Extraer mail' -> primer try falla
  const nuevo = runEachItem(code('Parsear IA'), aIA, refs);
  assert.deepStrictEqual(nuevo.map((i) => i.json.gmail_thread_id), ['t1', 't3']);
});
check('fix: respuesta no-JSON de OpenAI no rompe el nodo', () => {
  const roto = [{ json: { choices: [{ message: { content: 'lo siento, no puedo' } }] }, pairedItem: { item: 1 } }];
  const nuevo = runEachItem(code('Parsear IA'), roto, { 'Extraer mail': extraidos });
  assert.strictEqual(nuevo[0].json.es_presupuesto, false);
  assert.strictEqual(nuevo[0].json.gmail_thread_id, 't1');
});

console.log(`\n${fallos === 0 ? 'TODO OK' : fallos + ' FALLA(S)'}\n`);
process.exit(fallos === 0 ? 0 : 1);
