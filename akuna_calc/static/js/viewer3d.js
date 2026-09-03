/**
 * Visor 3D de aberturas — módulo autocontenido para el cotizador de presupuestos.
 *
 * Uso desde el host (React/Babel):
 *   window.__loadAkunViewer().then(v => v.mount(container, params))
 *
 * params = { tipo, ancho, alto, hojas, mosquitero, premarco, vidrio }
 *   - tipo: clave de TIPOS (ventana_corrediza | ventana_batiente | ventana_oscilo |
 *           ventana_proyectante | pano_fijo | puerta_batiente | puerta_corrediza)
 *   - ancho / alto: milímetros
 *   - hojas: cantidad de hojas (se acota a las válidas del tipo)
 *   - mosquitero / premarco: boolean
 *   - vidrio: incoloro | dvh | gris | bronce | esmerilado
 *   - tirantes: [{ medida_mm, ciego }] (opcional) — secciones divididas por tirantes
 *   - tirantes_orientacion: horizontal (bandas, default) | vertical (columnas)
 *
 * NO requiere build: se carga como ESM vía import map (three desde CDN).
 */
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { computarLayout, normalizarApertura, APERTURA_POR_CODIGO } from './abertura-layout.js?v=2';
import { crearOverlayCotas } from './cotas3d.js';

const TIPOS = {
  ventana_corrediza:  { hojas: [2, 3, 4], modo: 'slide',   puerta: false, open: 0.22 },
  ventana_batiente:   { hojas: [1, 2],    modo: 'swing',   puerta: false, open: 0.20 },
  ventana_oscilo:     { hojas: [1],       modo: 'tilt',    puerta: false, open: 0.55 },
  ventana_proyectante:{ hojas: [1],       modo: 'project', puerta: false, open: 0.55 },
  pano_fijo:          { hojas: [1],       modo: 'none',    puerta: false, open: 0.0 },
  puerta_batiente:    { hojas: [1, 2],    modo: 'swing',   puerta: true,  open: 0.22 },
  puerta_corrediza:   { hojas: [2, 3],    modo: 'slide',   puerta: true,  open: 0.22 },
};
const PERFILES = {
  blanco:    { color: 0xf3f4f4, metalness: 0.15, roughness: 0.45 },
  negro:     { color: 0x1b1d1f, metalness: 0.40, roughness: 0.38 },
  antracita: { color: 0x373b3f, metalness: 0.50, roughness: 0.36 },
  bronce:    { color: 0x54422e, metalness: 0.75, roughness: 0.35 },   // anodizado bronce
  madera:    { color: 0x6a4526, metalness: 0.05, roughness: 0.72 },
  aluminio:  { color: 0xbfc3c8, metalness: 0.90, roughness: 0.28 },
};
const VIDRIOS = {
  incoloro:   { color: 0xdff0f6, transmission: 0.95, roughness: 0.05, opacity: 0.30, dvh: false },
  dvh:        { color: 0xe6f2f7, transmission: 0.93, roughness: 0.06, opacity: 0.30, dvh: true },
  gris:       { color: 0x8b969d, transmission: 0.80, roughness: 0.08, opacity: 0.55, dvh: false },
  bronce:     { color: 0x9c7b4f, transmission: 0.80, roughness: 0.08, opacity: 0.55, dvh: false },
  esmerilado: { color: 0xeaeff2, transmission: 0.45, roughness: 0.60, opacity: 0.78, dvh: false },
};

let renderer, scene, camera, controls, host = null, ro = null, running = false;
let perfilMat, glassMat, spacerMat, handleMat, grooveMat, mallaTex, mallaMat;
let windowGroup = null, movers = [], curOpen = 0, targetOpen = 0, framed = false;
let overlayCotas = null, layoutCotas = null;

const state = { tipo: 'pano_fijo', ancho: 1200, alto: 1500, hojas: 1,
                mosquitero: false, premarco: false, vidrio: 'incoloro', color: 'blanco',
                tirantes: null, tirantesOrientacion: 'horizontal',
                cotas: true, vidrioComposicion: null, sentidos: null, apertura: null };

