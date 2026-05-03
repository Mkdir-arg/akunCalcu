from django.core.management.base import BaseCommand
from comercial.models import Recibo


class Command(BaseCommand):
    help = "Borra todos los archivos PDF de recibos del disco y limpia el campo pdf en la base."

    def add_arguments(self, parser):
        parser.add_argument(
            '--eliminar-recibos',
            action='store_true',
            help="Elimina también los registros de Recibo de la base (no solo el PDF).",
        )

    def handle(self, *args, **options):
        eliminar_recibos = options['eliminar_recibos']
        total_pdf = 0
        total_recibos = 0

        for recibo in Recibo.objects.all():
            if recibo.pdf:
                recibo.pdf.delete(save=False)
                total_pdf += 1
            recibo.pdf = None
            recibo.save(update_fields=['pdf'])
            self.stdout.write(self.style.WARNING(f"PDF borrado para recibo {recibo.numero}"))

        if eliminar_recibos:
            total_recibos = Recibo.objects.count()
            Recibo.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Recibos eliminados de la base: {total_recibos}"))

        self.stdout.write(self.style.SUCCESS(f"Total de PDFs borrados: {total_pdf}"))
        if eliminar_recibos:
            self.stdout.write(self.style.SUCCESS(f"Total de recibos eliminados: {total_recibos}"))
