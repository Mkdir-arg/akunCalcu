from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Altera los campos de vidrios de INT a TEXT'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            try:
                cursor.execute("ALTER TABLE vidrios MODIFY COLUMN Idproducto TEXT")
                self.stdout.write(self.style.SUCCESS('Campo Idproducto alterado a TEXT'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Idproducto: {e}'))
            
            try:
                cursor.execute("ALTER TABLE vidrios MODIFY COLUMN rebaje_ancho TEXT")
                self.stdout.write(self.style.SUCCESS('Campo rebaje_ancho alterado a TEXT'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'rebaje_ancho: {e}'))
            
            try:
                cursor.execute("ALTER TABLE vidrios MODIFY COLUMN rebaje_alto TEXT")
                self.stdout.write(self.style.SUCCESS('Campo rebaje_alto alterado a TEXT'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'rebaje_alto: {e}'))
