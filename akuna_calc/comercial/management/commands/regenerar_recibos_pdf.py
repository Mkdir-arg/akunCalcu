from django.core.management.base import BaseCommand
from comercial.models import Recibo

class Command(BaseCommand):
    help = "Regenera todos los PDFs de recibos con el nuevo formato"

    def handle(self, *args, **options):
        total = 0
        for recibo in Recibo.objects.all():
            # Cambia este método por el real de tu modelo:
            if hasattr(recibo, 'generar_pdf'):
                recibo.generar_pdf(force=True)
                self.stdout.write(self.style.SUCCESS(f"Recibo {recibo.pk} regenerado"))
                total += 1
            else:
                self.stdout.write(self.style.WARNING(f"Recibo {recibo.pk} no tiene método generar_pdf"))
        self.stdout.write(self.style.SUCCESS(f"Total de recibos regenerados: {total}"))
