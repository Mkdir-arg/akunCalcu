"""
Management command to create despiece_perfiles_hojas table if it doesn't exist.
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Crea la tabla despiece_perfiles_hojas si no existe'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            try:
                # Verificar si la tabla existe
                cursor.execute("SHOW TABLES LIKE 'despiece_perfiles_hojas';")
                if cursor.fetchone():
                    self.stdout.write(self.style.WARNING('⚠ La tabla despiece_perfiles_hojas ya existe'))
                else:
                    # Crear la tabla
                    cursor.execute("""
                        CREATE TABLE despiece_perfiles_hojas (
                            Id INT PRIMARY KEY,
                            Idhoja INT,
                            Formuladecantidad TEXT,
                            Perfil TEXT,
                            Formuladeperfil TEXT,
                            Angulo TEXT,
                            Mo_especifica INT
                        );
                    """)
                    self.stdout.write(self.style.SUCCESS('✓ Tabla despiece_perfiles_hojas creada exitosamente'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Error: {str(e)}'))
