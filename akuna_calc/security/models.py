from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import os


class AuditLog(models.Model):
    """Registro de auditoría de todas las acciones del sistema"""
    
    ACTION_CHOICES = [
        ('CREATE', 'Crear'),
        ('UPDATE', 'Actualizar'),
        ('DELETE', 'Eliminar'),
        ('LOGIN', 'Inicio de sesión'),
        ('LOGOUT', 'Cierre de sesión'),
        ('LOGIN_FAILED', 'Intento de login fallido'),
        ('VIEW', 'Visualizar'),
        ('EXPORT', 'Exportar'),
        ('PRINT', 'Imprimir'),
    ]
    
    LEVEL_CHOICES = [
        ('INFO', 'Información'),
        ('WARNING', 'Advertencia'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Crítico'),
    ]
    
    # Usuario y acción
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    username = models.CharField(max_length=150, blank=True)  # Por si el usuario se elimina
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default='INFO')
    
    # Detalles
    model_name = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=100, blank=True)
    object_repr = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    
    # Datos técnicos
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    path = models.CharField(max_length=500, blank=True)
    method = models.CharField(max_length=10, blank=True)
    
    # Cambios (JSON)
    changes = models.JSONField(null=True, blank=True)
    
    # Timestamp
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        verbose_name = 'Log de Auditoría'
        verbose_name_plural = 'Logs de Auditoría'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {self.username} - {self.get_action_display()}"


class LoginAttempt(models.Model):
    """Registro de intentos de login para detectar ataques"""
    
    username = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    success = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        verbose_name = 'Intento de Login'
        verbose_name_plural = 'Intentos de Login'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['ip_address', '-timestamp']),
            models.Index(fields=['username', '-timestamp']),
        ]
    
    def __str__(self):
        status = "✓" if self.success else "✗"
        return f"{status} {self.username} - {self.ip_address} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"


class SecuritySettings(models.Model):
    """Configuración de seguridad del sistema"""
    
    # Límites de intentos
    max_login_attempts = models.IntegerField(default=5, help_text="Intentos máximos de login antes de bloqueo")
    lockout_duration = models.IntegerField(default=30, help_text="Minutos de bloqueo tras exceder intentos")
    
    # Sesiones
    session_timeout = models.IntegerField(default=60, help_text="Minutos de inactividad antes de cerrar sesión")
    force_password_change_days = models.IntegerField(default=90, help_text="Días para forzar cambio de contraseña (0=desactivado)")
    
    # Contraseñas
    min_password_length = models.IntegerField(default=8)
    require_uppercase = models.BooleanField(default=True)
    require_lowercase = models.BooleanField(default=True)
    require_numbers = models.BooleanField(default=True)
    require_special_chars = models.BooleanField(default=False)
    
    # Auditoría
    log_all_actions = models.BooleanField(default=True)
    log_retention_days = models.IntegerField(default=365, help_text="Días para mantener logs")
    
    # Backup
    auto_backup_enabled = models.BooleanField(default=False)
    backup_frequency_hours = models.IntegerField(default=24)
    backup_retention_days = models.IntegerField(default=30)
    
    # Metadata
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        verbose_name = 'Configuración de Seguridad'
        verbose_name_plural = 'Configuración de Seguridad'
    
    def __str__(self):
        return f"Configuración de Seguridad (actualizada: {self.updated_at.strftime('%Y-%m-%d %H:%M')})"
    
    def save(self, *args, **kwargs):
        # Solo permitir una instancia
        self.pk = 1
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        """Obtener o crear configuración única"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class IPBlacklist(models.Model):
    """IPs bloqueadas por seguridad"""
    
    ip_address = models.GenericIPAddressField(unique=True)
    reason = models.TextField()
    blocked_at = models.DateTimeField(auto_now_add=True)
    blocked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="Dejar vacío para bloqueo permanente")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'IP Bloqueada'
        verbose_name_plural = 'IPs Bloqueadas'
        ordering = ['-blocked_at']
    
    def __str__(self):
        return f"{self.ip_address} - {self.reason[:50]}"
    
    def is_expired(self):
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at


class Backup(models.Model):
    """Registro de backups del sistema"""
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('running', 'En proceso'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
    ]
    
    filename = models.CharField(max_length=255)
    filepath = models.CharField(max_length=500)
    size_bytes = models.BigIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    # Estadísticas
    tables_count = models.IntegerField(default=0)
    records_count = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = 'Backup'
        verbose_name_plural = 'Backups'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.filename} - {self.get_status_display()}"
    
    def get_size_display(self):
        """Retorna tamaño en formato legible"""
        size = self.size_bytes
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"
    
    def file_exists(self):
        """Verifica si el archivo existe"""
        return os.path.exists(self.filepath)
    
    def delete_file(self):
        """Elimina el archivo físico"""
        if self.file_exists():
            try:
                os.remove(self.filepath)
                return True
            except:
                return False
        return False
