from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Agrega campo cant y modifica Tipo a TEXT en accesorios'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            try:
                cursor.execute("ALTER TABLE accesorios ADD COLUMN cant INT DEFAULT 1")
                self.stdout.write(self.style.SUCCESS('✓ Campo cant agregado'))
            except Exception as e:
                if '1060' in str(e):
                    self.stdout.write(self.style.WARNING('cant ya existe'))
                else:
                    self.stdout.write(self.style.ERROR(f'Error cant: {e}'))
            
            try:
                cursor.execute("ALTER TABLE accesorios MODIFY COLUMN Tipo TEXT")
                self.stdout.write(self.style.SUCCESS('✓ Campo Tipo modificado a TEXT'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error Tipo: {e}'))
            
            try:
                cursor.execute("ALTER TABLE accesorios ADD COLUMN cant_20 INT DEFAULT 20")
                self.stdout.write(self.style.SUCCESS('✓ Campo cant_20 agregado'))
            except Exception as e:
                if '1060' in str(e):
                    self.stdout.write(self.style.WARNING('cant_20 ya existe'))
                else:
                    self.stdout.write(self.style.ERROR(f'Error cant_20: {e}'))
