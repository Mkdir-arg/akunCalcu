from django.core.management.base import BaseCommand
from comercial.models import Venta
from django.test import RequestFactory
from comercial.views import generar_pdf_venta
import os
from django.conf import settings

class Command(BaseCommand):
    help = "Regenera todos los PDFs de ventas con el nuevo diseño y los guarda en la carpeta configurada."

    def handle(self, *args, **options):
        factory = RequestFactory()
        total = 0
        output_dir = os.path.join(settings.MEDIA_ROOT, "ventas_pdf")
        os.makedirs(output_dir, exist_ok=True)

        # Usar un usuario anónimo para evitar error de request.user
        from django.contrib.auth.models import AnonymousUser

        for venta in Venta.objects.all():
            request = factory.get("/")
            request.user = AnonymousUser()
            response = generar_pdf_venta(request, venta.pk)
            pdf_path = os.path.join(output_dir, f"venta_{venta.numero_pedido}.pdf")
            with open(pdf_path, "wb") as f:
                f.write(response.getvalue())
            self.stdout.write(self.style.SUCCESS(f"PDF generado para venta {venta.pk}: {pdf_path}"))
            total += 1
        self.stdout.write(self.style.SUCCESS(f"Total de PDFs generados: {total}"))
