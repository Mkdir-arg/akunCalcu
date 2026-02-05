from django.contrib import admin
from django.utils.html import format_html
from .models import AuditLog, LoginAttempt, SecuritySettings, IPBlacklist, Backup


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'username', 'action_badge', 'level_badge', 'model_name', 'description_short', 'ip_address']
    list_filter = ['action', 'level', 'timestamp', 'model_name']
    search_fields = ['username', 'description', 'ip_address', 'object_repr']
    readonly_fields = ['timestamp', 'user', 'username', 'action', 'level', 'model_name', 
                      'object_id', 'object_repr', 'description', 'ip_address', 'user_agent', 
                      'path', 'method', 'changes']
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def action_badge(self, obj):
        colors = {
            'CREATE': 'success',
            'UPDATE': 'info',
            'DELETE': 'danger',
            'LOGIN': 'primary',
            'LOGOUT': 'secondary',
            'LOGIN_FAILED': 'warning',
        }
        color = colors.get(obj.action, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color, obj.get_action_display()
        )
    action_badge.short_description = 'Acción'
    
    def level_badge(self, obj):
        colors = {
            'INFO': 'info',
            'WARNING': 'warning',
            'ERROR': 'danger',
            'CRITICAL': 'danger',
        }
        color = colors.get(obj.level, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color, obj.get_level_display()
        )
    level_badge.short_description = 'Nivel'
    
    def description_short(self, obj):
        return obj.description[:100] + '...' if len(obj.description) > 100 else obj.description
    description_short.short_description = 'Descripción'


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'username', 'ip_address', 'success_badge', 'user_agent_short']
    list_filter = ['success', 'timestamp']
    search_fields = ['username', 'ip_address']
    readonly_fields = ['username', 'ip_address', 'user_agent', 'success', 'timestamp']
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def success_badge(self, obj):
        if obj.success:
            return format_html('<span class="badge badge-success">✓ Exitoso</span>')
        return format_html('<span class="badge badge-danger">✗ Fallido</span>')
    success_badge.short_description = 'Estado'
    
    def user_agent_short(self, obj):
        return obj.user_agent[:50] + '...' if len(obj.user_agent) > 50 else obj.user_agent
    user_agent_short.short_description = 'Navegador'


@admin.register(SecuritySettings)
class SecuritySettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Intentos de Login', {
            'fields': ('max_login_attempts', 'lockout_duration')
        }),
        ('Sesiones', {
            'fields': ('session_timeout', 'force_password_change_days')
        }),
        ('Contraseñas', {
            'fields': ('min_password_length', 'require_uppercase', 'require_lowercase', 
                      'require_numbers', 'require_special_chars')
        }),
        ('Auditoría', {
            'fields': ('log_all_actions', 'log_retention_days')
        }),
        ('Backup', {
            'fields': ('auto_backup_enabled', 'backup_frequency_hours', 'backup_retention_days')
        }),
        ('Metadata', {
            'fields': ('updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['updated_at', 'updated_by']
    
    def has_add_permission(self, request):
        # Solo permitir una instancia
        return not SecuritySettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(IPBlacklist)
class IPBlacklistAdmin(admin.ModelAdmin):
    list_display = ['ip_address', 'reason_short', 'blocked_at', 'expires_at', 'is_active_badge']
    list_filter = ['is_active', 'blocked_at']
    search_fields = ['ip_address', 'reason']
    readonly_fields = ['blocked_at', 'blocked_by']
    
    def reason_short(self, obj):
        return obj.reason[:50] + '...' if len(obj.reason) > 50 else obj.reason
    reason_short.short_description = 'Razón'
    
    def is_active_badge(self, obj):
        if obj.is_active and not obj.is_expired():
            return format_html('<span class="badge badge-danger">🔒 Bloqueada</span>')
        return format_html('<span class="badge badge-success">✓ Desbloqueada</span>')
    is_active_badge.short_description = 'Estado'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.blocked_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Backup)
class BackupAdmin(admin.ModelAdmin):
    list_display = ['filename', 'created_at', 'status_badge', 'size_display', 'tables_count']
    list_filter = ['status', 'created_at']
    search_fields = ['filename']
    readonly_fields = ['filename', 'filepath', 'size_bytes', 'status', 'created_at', 
                      'completed_at', 'created_by', 'error_message', 'tables_count', 'records_count']
    
    def has_add_permission(self, request):
        return False
    
    def status_badge(self, obj):
        colors = {
            'pending': 'secondary',
            'running': 'info',
            'completed': 'success',
            'failed': 'danger',
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Estado'
    
    def size_display(self, obj):
        return obj.get_size_display()
    size_display.short_description = 'Tamaño'
