"""Add producto and rebaje fields to vidrios table."""

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Add producto_id, rebaje_ancho and rebaje_alto fields to vidrios table"

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            fields = [
                ("Idproducto", "INT"),
                ("rebaje_ancho", "INT DEFAULT 0"),
                ("rebaje_alto", "INT DEFAULT 0"),
            ]
            
            for field_name, field_type in fields:
                try:
                    cursor.execute(f"ALTER TABLE vidrios ADD COLUMN {field_name} {field_type}")
                    self.stdout.write(self.style.SUCCESS(f"✓ Added column: {field_name}"))
                except Exception as e:
                    if "Duplicate column name" in str(e) or "duplicate column" in str(e).lower():
                        self.stdout.write(self.style.WARNING(f"⊘ Column already exists: {field_name}"))
                    else:
                        self.stdout.write(self.style.ERROR(f"✗ Error adding {field_name}: {e}"))
        
        self.stdout.write(self.style.SUCCESS("\n✓ Vidrio fields migration completed"))
