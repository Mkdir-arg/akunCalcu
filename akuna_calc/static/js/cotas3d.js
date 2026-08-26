/**
 * Overlay de cotas sobre el visor 3D — opción A del análisis.
 *
 * Dibuja las cotas en un <svg> absoluto encima del canvas, proyectando los
 * puntos de anclaje 3D a coordenadas de pantalla. El texto es DOM real: nítido
 * a cualquier zoom, sin texturas y estilable con CSS.
 *
 * Por qué se ocultan solas: en perspectiva dos paños iguales se proyectan con
 * largos distintos, así que una cota vista de costado miente. El overlay se
 * desvanece cuando la cámara se aparta del frente más de cierto ángulo, y en esa
 * pose la lectura fiable es la elevación 2D (`elevacion.js`).
 */

const NS = 'http://www.w3.org/2000/svg';
const COLOR = '#1d4ed8';

/** Coseno mínimo entre la normal de la abertura y la dirección de cámara. */
const COS_MIN = 0.55;   // ~57° de apertura antes de empezar a desvanecer
const COS_LLENO = 0.90; // de acá en adelante, opacidad total

function el(tag, attrs) {
  const n = document.createElementNS(NS, tag);
  for (const k in attrs) n.setAttribute(k, attrs[k]);
  return n;
}

export function crearOverlayCotas(THREE) {
  const svg = el('svg', { width: '100%', height: '100%' });
  Object.assign(svg.style, {
    position: 'absolute', inset: '0', pointerEvents: 'none', overflow: 'visible',
  });

  const vTmp = new THREE.Vector3();
  const dirCam = new THREE.Vector3();
  let visible = true;

  /** mm con origen arriba-izquierda → metros centrados con y hacia arriba. */
  function aMundo(xMm, yMm, wMm, hMm) {
    return [(xMm - wMm / 2) / 1000, (hMm / 2 - yMm) / 1000];
  }

  /** Punto 3D → píxeles del contenedor. */
  function aPantalla(x, y, z, camera, w, h) {
    vTmp.set(x, y, z).project(camera);
    return [(vTmp.x * 0.5 + 0.5) * w, (-vTmp.y * 0.5 + 0.5) * h];
  }

  /** Cota entre dos puntos de pantalla, desplazada hacia `normal`. */
  function cota(p1, p2, normal, offset, texto, escala) {
    const g = el('g', {});
    const nx = normal[0] * offset, ny = normal[1] * offset;
    const a = [p1[0] + nx, p1[1] + ny];
    const b = [p2[0] + nx, p2[1] + ny];
    const sw = Math.max(1, escala * 0.9);
    const t = Math.max(4, escala * 4);

    // Líneas de referencia desde la pieza hasta la cota
    g.appendChild(el('line', { x1: p1[0], y1: p1[1], x2: a[0], y2: a[1],
      stroke: COLOR, 'stroke-width': sw * 0.6, 'stroke-dasharray': '3 3', opacity: 0.5 }));
    g.appendChild(el('line', { x1: p2[0], y1: p2[1], x2: b[0], y2: b[1],
      stroke: COLOR, 'stroke-width': sw * 0.6, 'stroke-dasharray': '3 3', opacity: 0.5 }));
    g.appendChild(el('line', { x1: a[0], y1: a[1], x2: b[0], y2: b[1], stroke: COLOR, 'stroke-width': sw }));

    // Topes perpendiculares a la cota
    const dx = b[0] - a[0], dy = b[1] - a[1];
    const len = Math.hypot(dx, dy) || 1;
    const px = -dy / len * t * 0.5, py = dx / len * t * 0.5;
    [a, b].forEach(p => g.appendChild(el('line', {
      x1: p[0] - px, y1: p[1] - py, x2: p[0] + px, y2: p[1] + py, stroke: COLOR, 'stroke-width': sw })));

    // Texto centrado y alineado con la cota, siempre legible de izq a der
    const mx = (a[0] + b[0]) / 2, my = (a[1] + b[1]) / 2;
    let ang = Math.atan2(dy, dx) * 180 / Math.PI;
    if (ang > 90 || ang < -90) ang += 180;
    const fs = Math.max(9, escala * 11);
    const txt = el('text', {
      x: mx, y: my - fs * 0.35, fill: COLOR, 'font-size': fs, 'font-weight': '600',
      'text-anchor': 'middle', transform: `rotate(${ang} ${mx} ${my})`,
      style: 'font-family:Arial,Helvetica,sans-serif;paint-order:stroke',
      stroke: '#ffffff', 'stroke-width': Math.max(2, fs * 0.28), 'stroke-linejoin': 'round',
    });
    txt.textContent = texto;
    g.appendChild(txt);
    return g;
  }

  return {
    dom: svg,

    setVisible(v) { visible = !!v; if (!v) svg.replaceChildren(); },

    /**
     * @param layout  salida de `computarLayout` (mm)
     * @param camera  cámara del visor
     * @param w,h     tamaño del contenedor en píxeles
     */
    update(layout, camera, w, h) {
      if (!visible || !layout || !w || !h) { svg.replaceChildren(); return; }

      // ¿Qué tan de frente estamos? La abertura mira hacia +Z.
      camera.getWorldDirection(dirCam);
      const cos = Math.abs(dirCam.z);
      if (cos < COS_MIN) { svg.replaceChildren(); return; }
      const opacidad = Math.min(1, (cos - COS_MIN) / (COS_LLENO - COS_MIN));

      const W = layout.ancho_mm, H = layout.alto_mm;
      const esquina = (xMm, yMm) => {
        const [x, y] = aMundo(xMm, yMm, W, H);
        return aPantalla(x, y, 0, camera, w, h);
      };

      const supIzq = esquina(0, 0);
      const infIzq = esquina(0, H);
      const infDer = esquina(W, H);

      // Escala en píxeles por metro: mantiene el trazo proporcional al zoom
      const anchoPx = Math.hypot(infDer[0] - infIzq[0], infDer[1] - infIzq[1]);
      const escala = Math.max(0.5, Math.min(2.2, anchoPx / 420));
      const off = Math.max(26, anchoPx * 0.09);

      const frag = document.createDocumentFragment();

      // Alto, a la izquierda
      frag.appendChild(cota(supIzq, infIzq, [-1, 0], off, String(layout.cotas.alto), escala));

      // Anchos por paño y total, abajo
      const anchos = layout.cotas.anchos;
      if (anchos.length) {
        anchos.forEach(c => frag.appendChild(
          cota(esquina(c.desde, H), esquina(c.hasta, H), [0, 1], off, String(c.valor), escala)));
      }
      frag.appendChild(cota(infIzq, infDer, [0, 1],
        off + (anchos.length ? off * 0.85 : 0), String(layout.cotas.ancho_total), escala));

      svg.replaceChildren(frag);
      svg.style.opacity = String(opacidad);
    },
  };
}

export default { crearOverlayCotas };
