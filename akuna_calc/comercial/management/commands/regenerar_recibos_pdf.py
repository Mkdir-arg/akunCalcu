from django.core.management.base import BaseCommand
from comercial.models import PagoVenta, Recibo


class Command(BaseCommand):
    help = "Genera (o regenera) los PDFs de todos los recibos a partir de los pagos existentes."

    def handle(self, *args, **options):
        total = 0
        errores = 0
        pagos = PagoVenta.objects.select_related('venta', 'venta__cliente').prefetch_related('retenciones').order_by('fecha_pago', 'pk')

        for pago in pagos:
            try:
                recibo = Recibo.obtener_o_crear_desde_pago(pago, force=True)
                self.stdout.write(self.style.SUCCESS(f"Recibo {recibo.numero} generado para pago {pago.pk}"))
                total += 1
            except Exception as exc:
                errores += 1
                self.stdout.write(self.style.ERROR(f"Error al generar recibo para pago {pago.pk}: {exc}"))

        self.stdout.write(self.style.SUCCESS(f"Total de recibos generados: {total}"))
        if errores:
            self.stdout.write(self.style.WARNING(f"Errores: {errores}"))