function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }

function initEngine() {
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.75));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;
  renderer.outputColorSpace = THREE.SRGBColorSpace;

  scene = new THREE.Scene();
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(renderer), 0.04).texture;

  camera = new THREE.PerspectiveCamera(42, 1, 0.05, 100);
  camera.position.set(1.7, 0.9, 3.2);

  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.enablePan = false;
  controls.minDistance = 0.8;
  controls.maxDistance = 16;

  scene.add(new THREE.AmbientLight(0xffffff, 0.35));
  const key = new THREE.DirectionalLight(0xffffff, 2.3);
  key.position.set(3.5, 5.5, 4.5); key.castShadow = true;
  key.shadow.mapSize.set(2048, 2048);
  key.shadow.camera.near = 0.5; key.shadow.camera.far = 30;
  key.shadow.camera.left = -5; key.shadow.camera.right = 5;
  key.shadow.camera.top = 5; key.shadow.camera.bottom = -5;
  key.shadow.bias = -0.0004;
  scene.add(key);
  const fill = new THREE.DirectionalLight(0xffffff, 0.5);
  fill.position.set(-4, 2, 3); scene.add(fill);

  const ground = new THREE.Mesh(new THREE.PlaneGeometry(50, 50), new THREE.ShadowMaterial({ opacity: 0.22 }));
  ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; ground.name = '__ground';
  scene.add(ground);

  perfilMat = new THREE.MeshStandardMaterial(PERFILES.blanco);
  glassMat = new THREE.MeshPhysicalMaterial({ color: 0xdff0f6, metalness: 0, roughness: 0.05,
    transmission: 0.95, thickness: 0.02, ior: 1.5, transparent: true, opacity: 0.3,
    envMapIntensity: 1.6, clearcoat: 0.18, clearcoatRoughness: 0.1 });
  spacerMat = new THREE.MeshStandardMaterial({ color: 0x8a9199, metalness: 0.7, roughness: 0.4 });
  handleMat = new THREE.MeshStandardMaterial({ color: 0x2b2e31, metalness: 0.85, roughness: 0.32 });
  grooveMat = new THREE.MeshStandardMaterial({ color: 0x8a8d90, metalness: 0.3, roughness: 0.6 });

  mallaTex = mallaTexture();
  mallaMat = new THREE.MeshBasicMaterial({ map: mallaTex, transparent: true, opacity: 0.85,
    color: 0x1c2024, side: THREE.DoubleSide, depthWrite: false });
}

function mallaTexture() {
  const c = document.createElement('canvas'); c.width = c.height = 64;
  const x = c.getContext('2d'); x.clearRect(0, 0, 64, 64);
  x.strokeStyle = 'rgba(28,32,36,1)'; x.lineWidth = 1.4;
  for (let i = 0; i <= 64; i += 5) {
    x.beginPath(); x.moveTo(i + .5, 0); x.lineTo(i + .5, 64); x.stroke();
    x.beginPath(); x.moveTo(0, i + .5); x.lineTo(64, i + .5); x.stroke();
  }
  const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; return t;
}

