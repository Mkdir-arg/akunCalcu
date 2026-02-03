from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Sum
from datetime import datetime
from decimal import Decimal

User = get_user_model()

def index(request):
    if request.user.is_authenticated:
        return redirect('home')
    return redirect('login')

@login_required
def home(request):
    from comercial.models import Venta, Compra, Cliente
    
    # Estadísticas comerciales
    total_ventas = Venta.objects.filter(deleted_at__isnull=True).aggregate(Sum('valor_total'))['valor_total__sum'] or Decimal('0')
    total_compras = Compra.objects.filter(deleted_at__isnull=True).aggregate(Sum('importe_abonado'))['importe_abonado__sum'] or Decimal('0')
    ventas_pendientes = Venta.objects.filter(deleted_at__isnull=True, estado='pendiente').count()
    clientes_count = Cliente.objects.filter(deleted_at__isnull=True).count()
    
    context = {
        'total_ventas': total_ventas,
        'total_compras': total_compras,
        'ventas_pendientes': ventas_pendientes,
        'clientes_count': clientes_count,
    }
    
    return render(request, 'core/home.html', context)