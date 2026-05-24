from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import FileResponse, Http404, HttpResponse, StreamingHttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.management import call_command
from django.core.paginator import Paginator
from django.conf import settings as django_settings
from django.utils import timezone

from .models import AuditLog, Backup, SecuritySettings
import os
import subprocess
from datetime import datetime


BACKUP_PASSWORD = "Modeoffputin.1167252190@!"


AUDIT_MODULE_OPTIONS = [
    ('security', 'Seguridad'),
    ('comercial', 'Comercial'),
    ('reportes', 'Reportes'),
    ('productos', 'Productos'),
    ('despiece', 'Despiece'),
    ('fabrica', 'Fábrica'),
    ('facturacion', 'Facturación'),
    ('presupuestos', 'Presupuestos'),
    ('configuracion', 'Configuración'),
    ('otros', 'Otros'),
]


@login_required
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


@login_required
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


def _get_audit_module(path):
    if not path:
        return 'otros'

    normalized_path = path.lower()
    module_prefix_map = [
        ('/security/', 'security'),
        ('/comercial/reportes/', 'reportes'),
        ('/comercial/', 'comercial'),
        ('/productos/', 'productos'),
        ('/plantillas/', 'despiece'),
        ('/pricing/', 'fabrica'),
        ('/facturacion/', 'facturacion'),
        ('/presupuestos/', 'presupuestos'),
        ('/configuracion/', 'configuracion'),
        ('/admin-usuarios/', 'configuracion'),
        ('/login/', 'security'),
        ('/logout/', 'security'),
    ]

    for prefix, module_key in module_prefix_map:
        if normalized_path.startswith(prefix):
            return module_key

    return 'otros'


def _get_audit_module_label(path):
    module_key = _get_audit_module(path)
    options_map = dict(AUDIT_MODULE_OPTIONS)
    return options_map.get(module_key, 'Otros')


def _build_module_query(module_key):
    if module_key == 'otros':
        return ~Q(path__startswith='/security/') & ~Q(path__startswith='/comercial/') & ~Q(path__startswith='/productos/') & ~Q(path__startswith='/plantillas/') & ~Q(path__startswith='/pricing/') & ~Q(path__startswith='/facturacion/') & ~Q(path__startswith='/presupuestos/') & ~Q(path__startswith='/configuracion/') & ~Q(path__startswith='/admin-usuarios/') & ~Q(path__startswith='/login/') & ~Q(path__startswith='/logout/')

    if module_key == 'security':
        return Q(path__startswith='/security/') | Q(path__startswith='/login/') | Q(path__startswith='/logout/')

    if module_key == 'reportes':
        return Q(path__startswith='/comercial/reportes/')

    if module_key == 'comercial':
        return Q(path__startswith='/comercial/') & ~Q(path__startswith='/comercial/reportes/')

    module_prefix_map = {
        'productos': ['/productos/'],
        'despiece': ['/plantillas/'],
        'fabrica': ['/pricing/'],
        'facturacion': ['/facturacion/'],
        'presupuestos': ['/presupuestos/'],
        'configuracion': ['/configuracion/', '/admin-usuarios/'],
    }

    prefixes = module_prefix_map.get(module_key, [])

    query = Q()
    for prefix in prefixes:
        query |= Q(path__startswith=prefix)
    return query


