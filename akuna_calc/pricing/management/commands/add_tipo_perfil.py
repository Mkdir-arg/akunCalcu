"""
Management command to add tipo_perfil column to perfiles table.
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Agrega columna tipo_perfil a la tabla perfiles'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            try:
                cursor.execute("ALTER TABLE perfiles ADD COLUMN tipo_perfil TEXT NULL;")
                self.stdout.write(self.style.SUCCESS('✓ Columna tipo_perfil agregada exitosamente'))
            except Exception as e:
                if 'Duplicate column name' in str(e):
                    self.stdout.write(self.style.WARNING('⚠ La columna tipo_perfil ya existe'))
                else:
                    self.stdout.write(self.style.ERROR(f'✗ Error: {str(e)}'))
