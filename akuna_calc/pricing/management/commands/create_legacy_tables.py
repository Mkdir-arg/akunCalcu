"""
Management command to check and create all legacy tables if they don't exist.
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Verifica y crea todas las tablas legacy que no existan'

    def handle(self, *args, **options):
        tables_to_check = {
            'despiece_perfiles_marcos': """
                CREATE TABLE despiece_perfiles_marcos (
                    Id INT PRIMARY KEY,
                    Idmarco INT,
                    Formuladecantidad TEXT,
                    Perfil TEXT,
                    Formuladeperfil TEXT,
                    Angulo TEXT,
                    Mo_especifica INT
                );
            """,
            'despiece_perfiles_hojas': """
                CREATE TABLE despiece_perfiles_hojas (
                    Id INT PRIMARY KEY,
                    Idhoja INT,
                    Formuladecantidad TEXT,
                    Perfil TEXT,
                    Formuladeperfil TEXT,
                    Angulo TEXT,
                    Mo_especifica INT
                );
            """,
            'despiece_accesorios_marco': """
                CREATE TABLE despiece_accesorios_marco (
                    Id INT PRIMARY KEY,
                    Idmarco INT,
                    Formuladecantidad TEXT,
                    Accesorio TEXT,
                    Mo_especifica INT
                );
            """,
            'despiece_accesorios_hoja': """
                CREATE TABLE despiece_accesorios_hoja (
                    Id INT PRIMARY KEY,
                    Idhoja INT,
                    Formuladecantidad TEXT,
                    Accesorio TEXT,
                    Idconjunto INT,
                    Nombre_conjunto TEXT,
                    Aparece_presupuesto TEXT,
                    Mo_especifica INT
                );
            """,
        }

        with connection.cursor() as cursor:
            created = []
            existing = []
            errors = []

            for table_name, create_sql in tables_to_check.items():
                try:
                    # Verificar si la tabla existe
                    cursor.execute(f"SHOW TABLES LIKE '{table_name}';")
                    if cursor.fetchone():
                        existing.append(table_name)
                        self.stdout.write(f"  ✓ {table_name} (ya existe)")
                    else:
                        # Crear la tabla
                        cursor.execute(create_sql)
                        created.append(table_name)
                        self.stdout.write(self.style.SUCCESS(f"  ✓ {table_name} (creada)"))
                except Exception as e:
                    errors.append((table_name, str(e)))
                    self.stdout.write(self.style.ERROR(f"  ✗ {table_name}: {str(e)}"))

            # Resumen
            self.stdout.write("\n" + "="*60)
            self.stdout.write(f"Tablas existentes: {len(existing)}")
            self.stdout.write(f"Tablas creadas: {len(created)}")
            self.stdout.write(f"Errores: {len(errors)}")
            
            if created:
                self.stdout.write(self.style.SUCCESS(f"\n✓ Se crearon {len(created)} tabla(s) exitosamente"))
            if errors:
                self.stdout.write(self.style.ERROR(f"\n✗ Hubo {len(errors)} error(es)"))
