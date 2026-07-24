"""Análisis (solo lectura) para validar la clasificación de tipología del visor 3D.

Compara, para TODO el catálogo de productos, la tipología que da el clasificador
por NOMBRE contra la que se podría inferir del DESPIECE (perfiles de hoja +
accesorios). Sirve para decidir si conviene clasificar por despiece antes de
implementarlo, y para ver qué productos quedan sin señal o en conflicto.

No modifica nada. Correr:
    python manage.py analizar_tipologias
"""

import unicodedata
from collections import Counter

from django.core.management.base import BaseCommand

from pricing.models import (
    Producto, Marco, Hoja, Perfil, Accesorio,
    DespiecePerfilesHoja, DespieceAccesoriosHoja, DespieceAccesoriosMarco,
)
from pricing.tipologia import clasificar_tipologia


def _norm(s):
    s = unicodedata.normalize('NFKD', str(s or ''))
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return s.lower()


def tipo_por_despiece(blob):
    """Tipología inferida de las señales del despiece (hoja + accesorios)."""
    b = _norm(blob)
    corrediza = any(k in b for k in ('corrediz', 'riel', 'rodamiento', 'ruedas', 'desliz'))
    puerta = ('hoja de puerta' in b) or ('zocalo de puerta' in b) or ('puerta' in b)
    oscilo = 'oscilo' in b
    proyect = any(k in b for k in ('proyect', 'banderola', 'brazo'))
    bisagra = 'bisagra' in b
    cerradura = ('cerradura' in b) or ('picaporte' in b)
    if puerta or (cerradura and bisagra):
        return 'puerta_corrediza' if corrediza else 'puerta_batiente'
    if corrediza:
        return 'ventana_corrediza'
    if oscilo:
        return 'ventana_oscilo'
    if proyect:
        return 'ventana_proyectante'
    if bisagra:
        return 'ventana_batiente'
    return ''  # sin señal clara


class Command(BaseCommand):
    help = 'Compara tipología por nombre vs por despiece en todo el catálogo (solo lectura).'

    def handle(self, *args, **options):
        perfiles = {p.codigo: (p.descripcion or '') for p in Perfil.objects.all()}
        accesorios = {}
        for ac in Accesorio.objects.all():
            accesorios.setdefault(ac.codigo, ac.descripcion or '')

        def desc_perfil(code):
            return perfiles.get((code or '').strip(), code or '')

        def desc_acc(code):
            return accesorios.get((code or '').strip(), code or '')

        productos = list(Producto.objects.exclude(bloqueado='Si'))
        by_name = Counter()
        by_despiece = Counter()
        sin_senal = []
        discrepancias = []

        for p in productos:
            textos = []
            for m in Marco.objects.filter(producto=p).exclude(bloqueado='Si'):
                for h in Hoja.objects.filter(marco=m).exclude(bloqueado='Si'):
                    for dp in DespiecePerfilesHoja.objects.filter(hoja=h):
                        textos.append(desc_perfil(dp.perfil))
                    for da in DespieceAccesoriosHoja.objects.filter(hoja=h):
                        textos.append(desc_acc(da.accesorio))
                for da in DespieceAccesoriosMarco.objects.filter(marco=m):
                    textos.append(desc_acc(da.accesorio))
            blob = ' | '.join(t for t in textos if t)

            t_nombre = clasificar_tipologia(p.descripcion, p.cantidad_hojas)
            t_desp = tipo_por_despiece(blob)
            by_name[t_nombre] += 1
            by_despiece[t_desp or '(sin senal)'] += 1
            if not t_desp:
                sin_senal.append((p.id, (p.descripcion or '')[:55]))
            elif t_desp != t_nombre:
                discrepancias.append((p.id, (p.descripcion or '')[:45], p.cantidad_hojas or 1, t_nombre, t_desp))

        w = self.stdout.write
        w('=' * 72)
        w(f'TOTAL productos activos: {len(productos)}')
        w('\n-- Tipo por NOMBRE (clasificador actual) --')
        for k, v in by_name.most_common():
            w(f'  {v:4d}  {k}')
        w('\n-- Tipo por DESPIECE (propuesto) --')
        for k, v in by_despiece.most_common():
            w(f'  {v:4d}  {k}')
        w(f'\nProductos SIN senal de despiece: {len(sin_senal)}')
        for pid, desc in sin_senal[:50]:
            w(f'  [{pid}] {desc}')
        w(f'\nDISCREPANCIAS (nombre != despiece): {len(discrepancias)}')
        for pid, desc, h, tn, td in discrepancias[:100]:
            w(f'  [{pid}] h{h} "{desc}"  nombre={tn}  despiece={td}')
        w('=' * 72)
