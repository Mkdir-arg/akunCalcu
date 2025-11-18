from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from productos.models import Producto, Cotizacion
from django.contrib.auth import get_user_model
from django.db.models import Sum
from datetime import datetime

User = get_user_model()

def index(request):
    if request.user.is_authenticated:
        return redirect('home')
    return redirect('login')

@login_required
def home(request):
    # Estadísticas para el dashboard
    productos_count = Producto.objects.filter(activo=True).count()
    cotizaciones_count = Cotizacion.objects.count()
    
    # Total del mes actual
    current_month = datetime.now().month
    current_year = datetime.now().year
    total_mes = Cotizacion.objects.filter(
        fecha__month=current_month,
        fecha__year=current_year
    ).aggregate(total=Sum('total_general'))['total'] or 0
    
    # Promedio de cotizaciones
    promedio = Cotizacion.objects.aggregate(
        promedio=Sum('total_general')
    )['promedio'] or 0
    if cotizaciones_count > 0:
        promedio = promedio / cotizaciones_count
    
    context = {
        'productos_count': productos_count,
        'cotizaciones_count': cotizaciones_count,
        'total_mes': int(total_mes),
        'promedio': int(promedio),
    }
    
    return render(request, 'core/home.html', context)