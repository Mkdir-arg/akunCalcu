from django.core.management.base import BaseCommand
from comercial.models import TipoCuenta


class Command(BaseCommand):
    help = 'Carga datos iniciales para el módulo comercial'

    def handle(self, *args, **options):
        # Crear tipos de cuenta
        tipos_cuenta = [
            ('colocadores', 'Colocadores'),
            ('colaboradores', 'Colaboradores'),
            ('fletes', 'Fletes'),
            ('retiros_propios', 'Retiros Propios'),
            ('varios', 'Varios'),
            ('proveedores', 'Proveedores'),
        ]

        for tipo, descripcion in tipos_cuenta:
            tipo_cuenta, created = TipoCuenta.objects.get_or_create(
                tipo=tipo,
                defaults={'descripcion': descripcion}
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Tipo de cuenta "{descripcion}" creado exitosamente')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Tipo de cuenta "{descripcion}" ya existe')
                )

        self.stdout.write(
            self.style.SUCCESS('Datos iniciales del módulo comercial cargados exitosamente')
        )