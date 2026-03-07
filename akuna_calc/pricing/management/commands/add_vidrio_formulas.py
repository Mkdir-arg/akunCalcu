"""Add formula fields to vidrios table."""

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Add formula fields to vidrios table"

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Agregar columna Idhoja
            try:
                cursor.execute("ALTER TABLE vidrios ADD COLUMN Idhoja INT")
                self.stdout.write(self.style.SUCCESS("✓ Added column: Idhoja"))
            except Exception as e:
                if "Duplicate column name" in str(e) or "duplicate column" in str(e).lower():
                    self.stdout.write(self.style.WARNING("⊘ Column already exists: Idhoja"))
                else:
                    self.stdout.write(self.style.ERROR(f"✗ Error adding Idhoja: {e}"))
            
            # Agregar columnas de fórmulas
            fields = [
                "formula_umbral_dintel",
                "formula_zocalo",
                "formula_parante",
                "formula_ancho_dvh",
                "formula_alto_dvh",
                "formula_ancho_mosq",
                "formula_alto_mosq",
                "formula_tope_mosq",
            ]
            
            for field in fields:
                try:
                    cursor.execute(f"ALTER TABLE vidrios ADD COLUMN {field} TEXT")
                    self.stdout.write(self.style.SUCCESS(f"✓ Added column: {field}"))
                except Exception as e:
                    if "Duplicate column name" in str(e) or "duplicate column" in str(e).lower():
                        self.stdout.write(self.style.WARNING(f"⊘ Column already exists: {field}"))
                    else:
                        self.stdout.write(self.style.ERROR(f"✗ Error adding {field}: {e}"))
        
        self.stdout.write(self.style.SUCCESS("\n✓ Vidrio formula fields migration completed"))
