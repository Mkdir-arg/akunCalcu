from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import FileResponse, Http404, HttpResponse
from django.views.decorators.http import require_http_methods
from django.core.management import call_command
from .models import Backup, SecuritySettings
import os


BACKUP_PASSWORD = "Modeoffputin.1167252190@!"


def backup_login(request):
    """Vista de login para acceder al módulo de backups"""
    if request.method == 'POST':
        password = request.POST.get('password', '')
        
        if password == BACKUP_PASSWORD:
            # Guardar en sesión
            request.session['backup_authenticated'] = True
            return redirect('security:backup_list')
        else:
            messages.error(request, 'Contraseña incorrecta')
    
    return render(request, 'security/backup_login.html')


def backup_logout(request):
    """Cerrar sesión del módulo de backups"""
    if 'backup_authenticated' in request.session:
        del request.session['backup_authenticated']
    messages.success(request, 'Sesión cerrada correctamente')
    return redirect('security:backup_login')


def backup_required(view_func):
    """Decorador para requerir autenticación de backup"""
    def wrapper(request, *args, **kwargs):
        if not request.session.get('backup_authenticated'):
            messages.warning(request, 'Debe autenticarse para acceder a esta sección')
            return redirect('security:backup_login')
        return view_func(request, *args, **kwargs)
    return wrapper


@backup_required
def backup_list(request):
    """Lista de backups disponibles"""
    backups = Backup.objects.all().order_by('-created_at')
    
    # Estadísticas
    total_backups = backups.count()
    completed_backups = backups.filter(status='completed').count()
    total_size = sum(b.size_bytes for b in backups.filter(status='completed'))
    
    # Configuración
    settings = SecuritySettings.get_settings()
    
    context = {
        'backups': backups,
        'total_backups': total_backups,
        'completed_backups': completed_backups,
        'total_size': _format_bytes(total_size),
        'settings': settings,
    }
    
    return render(request, 'security/backup_list.html', context)


@backup_required
@require_http_methods(["POST"])
def backup_create(request):
    """Crear nuevo backup manualmente"""
    try:
        messages.info(request, 'Creando backup... Esto puede tomar unos minutos.')
        
        # Ejecutar comando de backup
        call_command('create_backup')
        
        messages.success(request, '✅ Backup creado exitosamente')
    except Exception as e:
        messages.error(request, f'❌ Error al crear backup: {str(e)}')
    
    return redirect('security:backup_list')


@backup_required
def backup_download(request, pk):
    """Descargar archivo de backup"""
    backup = get_object_or_404(Backup, pk=pk)
    
    if backup.status != 'completed':
        messages.error(request, 'El backup no está completado')
        return redirect('security:backup_list')
    
    if not backup.file_exists():
        messages.error(request, 'El archivo de backup no existe')
        return redirect('security:backup_list')
    
    try:
        response = FileResponse(
            open(backup.filepath, 'rb'),
            as_attachment=True,
            filename=backup.filename
        )
        return response
    except Exception as e:
        messages.error(request, f'Error al descargar: {str(e)}')
        return redirect('security:backup_list')


@backup_required
@require_http_methods(["POST"])
def backup_delete(request, pk):
    """Eliminar backup"""
    backup = get_object_or_404(Backup, pk=pk)
    
    try:
        # Eliminar archivo físico
        if backup.file_exists():
            backup.delete_file()
        
        # Eliminar registro
        filename = backup.filename
        backup.delete()
        
        messages.success(request, f'Backup "{filename}" eliminado correctamente')
    except Exception as e:
        messages.error(request, f'Error al eliminar backup: {str(e)}')
    
    return redirect('security:backup_list')


@backup_required
def backup_settings(request):
    """Configuración de backups"""
    settings = SecuritySettings.get_settings()
    
    if request.method == 'POST':
        try:
            settings.auto_backup_enabled = request.POST.get('auto_backup_enabled') == 'on'
            settings.backup_frequency_hours = int(request.POST.get('backup_frequency_hours', 24))
            settings.backup_retention_days = int(request.POST.get('backup_retention_days', 30))
            settings.updated_by = request.user if request.user.is_authenticated else None
            settings.save()
            
            messages.success(request, 'Configuración actualizada correctamente')
            return redirect('security:backup_list')
        except Exception as e:
            messages.error(request, f'Error al guardar configuración: {str(e)}')
    
    return render(request, 'security/backup_settings.html', {'settings': settings})


def _format_bytes(bytes_size):
    """Formatea bytes a formato legible"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"
