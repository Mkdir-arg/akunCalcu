from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from security.models import Backup, SecuritySettings
import subprocess
import os
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Crea un backup de la base de datos MySQL'

    def add_arguments(self, parser):
        parser.add_argument(
            '--auto',
            action='store_true',
            help='Ejecutar en modo automático (limpia backups antiguos)',
        )

    def handle(self, *args, **options):
        auto_mode = options.get('auto', False)
        
        self.stdout.write(self.style.SUCCESS('🔄 Iniciando backup de base de datos...'))
        
        # Crear backup
        backup = Backup.objects.create(
            filename='',
            filepath='',
            status='running'
        )
        
        try:
            # Generar nombre de archivo
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'backup_{timestamp}.sql'
            
            # Directorio de backups
            backup_dir = settings.BASE_DIR / 'backups'
            backup_dir.mkdir(exist_ok=True)
            
            filepath = backup_dir / filename
            
            # Obtener configuración de BD
            db_config = settings.DATABASES['default']
            db_name = db_config['NAME']
            db_user = db_config['USER']
            db_password = db_config['PASSWORD']
            db_host = db_config['HOST']
            db_port = db_config['PORT']
            
            # Comando mysqldump
            cmd = [
                'mysqldump',
                f'--host={db_host}',
                f'--user={db_user}',
                f'--password={db_password}',
                '--single-transaction',
                '--quick',
                '--lock-tables=false',
                db_name
            ]
            
            # Agregar puerto solo si está definido
            if db_port:
                cmd.insert(3, f'--port={db_port}')
            
            # Ejecutar backup
            self.stdout.write('📦 Ejecutando mysqldump...')
            
            with open(filepath, 'w', encoding='utf-8') as f:
                result = subprocess.run(
                    cmd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    text=True
                )
            
            if result.returncode != 0:
                raise Exception(f'Error en mysqldump: {result.stderr}')
            
            # Obtener tamaño del archivo
            file_size = os.path.getsize(filepath)
            
            # Contar tablas y registros (aproximado)
            tables_count = self._count_tables(filepath)
            
            # Actualizar backup
            backup.filename = filename
            backup.filepath = str(filepath)
            backup.size_bytes = file_size
            backup.status = 'completed'
            backup.completed_at = timezone.now()
            backup.tables_count = tables_count
            backup.save()
            
            self.stdout.write(self.style.SUCCESS(f'✅ Backup completado: {filename}'))
            self.stdout.write(self.style.SUCCESS(f'📊 Tamaño: {backup.get_size_display()}'))
            self.stdout.write(self.style.SUCCESS(f'📁 Ubicación: {filepath}'))
            
            # Limpiar backups antiguos si está en modo automático
            if auto_mode:
                self._cleanup_old_backups()
            
        except Exception as e:
            backup.status = 'failed'
            backup.error_message = str(e)
            backup.save()
            
            self.stdout.write(self.style.ERROR(f'❌ Error al crear backup: {e}'))
            raise
    
    def _count_tables(self, filepath):
        """Cuenta aproximadamente las tablas en el backup"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                return content.count('CREATE TABLE')
        except:
            return 0
    
    def _cleanup_old_backups(self):
        """Elimina backups antiguos según configuración"""
        try:
            settings_obj = SecuritySettings.get_settings()
            retention_days = settings_obj.backup_retention_days
            
            if retention_days <= 0:
                return
            
            cutoff_date = timezone.now() - timedelta(days=retention_days)
            
            old_backups = Backup.objects.filter(
                created_at__lt=cutoff_date,
                status='completed'
            )
            
            deleted_count = 0
            for backup in old_backups:
                if backup.delete_file():
                    backup.delete()
                    deleted_count += 1
            
            if deleted_count > 0:
                self.stdout.write(self.style.WARNING(f'🗑️  Eliminados {deleted_count} backups antiguos'))
        
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠️  Error limpiando backups: {e}'))
