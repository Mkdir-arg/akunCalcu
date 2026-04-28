from django.core.management.base import BaseCommand
from comercial.models import PagoVenta, Recibo

class Command(BaseCommand):
    help = "Regenera todos los PDFs de recibos con el nuevo formato"

    def handle(self, *args, **options):
        total = 0
        for pago in PagoVenta.objects.select_related('venta', 'venta__cliente').prefetch_related('retenciones').order_by('fecha_pago', 'pk'):
            recibo = Recibo.obtener_o_crear_desde_pago(pago, force=True)
            self.stdout.write(self.style.SUCCESS(f"Recibo {recibo.numero} regenerado para pago {pago.pk}"))
            total += 1
        self.stdout.write(self.style.SUCCESS(f"Total de recibos regenerados: {total}"))
