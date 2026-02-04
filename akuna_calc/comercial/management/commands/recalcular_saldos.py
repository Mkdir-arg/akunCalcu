from django.core.management.base import BaseCommand
from comercial.models import Venta


class Command(BaseCommand):
    help = 'Recalcula los saldos de todas las ventas'

    def handle(self, *args, **options):
        ventas = Venta.objects.filter(deleted_at__isnull=True)
        for venta in ventas:
            venta.save()  # Esto recalculará el saldo
            self.stdout.write(f'Venta {venta.numero_pedido}: Saldo = ${venta.saldo}')
        
        self.stdout.write(self.style.SUCCESS(f'Se recalcularon {ventas.count()} ventas'))