// ---- Primitivas ----
function extrudedRing(W, H, pw, depth, bevel = 0.0035) {
  const s = new THREE.Shape();
  s.moveTo(-W / 2, -H / 2); s.lineTo(W / 2, -H / 2); s.lineTo(W / 2, H / 2); s.lineTo(-W / 2, H / 2); s.lineTo(-W / 2, -H / 2);
  const iw = W / 2 - pw, ih = H / 2 - pw;
  const hole = new THREE.Path();
  hole.moveTo(-iw, -ih); hole.lineTo(iw, -ih); hole.lineTo(iw, ih); hole.lineTo(-iw, ih); hole.lineTo(-iw, -ih);
  s.holes.push(hole);
  const geo = new THREE.ExtrudeGeometry(s, { depth, bevelEnabled: true, bevelThickness: bevel,
    bevelSize: bevel, bevelSegments: 1, steps: 1, curveSegments: 1 });
  geo.translate(0, 0, -depth / 2);
  return geo;
}
function frame(W, H, pw, pd, z) {
  const g = new THREE.Group();
  const ring = new THREE.Mesh(extrudedRing(W, H, pw, pd), perfilMat);
  ring.position.z = z; ring.castShadow = true; ring.receiveShadow = true; g.add(ring);
  if (W - pw > 0.12 && H - pw > 0.12) {
    const gr = new THREE.Mesh(extrudedRing(W - pw * 0.9, H - pw * 0.9, 0.006, 0.004), grooveMat);
    gr.position.z = z + pd / 2 - 0.003; g.add(gr);
  }
  const bd = pd * 0.42, open = Math.max(W - 2 * pw, 0.02);
  if (open > 0.05) {
    const bead = new THREE.Mesh(extrudedRing(open + 0.018, Math.max(H - 2 * pw, 0.05) + 0.018, 0.011, bd, 0.002), perfilMat);
    bead.position.z = z + pd / 2 - bd / 2 - 0.002; g.add(bead);
  }
  return g;
}
function glass(W, H, z, def) {
  const grp = new THREE.Group();
  const mk = zz => { const m = new THREE.Mesh(new THREE.BoxGeometry(W, H, 0.005), glassMat); m.position.set(0, 0, zz); return m; };
  if (def.dvh) {
    grp.add(mk(z - 0.008)); grp.add(mk(z + 0.008));
    const sh = 0.012, sd = 0.018;
    const sp = (x, y, w, h) => { const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, sd), spacerMat); m.position.set(x, y, z); grp.add(m); };
    sp(0, H / 2 - sh / 2, W, sh); sp(0, -H / 2 + sh / 2, W, sh); sp(-W / 2 + sh / 2, 0, sh, H); sp(W / 2 - sh / 2, 0, sh, H);
  } else grp.add(mk(z));
  return grp;
}
function handle() {
  const g = new THREE.Group();
  g.add(new THREE.Mesh(new RoundedBoxGeometry(0.028, 0.10, 0.018, 2, 0.005), handleMat));
  const lever = new THREE.Mesh(new RoundedBoxGeometry(0.018, 0.018, 0.10, 2, 0.005), handleMat);
  lever.position.set(0, -0.025, 0.05); g.add(lever); return g;
}

function setGlassMaterial(def) {
  glassMat.color.setHex(def.color); glassMat.transmission = def.transmission;
  glassMat.roughness = def.roughness; glassMat.opacity = def.opacity;
}

