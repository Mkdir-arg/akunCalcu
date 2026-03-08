from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Agrega campos tipo_calculo y formula_calculo a accesorios'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # tipo_calculo en accesorios
            try:
                cursor.execute("ALTER TABLE accesorios ADD COLUMN tipo_calculo TEXT DEFAULT 'unidad'")
                self.stdout.write(self.style.SUCCESS('✓ Campo tipo_calculo agregado a accesorios'))
            except Exception as e:
                if '1060' in str(e):
                    self.stdout.write(self.style.WARNING('tipo_calculo ya existe'))
                else:
                    self.stdout.write(self.style.ERROR(f'Error tipo_calculo: {e}'))
            
            # formula_calculo en accesorios
            try:
                cursor.execute("ALTER TABLE accesorios ADD COLUMN formula_calculo TEXT")
                self.stdout.write(self.style.SUCCESS('✓ Campo formula_calculo agregado a accesorios'))
            except Exception as e:
                if '1060' in str(e):
                    self.stdout.write(self.style.WARNING('formula_calculo ya existe'))
                else:
                    self.stdout.write(self.style.ERROR(f'Error formula_calculo: {e}'))
            
            self.stdout.write(self.style.SUCCESS('\n✓ Actualización completada'))
