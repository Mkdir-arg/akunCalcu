from django.contrib import messages
from django.contrib.auth import get_user_model, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Sum
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.cache import add_never_cache_headers
from django.utils.http import url_has_allowed_host_and_scheme
import re
from urllib.parse import urlencode
from django.contrib.auth.decorators import login_required
from datetime import datetime
from decimal import Decimal

from usuarios.access_control import get_default_url_for_user

User = get_user_model()


class AkunLoginView(LoginView):
    template_name = 'core/login.html'
    redirect_authenticated_user = True

    def dispatch(self, request, *args, **kwargs):
        # Después de un login correcto se vuelve acá con ?bienvenida=1 para mostrar la animación.
        # El POST tiene que seguir respondiendo 302: LoginAttemptMiddleware cuenta el 302 como login exitoso.
        # Va en dispatch porque LoginView redirige al usuario logueado antes de llegar a get().
        if request.method == 'GET' and request.user.is_authenticated and request.GET.get('bienvenida') == '1':
            destino = request.GET.get('next', '')
            # Solo rutas internas: el <meta refresh> le quita las comillas a la URL, así que
            # "'https://otro.com'" pasaría el validador de Django pero saldría del sitio.
            ruta_interna = destino.startswith('/') and not re.search(r"[\s'\"<>\\]", destino)
            if not (ruta_interna and url_has_allowed_host_and_scheme(destino, allowed_hosts={request.get_host()}, require_https=request.is_secure())):
                destino = get_default_url_for_user(request.user)
            if destino:
                response = render(request, self.template_name, {'bienvenida_url': destino})
                add_never_cache_headers(response)
                return response
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        from security.middleware import get_client_ip, login_lockout_minutes

        minutos = login_lockout_minutes(get_client_ip(request), request.POST.get('username', '').strip())
        if minutos:
            request._login_locked = True
            messages.error(
                request,
                f'Demasiados intentos fallidos con este usuario. Probá de nuevo en {minutos} minuto{"s" if minutos != 1 else ""}.',
            )
            return self.render_to_response(self.get_context_data(form=self.get_form_class()(request=request)))
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        auth_login(self.request, form.get_user())
        target_url = self.get_redirect_url() or get_default_url_for_user(self.request.user)
        if target_url:
            return HttpResponseRedirect(f"{reverse('login')}?{urlencode({'bienvenida': '1', 'next': target_url})}")

        messages.error(self.request, 'Tu usuario no tiene módulos asignados. Contacta a un administrador.')
        auth_logout(self.request)
        return redirect('login')


def healthcheck(request):
    return HttpResponse('ok', content_type='text/plain')

def index(request):
    if request.user.is_authenticated:
        target_url = get_default_url_for_user(request.user)
        if target_url:
            return redirect(target_url)
        auth_logout(request)
        messages.error(request, 'Tu usuario no tiene módulos asignados. Contacta a un administrador.')
        return redirect('login')
    return redirect('login')

@login_required
def home(request):
    from comercial.models import Venta, Compra, Cliente
    from usuarios.access_control import get_access_profile
    from solicitudes.models import SolicitudPresupuesto

    # Estadísticas comerciales
    total_ventas = Venta.objects.filter(deleted_at__isnull=True).aggregate(Sum('valor_total'))['valor_total__sum'] or Decimal('0')
    total_compras = Compra.objects.filter(deleted_at__isnull=True).aggregate(Sum('valor_total'))['valor_total__sum'] or Decimal('0')
    ventas_pendientes = Venta.objects.filter(deleted_at__isnull=True, estado='pendiente').count()
    clientes_count = Cliente.objects.filter(deleted_at__isnull=True).count()

    # Bandeja del vendedor: sus solicitudes de presupuesto sin atender.
    perfil = get_access_profile(request.user)
    es_vendedor = bool(perfil and perfil.rol and perfil.rol.codigo == 'vendedor')
    mis_solicitudes = []
    if es_vendedor:
        mis_solicitudes = list(
            SolicitudPresupuesto.objects
            .filter(vendedor=request.user, estado=SolicitudPresupuesto.ESTADO_ASIGNADA)
            .order_by('-fecha_recepcion')
        )

    context = {
        'total_ventas': total_ventas,
        'total_compras': total_compras,
        'ventas_pendientes': ventas_pendientes,
        'clientes_count': clientes_count,
        'es_vendedor': es_vendedor,
        'mis_solicitudes': mis_solicitudes,
    }

    return render(request, 'core/home.html', context)