function build() {
  if (windowGroup) { scene.remove(windowGroup); windowGroup.traverse(o => { if (o.geometry) o.geometry.dispose(); }); }
  const g = new THREE.Group(); movers = [];
  const T = TIPOS[state.tipo] || TIPOS.pano_fijo;
  const W = state.ancho / 1000, H = state.alto / 1000, puerta = T.puerta;
  // REQ-047: la apertura manda sobre la familia. Banderola/brazo/tijera comparten
  // tipologia pero abren distinto; un paño de abrir puede tener la bisagra a la
  // derecha; una corrediza define movimiento y carril por hoja.
  const ap = state.apertura;
  const apDef = ap ? APERTURA_POR_CODIGO[ap.codigo] : null;
  let modo = T.modo;
  if (apDef) {
    switch (apDef.simbolo) {
      case 'flechas':        modo = 'slide'; break;
      case 'lateral':
      case 'lateral_doble':  modo = 'swing'; break;
      case 'oscilo':         modo = 'tilt'; break;
      case 'vertice_arriba': modo = 'tilt'; break;      // bisagra abajo, abre por arriba
      case 'vertice_abajo':
      case 'rombo':          modo = 'project'; break;   // bisagra arriba, abre por abajo
      case 'ninguno':        modo = 'none'; break;
    }
  }
  const ladoBisagra = (ap && ap.lado === 'der') ? 'der' : 'izq';
  const pw = puerta ? 0.06 : 0.055, pd = puerta ? 0.085 : 0.075, lf = puerta ? 0.055 : 0.04, ld = puerta ? 0.055 : 0.05;
  const def = VIDRIOS[state.vidrio] || VIDRIOS.incoloro;
  setGlassMaterial(def);
  const nH = state.hojas;

  if (state.premarco) {
    const pm = frame(W + 0.06, H + 0.06, 0.03, pd + 0.02, -0.02);
    g.add(pm);
  }
  g.add(frame(W, H, pw, pd, 0));
  if (puerta) {
    const u = new THREE.Mesh(new RoundedBoxGeometry(W + 0.03, 0.07, pd + 0.05, 2, 0.006), perfilMat);
    u.position.set(0, -H / 2 + 0.03, 0); u.castShadow = true; g.add(u);
  }

  const Wi = W - 2 * pw, Hi = H - 2 * pw;

  function buildLeaf(lw, lh, withHandle, handleSide, tir, secciones) {
    const leaf = new THREE.Group();
    leaf.add(frame(lw, lh, lf, ld, 0));
    // Zócalo inferior en puertas (panel ciego bajo el vidrio): es lo que hace
    // que la hoja se lea como puerta — el despiece real lo tiene (ZÓCALO DE PUERTA).
    const zocaloH = puerta ? Math.min(0.24, Math.max(0.14, lh * 0.12)) : 0;
    if (zocaloH > 0) {
      const zoc = new THREE.Mesh(new RoundedBoxGeometry(lw - 2 * lf + 0.012, zocaloH, ld * 0.96, 2, 0.004), perfilMat);
      zoc.position.set(0, -lh / 2 + lf + zocaloH / 2, 0);
      zoc.castShadow = true; zoc.receiveShadow = true;
      leaf.add(zoc);
    }
    const fillW = lw - 2 * lf, fillH = lh - 2 * lf - zocaloH, fillY = zocaloH / 2;
    if (secciones) {
      addSecciones(leaf, fillW, fillH, fillY, 0.002, secciones);
    } else {
      const gl = glass(fillW, fillH, 0, def);
      gl.position.y = fillY;
      leaf.add(gl);
    }
    if (withHandle) {
      const h = handle();
      if (puerta) h.scale.setScalar(1.5);   // herraje de puerta, más visible
      const hx = handleSide === 'izq' ? -lw / 2 + lf + 0.035 : lw / 2 - lf - 0.035;
      h.position.set(hx, puerta ? -0.03 : 0, ld / 2 + 0.02);
      if (handleSide === 'izq') h.rotation.y = Math.PI;
      leaf.add(h);
      if (puerta) {
        const cer = new THREE.Mesh(new THREE.CylinderGeometry(0.014, 0.014, 0.022, 16), handleMat);
        cer.rotation.x = Math.PI / 2; cer.position.set(hx, -0.14, ld / 2 + 0.02); leaf.add(cer);
      }
    }
    if (tir) {
      const t = new THREE.Mesh(new RoundedBoxGeometry(0.022, 0.16, 0.016, 2, 0.005), handleMat);
      t.position.set(-lw / 2 + lf + 0.02, 0, ld / 2 + 0.015); leaf.add(t);
    }
    return leaf;
  }

  // Secciones de tirantes: bandas horizontales o columnas verticales (vidrio o
  // panel ciego) + barra divisora, dibujadas DENTRO del target (hoja o paño) para
  // que acompañen la apertura. `secs` = [{medida_mm, ciego}]; la medida es el alto
  // de la banda si los tirantes son horizontales y el ancho de la columna si son
  // verticales, siempre en proporción sobre el hueco disponible.
  const tir3 = (Array.isArray(state.tirantes) && state.tirantes.length >= 2) ? state.tirantes : null;
  const medidaSec = s => parseInt(s.medida_mm != null ? s.medida_mm : s.alto_mm, 10) || 0;
  function addSecciones(target, w, h, yBase, z, secs) {
    const totalMm = secs.reduce((a, s) => a + medidaSec(s), 0);
    if (totalMm <= 0) { return; }
    const vertical = state.tirantesOrientacion === 'vertical';

    if (vertical) {
      let xLeft = -w / 2;
      secs.forEach((s, i) => {
        const segW = (medidaSec(s) / totalMm) * w;
        const xc = xLeft + segW / 2;
        const ancho = Math.max(segW - 0.006, 0.02);
        if (s.ciego) {
          const panel = new THREE.Mesh(new THREE.BoxGeometry(ancho, h, 0.02), perfilMat);
          panel.position.set(xc, yBase, z); panel.castShadow = true; panel.receiveShadow = true; target.add(panel);
        } else {
          const gseg = glass(ancho, h, z, def);
          gseg.position.x = xc; gseg.position.y = yBase; target.add(gseg);
        }
        if (i < secs.length - 1) {
          const bar = new THREE.Mesh(new RoundedBoxGeometry(0.028, h + 0.02, 0.03, 2, 0.004), perfilMat);
          bar.position.set(xLeft + segW, yBase, z); bar.castShadow = true; target.add(bar);
        }
        xLeft += segW;
      });
      return;
    }

    let yTop = yBase + h / 2;
    secs.forEach((s, i) => {
      const segH = (medidaSec(s) / totalMm) * h;
      const yc = yTop - segH / 2;
      if (s.ciego) {
        const panel = new THREE.Mesh(new THREE.BoxGeometry(w, Math.max(segH - 0.006, 0.02), 0.02), perfilMat);
        panel.position.set(0, yc, z); panel.castShadow = true; panel.receiveShadow = true; target.add(panel);
      } else {
        const gseg = glass(w, Math.max(segH - 0.006, 0.02), z, def);
        gseg.position.y = yc; target.add(gseg);
      }
      if (i < secs.length - 1) {
        const bar = new THREE.Mesh(new RoundedBoxGeometry(w + 0.02, 0.028, 0.03, 2, 0.004), perfilMat);
        bar.position.set(0, yTop - segH, z); bar.castShadow = true; target.add(bar);
      }
      yTop -= segH;
    });
  }

  if (modo === 'none') {
    g.add(frame(Wi, Hi, lf * 0.7, ld * 0.7, 0.004));
    if (tir3) { addSecciones(g, Wi - 2 * lf, Hi - 2 * lf, 0, 0.004, tir3); }
    else { g.add(glass(Wi - 2 * lf, Hi - 2 * lf, 0, def)); }
  } else if (modo === 'slide') {
    const colW = Wi / nH, overlap = lf;
    for (let i = 0; i < nH; i++) {
      // Por hoja: carril interior = mas cerca de la camara (+z), exterior = atras;
      // el movimiento define hacia donde corre. Sin apertura, el default historico
      // (pares adelante y a la derecha) coincide con el default del catalogo.
      const hoja = (ap && ap.hojas && ap.hojas[i]) || null;
      const carril = hoja ? hoja.carril : (i % 2 === 0 ? 'int' : 'ext');
      const mov = hoja ? hoja.movimiento : (i % 2 === 0 ? 'der' : null);
      const lw = colW + overlap, lh = Hi, cx = -Wi / 2 + colW * (i + 0.5), z = carril === 'int' ? 0.017 : -0.017;
      const leaf = buildLeaf(lw, lh, false, mov === 'izq' ? 'izq' : 'der', true);
      leaf.position.set(cx, 0, z); g.add(leaf);
      if (mov) {
        const dir = mov === 'der' ? 1 : -1;
        // No salirse del marco: hacia el borde, solo lo que queda de hueco.
        const libre = mov === 'der' ? (Wi / 2 - (cx + lw / 2)) : ((cx - lw / 2) + Wi / 2);
        const amt = Math.max(0, Math.min(colW * 0.85, libre + colW * 0.85)) * dir;
        const base = cx; movers.push({ apply: t => { leaf.position.x = base + amt * t; } });
      }
    }
  } else if (modo === 'swing') {
    if (nH === 1) {
      // Bisagra del lado elegido (REQ-047; default izquierda) → manija en el borde opuesto.
      const der = ladoBisagra === 'der';
      const leaf = buildLeaf(Wi, Hi, true, der ? 'izq' : 'der', false, tir3);
      const hinge = new THREE.Group();
      hinge.position.set(der ? Wi / 2 : -Wi / 2, 0, 0.01);
      leaf.position.set(der ? -Wi / 2 : Wi / 2, 0, 0);
      hinge.add(leaf); g.add(hinge);
      const sign = der ? 1 : -1;
      movers.push({ apply: t => { hinge.rotation.y = sign * (Math.PI * 0.44) * t; } });
    } else {
      const colW = Wi / 2;
      for (let i = 0; i < 2; i++) {
        const cx = -Wi / 2 + colW * (i + 0.5), handleSide = i === 0 ? 'der' : 'izq';
        const leaf = buildLeaf(colW, Hi, true, handleSide, false);
        const hx = i === 0 ? -Wi / 2 : Wi / 2;
        const hinge = new THREE.Group(); hinge.position.set(hx, 0, 0.01); leaf.position.set(cx - hx, 0, 0); hinge.add(leaf); g.add(hinge);
        const sign = i === 0 ? -1 : 1; movers.push({ apply: t => { hinge.rotation.y = sign * (Math.PI * 0.42) * t; } });
      }
    }
  } else if (modo === 'tilt') {
    const leaf = buildLeaf(Wi, Hi, true, 'izq', false, tir3);
    const hinge = new THREE.Group(); hinge.position.set(0, -Hi / 2, 0.01); leaf.position.set(0, Hi / 2, 0); hinge.add(leaf); g.add(hinge);
    movers.push({ apply: t => { hinge.rotation.x = -(Math.PI * 0.09) * t; } });
  } else if (modo === 'project') {
    const leaf = buildLeaf(Wi, Hi, true, 'izq', false, tir3);
    const hinge = new THREE.Group(); hinge.position.set(0, Hi / 2, 0.01); leaf.position.set(0, -Hi / 2, 0); hinge.add(leaf); g.add(hinge);
    movers.push({ apply: t => { hinge.rotation.x = (Math.PI * 0.11) * t; } });
  }

  if (state.mosquitero && modo !== 'none') {
    const mg = new THREE.Group();
    mg.add(frame(Wi, Hi, 0.028, 0.02, 0));
    const mesh = new THREE.Mesh(new THREE.PlaneGeometry(Wi - 0.05, Hi - 0.05), mallaMat);
    mallaTex.repeat.set((Wi - 0.05) * 45, (Hi - 0.05) * 45);
    mg.add(mesh); mg.position.z = pd / 2 + 0.012; g.add(mg);
  }

  scene.add(g); windowGroup = g;
  scene.getObjectByName('__ground').position.y = -H / 2 - 0.02;
  targetOpen = T.open || 0;
  if (!framed) { reframe(W, H); framed = true; }
}