@login_required
def audit_list(request):
    logs = AuditLog.objects.select_related('user').all().order_by('-timestamp')

    username = request.GET.get('username', '').strip()
    action = request.GET.get('action', '').strip()
    module = request.GET.get('module', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()

    if username:
        logs = logs.filter(username__icontains=username)

    if action:
        logs = logs.filter(action=action)

    if date_from:
        logs = logs.filter(timestamp__date__gte=date_from)

    if date_to:
        logs = logs.filter(timestamp__date__lte=date_to)

    if module:
        logs = logs.filter(_build_module_query(module))

    paginator = Paginator(logs, 50)
    page_obj = paginator.get_page(request.GET.get('page'))

    for log in page_obj:
        log.module_label = _get_audit_module_label(log.path)
        log.object_reference = log.object_repr or log.object_id or log.path

    context = {
        'logs': page_obj,
        'page_obj': page_obj,
        'action_choices': AuditLog.ACTION_CHOICES,
        'module_options': AUDIT_MODULE_OPTIONS,
        'filters': {
            'username': username,
            'action': action,
            'module': module,
            'date_from': date_from,
            'date_to': date_to,
        },
    }
    return render(request, 'security/audit_list.html', context)


@login_required
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


@login_required
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


@login_required
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


@login_required
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


@login_required
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


def _build_mysqldump_command():
    """Construye el comando mysqldump usando la config de Django.

    Reutilizable por el management command y por el endpoint API.
    Usa --skip-ssl por compatibilidad con mariadb-client (ver HFX-001).
    """
    db_config = django_settings.DATABASES['default']
    cmd = [
        'mysqldump',
        f"--host={db_config['HOST']}",
        f"--user={db_config['USER']}",
        f"--password={db_config['PASSWORD']}",
        '--skip-ssl',
        '--single-transaction',
        '--quick',
        '--lock-tables=false',
    ]
    if db_config.get('PORT'):
        cmd.insert(3, f"--port={db_config['PORT']}")
    cmd.append(db_config['NAME'])
    return cmd


@login_required
@backup_required
@require_http_methods(["POST"])
def backup_trigger_n8n(request):
    """Fuerza la ejecución del workflow de backup n8n → Google Drive."""
    import urllib.request
    import urllib.error
    import json

    n8n_url = os.environ.get('N8N_BASE_URL', 'https://n8n-production-9a1a.up.railway.app').rstrip('/')
    workflow_id = os.environ.get('N8N_BACKUP_WORKFLOW_ID', '9qXmKDqq0mOEKnHc')
    api_key = os.environ.get('N8N_API_KEY', '')

    if not api_key:
        messages.error(request, '❌ N8N_API_KEY no está configurado en el servidor.')
        return redirect('security:backup_list')

    try:
        url = f"{n8n_url}/api/v1/workflows/{workflow_id}/run"
        req = urllib.request.Request(
            url,
            data=b'{}',
            headers={
                'Content-Type': 'application/json',
                'X-N8N-API-KEY': api_key,
            },
            method='POST',
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp_body = json.loads(resp.read())
        execution_id = resp_body.get('data', {}).get('executionId', '—')
        messages.success(
            request,
            f'✅ Workflow n8n iniciado (ejecución #{execution_id}). '
            'El backup se guardará en Google Drive en breve.'
        )
    except urllib.error.HTTPError as exc:
        body = exc.read().decode('utf-8', errors='replace')[:300]
        messages.error(request, f'❌ Error n8n HTTP {exc.code}: {body}')
    except Exception as exc:
        messages.error(request, f'❌ Error al iniciar workflow n8n: {exc}')

    return redirect('security:backup_list')


@csrf_exempt
@require_http_methods(["POST"])
def backup_api_create(request):
    """Endpoint API protegido por header X-Bot-Secret.

    Ejecuta mysqldump y devuelve el SQL como respuesta binaria stream.
    Registra el backup como storage_location='drive'.
    Pensado para ser consumido por n8n + Google Drive.
    """
    expected_secret = os.environ.get('BACKUP_BOT_SECRET', '')
    received_secret = request.META.get('HTTP_X_BOT_SECRET', '')

    if not expected_secret or received_secret != expected_secret:
        return JsonResponse({'error': 'forbidden'}, status=403)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'backup_{timestamp}.sql'

    backup = Backup.objects.create(
        filename=filename,
        filepath='',
        status='running',
        storage_location='drive',
    )

    try:
        cmd = _build_mysqldump_command()
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        total_bytes = {'count': 0}

        def stream_chunks():
            try:
                while True:
                    chunk = process.stdout.read(64 * 1024)
                    if not chunk:
                        break
                    total_bytes['count'] += len(chunk)
                    yield chunk
                process.wait()
                if process.returncode != 0:
                    err = process.stderr.read().decode('utf-8', errors='replace')
                    backup.status = 'failed'
                    backup.error_message = f'mysqldump rc={process.returncode}: {err[:500]}'
                    backup.save()
                else:
                    backup.size_bytes = total_bytes['count']
                    backup.status = 'completed'
                    backup.completed_at = timezone.now()
                    backup.save()
            except Exception as exc:
                backup.status = 'failed'
                backup.error_message = str(exc)[:500]
                backup.save()
                raise

        response = StreamingHttpResponse(
            stream_chunks(),
            content_type='application/sql',
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['X-Backup-Id'] = str(backup.id)
        return response

    except Exception as exc:
        backup.status = 'failed'
        backup.error_message = str(exc)[:500]
        backup.save()
        return JsonResponse({'error': 'backup_failed', 'detail': str(exc)}, status=500)
