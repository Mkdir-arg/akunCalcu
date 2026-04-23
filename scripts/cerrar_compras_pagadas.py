from comercial.models import Compra
from django.db import transaction

# Script para cerrar compras pagadas
with transaction.atomic():
    compras = Compra.objects.filter(estado='pendiente', deleted_at__isnull=True)
    cerradas = 0
    for compra in compras:
        total_pagos = sum(pago.monto for pago in compra.pagos_compra.all())
        saldo = compra.valor_total - compra.sena - total_pagos
        if saldo <= 0:
            compra.estado = 'pagado'
            compra.saldo = 0
            compra.save()
            cerradas += 1
    print(f"Compras cerradas automáticamente: {cerradas}")
