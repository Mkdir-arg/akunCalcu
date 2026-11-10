"""Contexto de las planillas internas A4 que salen del presupuesto (REQ-056/057)."""
from decimal import Decimal

from core.pdf import contexto_base_pdf, filas_cliente
from .pdf_descriptions import build_ficha_item


def venta_activa(presupuesto):
    """La venta del presupuesto confirmado, o None. Se mira la venta y no solo el estado porque
    `cambiar_estado` permite des-confirmar y la venta queda."""
    venta = presupuesto.venta
    if presupuesto.estado != 'confirmado' or venta is None or venta.deleted_at is not None:
        return None
    return venta


def _forma_pago(venta, presupuesto):
    medios = []
    if venta.sena > 0 and venta.forma_pago:
        medios.append(venta.get_forma_pago_display())
    for pago in venta.pagos.all():
        medio = pago.get_forma_pago_display()
        if medio not in medios:
            medios.append(medio)
    partes = [', '.join(medios)] if medios else []
    partes.append(f'Seña {presupuesto.get_modalidad_sena_display()}')
    return ' · '.join(partes)


def build_medicion_context(presupuesto, user, fecha):
    return {
        **contexto_base_pdf(),
        'presupuesto': presupuesto,
        'meta_filas': [
            ('PRESUPUESTO', presupuesto.numero),
            ('FECHA', fecha.strftime('%d/%m/%Y')),
        ],
        'responsable': user.get_full_name() or user.get_username(),
        'filas_cliente': filas_cliente(presupuesto.cliente, incluir=('cliente', 'domicilio', 'localidad', 'telefono')),
        'renglones': range(10),
    }


def build_colocacion_context(presupuesto, venta, colocador=None, fecha=None, observaciones=''):
    pagado = venta.sena + sum((pago.monto for pago in venta.pagos.all()), Decimal('0'))
    total = venta.get_total_con_percepciones()
    es_pvc = presupuesto.es_pvc() and presupuesto.tiene_cotizacion_usd()

    importes = [
        ('VALOR TOTAL', total, presupuesto._convertir_a_usd(total) if es_pvc else None),
        ('SEÑA / A CUENTA', pagado, presupuesto._convertir_a_usd(pagado) if es_pvc else None),
        ('SALDO PENDIENTE', venta.saldo, presupuesto._convertir_a_usd(venta.saldo) if es_pvc else None),
    ]

    return {
        **contexto_base_pdf(),
        'presupuesto': presupuesto,
        'meta_filas': [
            ('PRESUPUESTO', presupuesto.numero),
            ('FECHA', fecha.strftime('%d/%m/%Y') if fecha else ''),
        ],
        'colocador': colocador,
        'filas_cliente': filas_cliente(presupuesto.cliente),
        'fichas': [build_ficha_item(item) for item in presupuesto.items.all()],
        'importes': importes,
        'es_pvc': es_pvc,
        'cotizacion_usd': presupuesto.cotizacion_usd if es_pvc else None,
        'forma_pago': _forma_pago(venta, presupuesto),
        'observaciones': observaciones,
        'renglones_extra': range(0 if observaciones else 4),
    }
