from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
from .models import AuditLog, LoginAttempt, SecuritySettings, IPBlacklist
import json


HEALTHCHECK_PATHS = {'/health', '/health/'}
SECURITY_EXEMPT_PATHS = {
    '/',
    '/login',
    '/login/',
    '/logout',
    '/logout/',
    '/health',
    '/health/',
    '/favicon.ico',
}
# La consulta periódica de tiempo real (live.js) no es actividad del usuario: si contara,
# una pestaña abierta impediría el cierre de sesión por inactividad.
PASSIVE_POLL_PATHS = {'/core/api/live/'}

SECURITY_EXEMPT_PREFIXES = (
    '/static/',
    '/media/',
    '/admin/jsi18n/',
    '/security/backups/api/',
    '/security/salud/api/',
    '/agenda/api/',
    '/solicitudes/api/',
)


def is_healthcheck_request(request):
    return request.path in HEALTHCHECK_PATHS


def is_security_exempt_request(request):
    path = request.path
    return path in SECURITY_EXEMPT_PATHS or any(path.startswith(prefix) for prefix in SECURITY_EXEMPT_PREFIXES)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def login_lockout_minutes(ip_address, username):
    """Minutos que le faltan a este usuario, desde esta IP, para volver a intentar (0 = libre).

    El bloqueo es por usuario + IP y no por IP sola: la oficina comparte una IP pública y
    un usuario que se equivoca la clave no puede dejar afuera a los demás.
    """
    if not username:
        return 0
    from datetime import timedelta
    settings = SecuritySettings.get_settings()
    if settings.max_login_attempts <= 0 or settings.lockout_duration <= 0:
        return 0
    window = timedelta(minutes=settings.lockout_duration)
    now = timezone.now()
    failed = list(
        LoginAttempt.objects.filter(
            ip_address=ip_address,
            username__iexact=username,
            success=False,
            timestamp__gte=now - window,
        ).order_by('-timestamp').values_list('timestamp', flat=True)[:settings.max_login_attempts]
    )
    if len(failed) < settings.max_login_attempts:
        return 0
    remaining = (failed[-1] + window) - now
    return max(1, -(-int(remaining.total_seconds()) // 60))


class AuditMiddleware(MiddlewareMixin):
    """Middleware para registrar todas las acciones del sistema"""
    
    EXCLUDED_PATHS = [
        '/static/',
        '/media/',
        '/admin/jsi18n/',
        '/favicon.ico',
        '/health',
        '/health/',
        '/security/backups/api/',
        '/agenda/api/',
        '/solicitudes/api/',
        '/core/api/',
    ]
    
    SENSITIVE_FIELDS = ['password', 'token', 'secret', 'key']
    
    def process_request(self, request):
        # Guardar datos para usar en process_response
        request._audit_start_time = timezone.now()
        return None
    
    def process_response(self, request, response):
        # No auditar rutas excluidas
        if any(request.path.startswith(path) for path in self.EXCLUDED_PATHS):
            return response

        if not self._should_audit(request):
            return response
        
        # Solo auditar si está configurado
        settings = SecuritySettings.get_settings()
        if not settings.log_all_actions:
            return response

        self._create_audit_log(request, response)
        
        return response
    
    def _create_audit_log(self, request, response):
        try:
            action = self._get_action(request)
            if request.path == '/login/' and response.status_code != 302:
                action = 'LOGIN_FAILED'
            user = request.user if request.user.is_authenticated else None
            username = user.username if user else request.POST.get('username', 'Anonymous')
            ip_address = self._get_client_ip(request)
            status_level = 'ERROR' if response.status_code >= 400 else 'INFO'
            if action == 'LOGIN_FAILED':
                status_level = 'WARNING'

            resolver_match = getattr(request, 'resolver_match', None)
            route_name = resolver_match.view_name if resolver_match else ''
            object_id = ''
            if resolver_match:
                object_id = str(resolver_match.kwargs.get('pk') or resolver_match.kwargs.get('id') or '')

            AuditLog.objects.create(
                user=user,
                username=username,
                action=action,
                level=status_level,
                model_name=route_name[:100],
                object_id=object_id,
                object_repr=request.POST.get('nombre', '')[:200] if request.method == 'POST' else '',
                path=request.path,
                method=request.method,
                ip_address=ip_address,
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                description=f"{request.method} {request.path} ({response.status_code})",
            )
        except Exception as e:
            # No fallar si hay error en auditoría
            print(f"Error en auditoría: {e}")

    def _should_audit(self, request):
        if request.path in ['/login', '/login/']:
            return request.method == 'POST'

        if request.path in ['/logout', '/logout/']:
            return True

        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            return True
        return False
    
    def _get_action(self, request):
        """Determinar tipo de acción según método HTTP y ruta."""
        path = request.path.lower()
        route_name = ''
        if getattr(request, 'resolver_match', None):
            route_name = (request.resolver_match.view_name or '').lower()

        if path == '/login/':
            return 'LOGIN'

        if path == '/logout/':
            return 'LOGOUT'

        if request.method == 'POST':
            if any(token in path or token in route_name for token in ['delete', 'eliminar']):
                return 'DELETE'
            if any(token in path or token in route_name for token in ['edit', 'editar', 'update']):
                return 'UPDATE'
            if any(token in path or token in route_name for token in ['login']):
                return 'LOGIN'
            return 'CREATE'
        elif request.method in ['PUT', 'PATCH']:
            return 'UPDATE'
        elif request.method == 'DELETE':
            return 'DELETE'
        return 'VIEW'

    def process_exception(self, request, exception):
        if not self._should_audit(request):
            return None

        try:
            user = request.user if request.user.is_authenticated else None
            AuditLog.objects.create(
                user=user,
                username=user.username if user else request.POST.get('username', 'Anonymous'),
                action='LOGIN_FAILED' if request.path == '/login/' else self._get_action(request),
                level='ERROR',
                path=request.path,
                method=request.method,
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                description=f"{request.method} {request.path} - error: {exception}",
            )
        except Exception:
            pass
        return None
    
    def _get_client_ip(self, request):
        """Obtener IP real del cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SecurityMiddleware(MiddlewareMixin):
    """Middleware para controles de seguridad"""
    
    def process_request(self, request):
        if is_security_exempt_request(request):
            return None

        # Verificar IP bloqueada
        ip_address = self._get_client_ip(request)
        
        if self._is_ip_blocked(ip_address):
            if request.user.is_authenticated:
                from django.contrib.auth import logout
                logout(request)
            messages.error(request, 'Su IP ha sido bloqueada por razones de seguridad.')
            return redirect('login')
        
        # Verificar timeout de sesión
        if request.user.is_authenticated:
            self._check_session_timeout(request)
        
        return None
    
    def _get_client_ip(self, request):
        """Obtener IP real del cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _is_ip_blocked(self, ip_address):
        """Verificar si la IP está bloqueada"""
        try:
            return IPBlacklist.is_ip_blocked(ip_address)
        except Exception:
            return False
    
    def _check_session_timeout(self, request):
        """Verificar timeout de sesión por inactividad"""
        try:
            settings = SecuritySettings.get_settings()
            if settings.session_timeout <= 0:
                return
            
            last_activity = request.session.get('last_activity')
            if last_activity:
                from datetime import datetime, timedelta
                last_activity_time = datetime.fromisoformat(last_activity)
                timeout = timedelta(minutes=settings.session_timeout)
                
                if timezone.now() - last_activity_time > timeout:
                    # Sesión expirada
                    from django.contrib.auth import logout
                    logout(request)
                    messages.warning(request, 'Su sesión ha expirado por inactividad.')
                    return redirect('login')
            
            # Actualizar última actividad
            if request.path not in PASSIVE_POLL_PATHS:
                request.session['last_activity'] = timezone.now().isoformat()
        except:
            pass


class LoginAttemptMiddleware(MiddlewareMixin):
    """Middleware para controlar intentos de login"""
    
    def process_response(self, request, response):
        # Solo procesar en la página de login
        if request.path == '/login/' and request.method == 'POST' and not getattr(request, '_login_locked', False):
            self._record_login_attempt(request, response)
        
        return response
    
    def _record_login_attempt(self, request, response):
        """Registrar intento de login"""
        try:
            username = request.POST.get('username', '')
            ip_address = get_client_ip(request)
            success = response.status_code == 302  # Redirect = login exitoso
            
            # Registrar intento
            LoginAttempt.objects.create(
                username=username,
                ip_address=ip_address,
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                success=success
            )
        except Exception as e:
            print(f"Error registrando intento de login: {e}")
    
    def _get_client_ip(self, request):
        """Obtener IP real del cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
