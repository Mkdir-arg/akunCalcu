from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from datetime import datetime

from .models import Cuenta, Asiento, AsientoLinea
from .services.reportes import (
    generar_libro_diario,
    generar_libro_mayor,
    generar_balance_sumas_saldos,
    generar_estado_resultados,
    generar_balance_general
)


@login_required
def plan_cuentas(request):
    """Muestra el plan de cuentas"""
    cuentas = Cuenta.objects.filter(activa=True).order_by('codigo')
    
    context = {
        'cuentas': cuentas,
        'titulo': 'Plan de Cuentas'
    }
    return render(request, 'contabilidad/plan_cuentas.html', context)


@login_required
def libro_diario(request):
    """Muestra el Libro Diario"""
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    # Convertir strings a fechas
    if fecha_desde:
        fecha_desde = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
    if fecha_hasta:
        fecha_hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
    
    asientos = generar_libro_diario(fecha_desde, fecha_hasta)
    
    context = {
        'asientos': asientos,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'titulo': 'Libro Diario'
    }
    return render(request, 'contabilidad/libro_diario.html', context)


@login_required
def libro_mayor(request, cuenta_id):
    """Muestra el Mayor de una cuenta"""
    cuenta = get_object_or_404(Cuenta, id=cuenta_id)
    
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    if fecha_desde:
        fecha_desde = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
    if fecha_hasta:
        fecha_hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
    
    movimientos = generar_libro_mayor(cuenta, fecha_desde, fecha_hasta)
    
    context = {
        'cuenta': cuenta,
        'movimientos': movimientos,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'titulo': f'Mayor - {cuenta.codigo} {cuenta.nombre}'
    }
    return render(request, 'contabilidad/libro_mayor.html', context)


@login_required
def balance_sumas_saldos(request):
    """Muestra Balance de Sumas y Saldos"""
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    if fecha_desde:
        fecha_desde = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
    if fecha_hasta:
        fecha_hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
    
    balance = generar_balance_sumas_saldos(fecha_desde, fecha_hasta)
    
    context = {
        'balance': balance,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'titulo': 'Balance de Sumas y Saldos'
    }
    return render(request, 'contabilidad/balance_sumas_saldos.html', context)


@login_required
def estado_resultados(request):
    """Muestra Estado de Resultados (PyG)"""
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    if not fecha_desde or not fecha_hasta:
        # Default: mes actual
        hoy = datetime.now().date()
        fecha_desde = hoy.replace(day=1)
        fecha_hasta = hoy
    else:
        fecha_desde = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
        fecha_hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
    
    resultado = generar_estado_resultados(fecha_desde, fecha_hasta)
    
    context = {
        'resultado': resultado,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'titulo': 'Estado de Resultados'
    }
    return render(request, 'contabilidad/estado_resultados.html', context)


@login_required
def balance_general(request):
    """Muestra Balance General"""
    fecha = request.GET.get('fecha')
    
    if not fecha:
        fecha = datetime.now().date()
    else:
        fecha = datetime.strptime(fecha, '%Y-%m-%d').date()
    
    balance = generar_balance_general(fecha)
    
    context = {
        'balance': balance,
        'fecha': fecha,
        'titulo': 'Balance General'
    }
    return render(request, 'contabilidad/balance_general.html', context)


@login_required
def crear_asiento(request):
    """Crea un asiento manual"""
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Obtener datos del formulario
                fecha = datetime.strptime(request.POST.get('fecha'), '%Y-%m-%d').date()
                descripcion = request.POST.get('descripcion')
                
                # Obtener siguiente número
                ultimo = Asiento.objects.filter(fecha=fecha).order_by('-numero').first()
                numero = (ultimo.numero + 1) if ultimo else 1
                
                # Crear asiento
                asiento = Asiento.objects.create(
                    numero=numero,
                    fecha=fecha,
                    tipo='MAN',
                    descripcion=descripcion,
                    created_by=request.user
                )
                
                # Crear líneas (simplificado - en producción usar formset)
                # Por ahora redirigir al admin para completar
                messages.success(request, f'Asiento {numero} creado. Complete las líneas en el admin.')
                return redirect('admin:contabilidad_asiento_change', asiento.id)
                
        except Exception as e:
            messages.error(request, f'Error al crear asiento: {str(e)}')
    
    context = {
        'titulo': 'Nuevo Asiento Manual'
    }
    return render(request, 'contabilidad/crear_asiento.html', context)
