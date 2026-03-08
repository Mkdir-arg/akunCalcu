from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Actualiza todas las tablas de la base de datos para producción'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # tipo_perfil en perfiles
            try:
                cursor.execute("ALTER TABLE perfiles ADD COLUMN tipo_perfil TEXT")
                self.stdout.write(self.style.SUCCESS('✓ Campo tipo_perfil agregado a perfiles'))
            except Exception as e:
                if '1060' in str(e):
                    self.stdout.write(self.style.WARNING('tipo_perfil ya existe en perfiles'))
                else:
                    self.stdout.write(self.style.ERROR(f'Error tipo_perfil: {e}'))
            
            # Idproducto en vidrios
            try:
                cursor.execute("ALTER TABLE vidrios ADD COLUMN Idproducto TEXT")
                self.stdout.write(self.style.SUCCESS('✓ Campo Idproducto agregado a vidrios'))
            except Exception as e:
                if '1060' in str(e):
                    self.stdout.write(self.style.WARNING('Idproducto ya existe'))
                else:
                    self.stdout.write(self.style.ERROR(f'Error Idproducto: {e}'))
            
            # rebaje_ancho en vidrios
            try:
                cursor.execute("ALTER TABLE vidrios ADD COLUMN rebaje_ancho TEXT")
                self.stdout.write(self.style.SUCCESS('✓ Campo rebaje_ancho agregado a vidrios'))
            except Exception as e:
                if '1060' in str(e):
                    self.stdout.write(self.style.WARNING('rebaje_ancho ya existe'))
                else:
                    self.stdout.write(self.style.ERROR(f'Error rebaje_ancho: {e}'))
            
            # rebaje_alto en vidrios
            try:
                cursor.execute("ALTER TABLE vidrios ADD COLUMN rebaje_alto TEXT")
                self.stdout.write(self.style.SUCCESS('✓ Campo rebaje_alto agregado a vidrios'))
            except Exception as e:
                if '1060' in str(e):
                    self.stdout.write(self.style.WARNING('rebaje_alto ya existe'))
                else:
                    self.stdout.write(self.style.ERROR(f'Error rebaje_alto: {e}'))
            
            # Idhoja en vidrios
            try:
                cursor.execute("ALTER TABLE vidrios ADD COLUMN Idhoja TEXT")
                self.stdout.write(self.style.SUCCESS('✓ Campo Idhoja agregado a vidrios'))
            except Exception as e:
                if '1060' in str(e):
                    self.stdout.write(self.style.WARNING('Idhoja ya existe'))
                else:
                    self.stdout.write(self.style.ERROR(f'Error Idhoja: {e}'))
            
            # cant en accesorios
            try:
                cursor.execute("ALTER TABLE accesorios ADD COLUMN cant INT DEFAULT 1")
                self.stdout.write(self.style.SUCCESS('✓ Campo cant agregado a accesorios'))
            except Exception as e:
                if '1060' in str(e):
                    self.stdout.write(self.style.WARNING('cant ya existe'))
                else:
                    self.stdout.write(self.style.ERROR(f'Error cant: {e}'))
            
            # Tipo TEXT en accesorios
            try:
                cursor.execute("ALTER TABLE accesorios MODIFY COLUMN Tipo TEXT")
                self.stdout.write(self.style.SUCCESS('✓ Campo Tipo modificado a TEXT en accesorios'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error Tipo: {e}'))
            
            # obligatorio en despiece_accesorios_hoja
            try:
                cursor.execute("ALTER TABLE despiece_accesorios_hoja ADD COLUMN obligatorio TEXT")
                self.stdout.write(self.style.SUCCESS('✓ Campo obligatorio agregado a despiece_accesorios_hoja'))
            except Exception as e:
                if '1060' in str(e):
                    self.stdout.write(self.style.WARNING('obligatorio ya existe en despiece_accesorios_hoja'))
                else:
                    self.stdout.write(self.style.ERROR(f'Error obligatorio hoja: {e}'))
            
            # obligatorio en despiece_accesorios_marco
            try:
                cursor.execute("ALTER TABLE despiece_accesorios_marco ADD COLUMN obligatorio TEXT")
                self.stdout.write(self.style.SUCCESS('✓ Campo obligatorio agregado a despiece_accesorios_marco'))
            except Exception as e:
                if '1060' in str(e):
                    self.stdout.write(self.style.WARNING('obligatorio ya existe en despiece_accesorios_marco'))
                else:
                    self.stdout.write(self.style.ERROR(f'Error obligatorio marco: {e}'))
            
            # cant_20 en accesorios
            try:
                cursor.execute("ALTER TABLE accesorios ADD COLUMN cant_20 INT DEFAULT 20")
                self.stdout.write(self.style.SUCCESS('✓ Campo cant_20 agregado a accesorios'))
            except Exception as e:
                if '1060' in str(e):
                    self.stdout.write(self.style.WARNING('cant_20 ya existe'))
                else:
                    self.stdout.write(self.style.ERROR(f'Error cant_20: {e}'))
            
            self.stdout.write(self.style.SUCCESS('\n✓ Actualización completada'))
