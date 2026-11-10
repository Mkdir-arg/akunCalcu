"""Acomodo de tramos en barras: First Fit Decreasing (REQ-070)."""


def acomodar(tramos, largo_barra, disco, despunte):
    """tramos: lista de dicts con 'largo_mm' (un dict por pieza a cortar).

    Devuelve (barras, no_entran). Cada barra: {'piezas': [...], 'usado': mm, 'sobrante': mm}. Cada corte
    consume largo + disco y cada barra arranca con el despunte ya usado, pero el último corte de una barra no
    gasta disco (un tramo entra si usado + largo <= largo_barra). El sobrante nunca es negativo. Un tramo que no entra ni en una
    barra vacía (largo + despunte > largo_barra) va aparte.
    """
    barras = []
    no_entran = []
    for tramo in sorted(tramos, key=lambda t: t['largo_mm'], reverse=True):
        largo = tramo['largo_mm']
        if largo + despunte > largo_barra:
            no_entran.append(tramo)
            continue
        destino = next((b for b in barras if b['usado'] + largo <= largo_barra), None)
        if destino is None:
            destino = {'piezas': [], 'usado': despunte}
            barras.append(destino)
        destino['piezas'].append(tramo)
        destino['usado'] += largo + disco
    for barra in barras:
        barra['sobrante'] = max(largo_barra - barra['usado'], 0)
    return barras, no_entran