function reframe(W, H) {
  const d = Math.max(W, H, 1) * 1.65 + 0.9;
  camera.position.set(d * 0.5, d * 0.28, d * 0.92);
  controls.target.set(0, 0, 0); controls.update();
}

function resize() {
  if (!host) return;
  const w = host.clientWidth || 1, h = host.clientHeight || 1;
  // Anti-loop: si el tamaño casi no cambió, no tocar el canvas (evita el
  // feedback ResizeObserver → setSize → ResizeObserver que agranda el modal).
  const cur = renderer.getSize(new THREE.Vector2());
  if (Math.abs(cur.x - w) < 2 && Math.abs(cur.y - h) < 2) return;
  renderer.setSize(w, h, false);
  camera.aspect = w / h; camera.updateProjectionMatrix();
}

function loop() {
  if (!running) return;
  requestAnimationFrame(loop);
  if (!host || host.clientWidth === 0) return;   // auto-pausa si el modal está oculto
  curOpen += (targetOpen - curOpen) * 0.1;
  movers.forEach(m => m.apply(curOpen));
  controls.update();
  renderer.render(scene, camera);
  if (overlayCotas && state.cotas) {
    overlayCotas.update(layoutCotas, camera, host.clientWidth, host.clientHeight);
  }
}

function applyParams(params) {
  params = params || {};
  state.tipo = TIPOS[params.tipo] ? params.tipo : 'pano_fijo';
  const T = TIPOS[state.tipo];
  state.ancho = clamp(parseInt(params.ancho, 10) || 1200, 300, 4000);
  state.alto = clamp(parseInt(params.alto, 10) || 1500, 300, 3000);
  let hojas = parseInt(params.hojas, 10) || T.hojas[0];
  state.hojas = T.hojas.includes(hojas) ? hojas : T.hojas[0];
  state.mosquitero = !!params.mosquitero;
  state.premarco = !!params.premarco;
  state.vidrio = VIDRIOS[params.vidrio] ? params.vidrio : 'incoloro';
  state.color = PERFILES[params.color] ? params.color : 'blanco';
  state.tirantes = Array.isArray(params.tirantes) ? params.tirantes : null;
  state.tirantesOrientacion = params.tirantes_orientacion === 'vertical' ? 'vertical' : 'horizontal';
  state.cotas = params.cotas !== false;
  state.vidrioComposicion = params.vidrio_composicion || null;
  state.sentidos = Array.isArray(params.sentidos) ? params.sentidos : null;
  // REQ-047: como abre. Normalizada contra las hojas del producto; null si no vino.
  state.apertura = normalizarApertura(params.apertura, state.hojas);
  // El layout de cotas se recalcula acá (no en cada frame): solo depende de los
  // params, no de la cámara.
  layoutCotas = computarLayout({
    tipo: state.tipo, ancho: state.ancho, alto: state.alto, hojas: state.hojas,
    mosquitero: state.mosquitero, premarco: state.premarco,
    tirantes: state.tirantes, tirantes_orientacion: state.tirantesOrientacion,
    vidrio_composicion: state.vidrioComposicion, sentidos: state.sentidos,
  });
  if (overlayCotas) overlayCotas.setVisible(state.cotas);
  const p = PERFILES[state.color];
  perfilMat.color.setHex(p.color); perfilMat.metalness = p.metalness; perfilMat.roughness = p.roughness;
  curOpen = 0;
  build();
}

