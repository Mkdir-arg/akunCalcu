from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Agrega campo cantidad_hojas a productos'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # cantidad_hojas en productos
            try:
                cursor.execute("ALTER TABLE productos ADD COLUMN cantidad_hojas INT DEFAULT 1")
                self.stdout.write(self.style.SUCCESS('✓ Campo cantidad_hojas agregado a productos'))
            except Exception as e:
                if '1060' in str(e):
                    self.stdout.write(self.style.WARNING('cantidad_hojas ya existe'))
                else:
                    self.stdout.write(self.style.ERROR(f'Error cantidad_hojas: {e}'))
            
            self.stdout.write(self.style.SUCCESS('\n✓ Actualización completada'))
