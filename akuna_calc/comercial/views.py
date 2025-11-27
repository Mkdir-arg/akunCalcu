from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.http import JsonResponse
from datetime import datetime
from .models import Cliente, Venta, Cuenta, Compra, TipoCuenta
from .forms import ClienteForm, VentaForm, CuentaForm, CompraForm, ReporteForm


@login_required
def dashboard_comercial(request):
    # Estadísticas generales
    total_ventas = Venta.objects.aggregate(Sum('valor_total'))['valor_total__sum'] or 0
    total_compras = Compra.objects.aggregate(Sum('importe_abonado'))['importe_abonado__sum'] or 0
    ventas_pendientes = Venta.objects.filter(estado='pendiente').count()
    
    context = {
        'total_ventas': total_ventas,
        'total_compras': total_compras,
        'ventas_pendientes': ventas_pendientes,
        'clientes_count': Cliente.objects.count(),
    }
    return render(request, 'comercial/dashboard.html', context)


# VENTAS
@login_required
def ventas_list(request):
    ventas = Venta.objects.select_related('cliente').all()
    return render(request, 'comercial/ventas/list.html', {'ventas': ventas})


@login_required
def venta_create(request):
    if request.method == 'POST':
        form = VentaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Venta creada exitosamente.')
            return redirect('comercial:ventas_list')
    else:
        form = VentaForm()
    return render(request, 'comercial/ventas/form.html', {'form': form, 'title': 'Nueva Venta'})


@login_required
def venta_edit(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    if request.method == 'POST':
        form = VentaForm(request.POST, instance=venta)
        if form.is_valid():
            form.save()
            messages.success(request, 'Venta actualizada exitosamente.')
            return redirect('comercial:ventas_list')
    else:
        form = VentaForm(instance=venta)
    return render(request, 'comercial/ventas/form.html', {'form': form, 'title': 'Editar Venta'})


# CLIENTES
@login_required
def clientes_list(request):
    clientes = Cliente.objects.all()
    return render(request, 'comercial/clientes/list.html', {'clientes': clientes})


@login_required
def cliente_create(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente creado exitosamente.')
            return redirect('comercial:clientes_list')
    else:
        form = ClienteForm()
    return render(request, 'comercial/clientes/form.html', {'form': form, 'title': 'Nuevo Cliente'})


@login_required
def cliente_edit(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente actualizado exitosamente.')
            return redirect('comercial:clientes_list')
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'comercial/clientes/form.html', {'form': form, 'title': 'Editar Cliente'})


# COMPRAS
@login_required
def compras_list(request):
    compras = Compra.objects.select_related('cuenta', 'cuenta__tipo_cuenta').all()
    return render(request, 'comercial/compras/list.html', {'compras': compras})


@login_required
def compra_create(request):
    if request.method == 'POST':
        form = CompraForm(request.POST)
        if form.is_valid():
            compra = form.save(commit=False)
            compra.created_by = request.user
            compra.save()
            messages.success(request, 'Compra registrada exitosamente.')
            return redirect('comercial:compras_list')
    else:
        form = CompraForm()
    return render(request, 'comercial/compras/form.html', {'form': form, 'title': 'Nueva Compra'})


@login_required
def compra_edit(request, pk):
    compra = get_object_or_404(Compra, pk=pk)
    if request.method == 'POST':
        form = CompraForm(request.POST, instance=compra)
        if form.is_valid():
            form.save()
            messages.success(request, 'Compra actualizada exitosamente.')
            return redirect('comercial:compras_list')
    else:
        form = CompraForm(instance=compra)
    return render(request, 'comercial/compras/form.html', {'form': form, 'title': 'Editar Compra'})


# CUENTAS
@login_required
def cuentas_list(request):
    cuentas = Cuenta.objects.select_related('tipo_cuenta').all()
    return render(request, 'comercial/cuentas/list.html', {'cuentas': cuentas})


@login_required
def cuenta_create(request):
    if request.method == 'POST':
        form = CuentaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cuenta creada exitosamente.')
            return redirect('comercial:cuentas_list')
    else:
        form = CuentaForm()
    return render(request, 'comercial/cuentas/form.html', {'form': form, 'title': 'Nueva Cuenta'})


@login_required
def cuenta_edit(request, pk):
    cuenta = get_object_or_404(Cuenta, pk=pk)
    if request.method == 'POST':
        form = CuentaForm(request.POST, instance=cuenta)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cuenta actualizada exitosamente.')
            return redirect('comercial:cuentas_list')
    else:
        form = CuentaForm(instance=cuenta)
    return render(request, 'comercial/cuentas/form.html', {'form': form, 'title': 'Editar Cuenta'})


# REPORTES
@login_required
def reportes(request):
    form = ReporteForm()
    reporte_data = None
    
    if request.method == 'POST':
        form = ReporteForm(request.POST)
        if form.is_valid():
            mes = form.cleaned_data['mes']
            año = form.cleaned_data['año']
            tipo_cuenta = form.cleaned_data['tipo_cuenta']
            
            # Filtrar compras por mes y año
            compras_query = Compra.objects.filter(
                fecha_pago__month=mes,
                fecha_pago__year=año
            )
            
            if tipo_cuenta:
                compras_query = compras_query.filter(cuenta__tipo_cuenta=tipo_cuenta)
            
            # Agrupar por tipo de cuenta
            reporte_data = {}
            total_general = 0
            
            for tipo in TipoCuenta.objects.filter(activo=True):
                if tipo_cuenta and tipo != tipo_cuenta:
                    continue
                    
                compras_tipo = compras_query.filter(cuenta__tipo_cuenta=tipo)
                total_tipo = compras_tipo.aggregate(Sum('importe_abonado'))['importe_abonado__sum'] or 0
                
                reporte_data[tipo.get_tipo_display()] = {
                    'total': total_tipo,
                    'compras': compras_tipo.select_related('cuenta')
                }
                total_general += total_tipo
            
            reporte_data['total_general'] = total_general
    
    context = {
        'form': form,
        'reporte_data': reporte_data,
    }
    return render(request, 'comercial/reportes/reportes.html', context)


@login_required
def get_cuentas_by_tipo(request):
    tipo_id = request.GET.get('tipo_id')
    cuentas = Cuenta.objects.filter(tipo_cuenta_id=tipo_id, activo=True).values('id', 'nombre')
    return JsonResponse(list(cuentas), safe=False)