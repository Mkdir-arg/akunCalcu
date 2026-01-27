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
    
    # Filtros
    estado = request.GET.get('estado')
    con_factura = request.GET.get('con_factura')
    buscar = request.GET.get('q')
    
    if estado:
        ventas = ventas.filter(estado=estado)
    
    if con_factura == 'si':
        ventas = ventas.filter(con_factura=True)
    elif con_factura == 'no':
        ventas = ventas.filter(con_factura=False)
    
    if buscar:
        ventas = ventas.filter(
            Q(numero_pedido__icontains=buscar) |
            Q(cliente__nombre__icontains=buscar) |
            Q(cliente__apellido__icontains=buscar) |
            Q(numero_factura__icontains=buscar)
        )
    
    # Ordenar por número de pedido
    ventas = ventas.order_by('numero_pedido', '-created_at')
    
    context = {
        'ventas': ventas,
        'estados': Venta.ESTADO_CHOICES,
        'filtro_estado': estado,
        'filtro_factura': con_factura,
        'buscar': buscar
    }
    return render(request, 'comercial/ventas/list.html', context)


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
    
    # Filtros
    tipo_cuenta = request.GET.get('tipo_cuenta')
    con_factura = request.GET.get('con_factura')
    buscar = request.GET.get('q')
    
    if tipo_cuenta:
        compras = compras.filter(cuenta__tipo_cuenta_id=tipo_cuenta)
    
    if con_factura == 'si':
        compras = compras.filter(con_factura=True)
    elif con_factura == 'no':
        compras = compras.filter(con_factura=False)
    
    if buscar:
        compras = compras.filter(
            Q(numero_pedido__icontains=buscar) |
            Q(cuenta__nombre__icontains=buscar) |
            Q(numero_factura__icontains=buscar)
        )
    
    # Ordenar por fecha de pago descendente
    compras = compras.order_by('-fecha_pago')
    
    context = {
        'compras': compras,
        'tipos_cuenta': TipoCuenta.objects.filter(activo=True),
        'filtro_tipo': tipo_cuenta,
        'filtro_factura': con_factura,
        'buscar': buscar
    }
    return render(request, 'comercial/compras/list.html', context)


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
            mes = form.cleaned_data.get('mes')
            año = form.cleaned_data.get('año')
            tipo_cuenta = form.cleaned_data.get('tipo_cuenta')
            cliente = form.cleaned_data.get('cliente')
            estado_venta = form.cleaned_data.get('estado_venta')
            monto_min = form.cleaned_data.get('monto_min')
            monto_max = form.cleaned_data.get('monto_max')
            
            # Filtrar compras
            compras_query = Compra.objects.all()
            if mes:
                compras_query = compras_query.filter(fecha_pago__month=mes)
            if año:
                compras_query = compras_query.filter(fecha_pago__year=año)
            if tipo_cuenta:
                compras_query = compras_query.filter(cuenta__tipo_cuenta=tipo_cuenta)
            
            # Filtrar ventas
            ventas_query = Venta.objects.all()
            if mes:
                ventas_query = ventas_query.filter(fecha_pago__month=mes)
            if año:
                ventas_query = ventas_query.filter(fecha_pago__year=año)
            if cliente:
                ventas_query = ventas_query.filter(cliente=cliente)
            if estado_venta:
                ventas_query = ventas_query.filter(estado=estado_venta)
            if monto_min:
                ventas_query = ventas_query.filter(valor_total__gte=monto_min)
            if monto_max:
                ventas_query = ventas_query.filter(valor_total__lte=monto_max)
            
            # Estadísticas de ventas (separadas por blanco/negro)
            ventas_blanco = ventas_query.filter(con_factura=True)
            ventas_negro = ventas_query.filter(con_factura=False)
            
            total_ventas_blanco = ventas_blanco.aggregate(Sum('valor_total'))['valor_total__sum'] or 0
            total_ventas_negro = ventas_negro.aggregate(Sum('valor_total'))['valor_total__sum'] or 0
            total_ventas = total_ventas_blanco + total_ventas_negro
            
            saldo_blanco = ventas_blanco.aggregate(Sum('saldo'))['saldo__sum'] or 0
            saldo_negro = ventas_negro.aggregate(Sum('saldo'))['saldo__sum'] or 0
            total_saldo = saldo_blanco + saldo_negro
            
            # Agrupar compras por tipo de cuenta (separadas por blanco/negro)
            compras_por_tipo = {}
            total_compras_blanco = 0
            total_compras_negro = 0
            
            for tipo in TipoCuenta.objects.filter(activo=True):
                if tipo_cuenta and tipo != tipo_cuenta:
                    continue
                    
                compras_tipo = compras_query.filter(cuenta__tipo_cuenta=tipo)
                compras_blanco = compras_tipo.filter(con_factura=True)
                compras_negro_tipo = compras_tipo.filter(con_factura=False)
                
                total_blanco = compras_blanco.aggregate(Sum('importe_abonado'))['importe_abonado__sum'] or 0
                total_negro_tipo = compras_negro_tipo.aggregate(Sum('importe_abonado'))['importe_abonado__sum'] or 0
                
                compras_por_tipo[tipo.get_tipo_display()] = {
                    'total_blanco': total_blanco,
                    'total_negro': total_negro_tipo,
                    'total': total_blanco + total_negro_tipo,
                    'compras_blanco': compras_blanco.select_related('cuenta'),
                    'compras_negro': compras_negro_tipo.select_related('cuenta')
                }
                total_compras_blanco += total_blanco
                total_compras_negro += total_negro_tipo
            
            total_compras = total_compras_blanco + total_compras_negro
            
            reporte_data = {
                'ventas': {
                    'total_blanco': total_ventas_blanco,
                    'total_negro': total_ventas_negro,
                    'total': total_ventas,
                    'saldo_blanco': saldo_blanco,
                    'saldo_negro': saldo_negro,
                    'saldo': total_saldo,
                    'cantidad_blanco': ventas_blanco.count(),
                    'cantidad_negro': ventas_negro.count(),
                    'cantidad': ventas_query.count(),
                    'lista_blanco': ventas_blanco.select_related('cliente')[:25],
                    'lista_negro': ventas_negro.select_related('cliente')[:25]
                },
                'compras': compras_por_tipo,
                'total_compras_blanco': total_compras_blanco,
                'total_compras_negro': total_compras_negro,
                'total_compras': total_compras,
                'balance_blanco': total_ventas_blanco - total_compras_blanco,
                'balance_negro': total_ventas_negro - total_compras_negro,
                'balance': total_ventas - total_compras,
            }
    
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