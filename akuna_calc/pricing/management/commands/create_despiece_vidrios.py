"""Create despiece_perfiles_vidrios table."""

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Create despiece_perfiles_vidrios table"

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            try:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS despiece_perfiles_vidrios (
                        Id INT PRIMARY KEY AUTO_INCREMENT,
                        Idvidrio VARCHAR(255),
                        Formuladecantidad TEXT,
                        Perfil TEXT,
                        Formuladeperfil TEXT,
                        Angulo TEXT,
                        Mo_especifica INT
                    )
                """)
                self.stdout.write(self.style.SUCCESS("✓ Table despiece_perfiles_vidrios created"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Error: {e}"))