const AkunViewer = {
  mount(container, params) {
    if (!container) return;
    if (!renderer) initEngine();
    if (host !== container) {
      host = container;
      // El canvas va ABSOLUTO dentro del contenedor: queda fuera del flujo y
      // no puede agrandar al padre (evita el scroll infinito del modal).
      container.style.position = 'relative';
      container.style.overflow = 'hidden';
      if (container.clientHeight < 40) container.style.height = '288px';  // fallback si la clase de altura no aplicó
      container.appendChild(renderer.domElement);
      renderer.domElement.style.position = 'absolute';
      renderer.domElement.style.inset = '0';
      renderer.domElement.style.width = '100%';
      renderer.domElement.style.height = '100%';
      renderer.domElement.style.display = 'block';
      if (!overlayCotas) overlayCotas = crearOverlayCotas(THREE);
      container.appendChild(overlayCotas.dom);
      if (ro) ro.disconnect();
      ro = new ResizeObserver(() => resize());
      ro.observe(container);
    }
    resize();
    applyParams(params);
    if (!running) { running = true; loop(); }
  },
  setParams(params) { if (renderer) applyParams(params); },
  setCotas(v) { state.cotas = !!v; if (overlayCotas) overlayCotas.setVisible(!!v); },
  dispose() {
    running = false;
    if (ro) { ro.disconnect(); ro = null; }
    if (renderer && renderer.domElement && renderer.domElement.parentNode) {
      renderer.domElement.parentNode.removeChild(renderer.domElement);
    }
    if (overlayCotas && overlayCotas.dom.parentNode) {
      overlayCotas.dom.parentNode.removeChild(overlayCotas.dom);
    }
    host = null; framed = false;
  },
};

window.AkunViewer = AkunViewer;
export default AkunViewer;
