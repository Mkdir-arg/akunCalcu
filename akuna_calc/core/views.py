from django.contrib import messages
from django.contrib.auth import get_user_model, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Sum
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from datetime import datetime
from decimal import Decimal

from usuarios.access_control import get_default_url_for_user

User = get_user_model()


class AkunLoginView(LoginView):
    template_name = 'core/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        auth_login(self.request, form.get_user())
        target_url = self.get_redirect_url() or get_default_url_for_user(self.request.user)
        if target_url:
            return HttpResponseRedirect(target_url)

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
    
    # Estadísticas comerciales
    total_ventas = Venta.objects.filter(deleted_at__isnull=True).aggregate(Sum('valor_total'))['valor_total__sum'] or Decimal('0')
    total_compras = Compra.objects.filter(deleted_at__isnull=True).aggregate(Sum('valor_total'))['valor_total__sum'] or Decimal('0')
    ventas_pendientes = Venta.objects.filter(deleted_at__isnull=True, estado='pendiente').count()
    clientes_count = Cliente.objects.filter(deleted_at__isnull=True).count()
    
    context = {
        'total_ventas': total_ventas,
        'total_compras': total_compras,
        'ventas_pendientes': ventas_pendientes,
        'clientes_count': clientes_count,
    }
    
    return render(request, 'core/home.html', context)