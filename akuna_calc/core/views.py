from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from productos.models import Producto, Cotizacion
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
    # Estadísticas para el dashboard
    productos_count = Producto.objects.filter(activo=True).count()
    cotizaciones_count = Cotizacion.objects.count()
    
    # Indicadores del mes actual
    mes_actual = datetime.now().month
    anio_actual = datetime.now().year
    
    cotizaciones_mes = Cotizacion.objects.filter(
        fecha__month=mes_actual,
        fecha__year=anio_actual
    )
    
    total_cotizado_mes = cotizaciones_mes.aggregate(Sum('total_general'))['total_general__sum'] or Decimal('0')
    total_vendido_mes = cotizaciones_mes.filter(estado='vendido').aggregate(Sum('total_general'))['total_general__sum'] or Decimal('0')
    
    count_cotizaciones_mes = cotizaciones_mes.count()
    promedio_cotizado = total_cotizado_mes / count_cotizaciones_mes if count_cotizaciones_mes > 0 else Decimal('0')
    
    count_vendidas_mes = cotizaciones_mes.filter(estado='vendido').count()
    tasa_conversion = (count_vendidas_mes / count_cotizaciones_mes * 100) if count_cotizaciones_mes > 0 else 0
    
    context = {
        'productos_count': productos_count,
        'cotizaciones_count': cotizaciones_count,
        'total_cotizado_mes': total_cotizado_mes,
        'total_vendido_mes': total_vendido_mes,
        'promedio_cotizado': promedio_cotizado,
        'tasa_conversion': tasa_conversion,
    }
    
    return render(request, 'core/home.html', context)