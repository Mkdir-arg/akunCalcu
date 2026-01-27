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
    from datetime import datetime, timedelta
    from django.db.models.functions import TruncMonth
    
    # Estadísticas generales
    total_ventas = Venta.objects.aggregate(Sum('valor_total'))['valor_total__sum'] or 0
    total_compras = Compra.objects.aggregate(Sum('importe_abonado'))['importe_abonado__sum'] or 0
    ventas_pendientes = Venta.objects.filter(estado='pendiente').count()
    
    # Últimos 6 meses
    hace_6_meses = datetime.now() - timedelta(days=180)
    
    # Ventas por mes
    ventas_por_mes = Venta.objects.filter(created_at__gte=hace_6_meses).annotate(
        mes=TruncMonth('created_at')
    ).values('mes').annotate(
        total=Sum('valor_total')
    ).order_by('mes')
    
    # Compras por mes
    compras_por_mes = Compra.objects.filter(fecha_pago__gte=hace_6_meses).annotate(
        mes=TruncMonth('fecha_pago')
    ).values('mes').annotate(
        total=Sum('importe_abonado')
    ).order_by('mes')
    
    # Top 5 clientes
    top_clientes = Venta.objects.values('cliente__nombre', 'cliente__apellido').annotate(
        total=Sum('valor_total')
    ).order_by('-total')[:5]
    
    # Compras por tipo
    compras_por_tipo = Compra.objects.values('cuenta__tipo_cuenta__tipo').annotate(
        total=Sum('importe_abonado')
    ).order_by('-total')
    
    context = {
        'total_ventas': total_ventas,
        'total_compras': total_compras,
        'ventas_pendientes': ventas_pendientes,
        'clientes_count': Cliente.objects.count(),
        'ventas_por_mes': list(ventas_por_mes),
        'compras_por_mes': list(compras_por_mes),
        'top_clientes': list(top_clientes),
        'compras_por_tipo': list(compras_por_tipo),
    }
    return render(request, 'comercial/dashboard.html', context)


# VENTAS
@login_required
def ventas_list(request):
    from django.core.paginator import Paginator
    
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
    
    # Paginación
    paginator = Paginator(ventas, 20)  # 20 items por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'ventas': page_obj,
        'page_obj': page_obj,
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
            cliente = form.save()
            
            # Si es AJAX (desde modal), devolver JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'cliente': {
                        'id': cliente.id,
                        'nombre': str(cliente)
                    }
                })
            
            messages.success(request, 'Cliente creado exitosamente.')
            return redirect('comercial:clientes_list')
        else:
            # Si es AJAX y hay errores
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                }, status=400)
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
    from django.core.paginator import Paginator
    
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
    
    # Paginación
    paginator = Paginator(compras, 20)  # 20 items por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'compras': page_obj,
        'page_obj': page_obj,
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
            cuenta = form.save()
            
            # Si es AJAX (desde modal), devolver JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'cuenta': {
                        'id': cuenta.id,
                        'nombre': str(cuenta)
                    }
                })
            
            messages.success(request, 'Cuenta creada exitosamente.')
            return redirect('comercial:cuentas_list')
        else:
            # Si es AJAX y hay errores
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                }, status=400)
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
            
            # Guardar en sesión para exportar
            request.session['reporte_filtros'] = {
                'mes': mes,
                'año': año,
                'tipo_cuenta_id': tipo_cuenta.id if tipo_cuenta else None,
                'cliente_id': cliente.id if cliente else None,
                'estado_venta': estado_venta,
                'monto_min': str(monto_min) if monto_min else None,
                'monto_max': str(monto_max) if monto_max else None,
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


@login_required
def get_clientes_list(request):
    clientes = Cliente.objects.all().values('id', 'nombre', 'apellido')
    return JsonResponse(list(clientes), safe=False)


@login_required
def exportar_reporte_excel(request):
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill
    from django.http import HttpResponse
    from decimal import Decimal
    
    # Recuperar filtros de la sesión
    filtros = request.session.get('reporte_filtros', {})
    
    # Aplicar filtros
    mes = filtros.get('mes')
    año = filtros.get('año')
    tipo_cuenta_id = filtros.get('tipo_cuenta_id')
    cliente_id = filtros.get('cliente_id')
    estado_venta = filtros.get('estado_venta')
    monto_min = Decimal(filtros.get('monto_min')) if filtros.get('monto_min') else None
    monto_max = Decimal(filtros.get('monto_max')) if filtros.get('monto_max') else None
    
    # Filtrar ventas
    ventas_query = Venta.objects.all()
    if mes:
        ventas_query = ventas_query.filter(fecha_pago__month=mes)
    if año:
        ventas_query = ventas_query.filter(fecha_pago__year=año)
    if cliente_id:
        ventas_query = ventas_query.filter(cliente_id=cliente_id)
    if estado_venta:
        ventas_query = ventas_query.filter(estado=estado_venta)
    if monto_min:
        ventas_query = ventas_query.filter(valor_total__gte=monto_min)
    if monto_max:
        ventas_query = ventas_query.filter(valor_total__lte=monto_max)
    
    # Filtrar compras
    compras_query = Compra.objects.all()
    if mes:
        compras_query = compras_query.filter(fecha_pago__month=mes)
    if año:
        compras_query = compras_query.filter(fecha_pago__year=año)
    if tipo_cuenta_id:
        compras_query = compras_query.filter(cuenta__tipo_cuenta_id=tipo_cuenta_id)
    
    # Crear workbook
    wb = Workbook()
    
    # Estilos
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=12)
    title_font = Font(bold=True, size=14)
    
    # Hoja Resumen
    ws_resumen = wb.active
    ws_resumen.title = "Resumen"
    
    ws_resumen['A1'] = 'REPORTE COMERCIAL'
    ws_resumen['A1'].font = title_font
    ws_resumen.merge_cells('A1:D1')
    
    row = 3
    ws_resumen[f'A{row}'] = 'VENTAS'
    ws_resumen[f'A{row}'].font = header_font
    ws_resumen[f'A{row}'].fill = header_fill
    
    ventas_blanco = ventas_query.filter(con_factura=True)
    ventas_negro = ventas_query.filter(con_factura=False)
    total_ventas_blanco = ventas_blanco.aggregate(Sum('valor_total'))['valor_total__sum'] or 0
    total_ventas_negro = ventas_negro.aggregate(Sum('valor_total'))['valor_total__sum'] or 0
    
    row += 1
    ws_resumen[f'A{row}'] = 'Ventas Blanco:'
    ws_resumen[f'B{row}'] = float(total_ventas_blanco)
    ws_resumen[f'B{row}'].number_format = '$#,##0.00'
    
    row += 1
    ws_resumen[f'A{row}'] = 'Ventas Negro:'
    ws_resumen[f'B{row}'] = float(total_ventas_negro)
    ws_resumen[f'B{row}'].number_format = '$#,##0.00'
    
    row += 1
    ws_resumen[f'A{row}'] = 'Total Ventas:'
    ws_resumen[f'A{row}'].font = Font(bold=True)
    ws_resumen[f'B{row}'] = float(total_ventas_blanco + total_ventas_negro)
    ws_resumen[f'B{row}'].number_format = '$#,##0.00'
    ws_resumen[f'B{row}'].font = Font(bold=True)
    
    row += 2
    ws_resumen[f'A{row}'] = 'COMPRAS'
    ws_resumen[f'A{row}'].font = header_font
    ws_resumen[f'A{row}'].fill = header_fill
    
    compras_blanco = compras_query.filter(con_factura=True)
    compras_negro = compras_query.filter(con_factura=False)
    total_compras_blanco = compras_blanco.aggregate(Sum('importe_abonado'))['importe_abonado__sum'] or 0
    total_compras_negro = compras_negro.aggregate(Sum('importe_abonado'))['importe_abonado__sum'] or 0
    
    row += 1
    ws_resumen[f'A{row}'] = 'Compras Blanco:'
    ws_resumen[f'B{row}'] = float(total_compras_blanco)
    ws_resumen[f'B{row}'].number_format = '$#,##0.00'
    
    row += 1
    ws_resumen[f'A{row}'] = 'Compras Negro:'
    ws_resumen[f'B{row}'] = float(total_compras_negro)
    ws_resumen[f'B{row}'].number_format = '$#,##0.00'
    
    row += 1
    ws_resumen[f'A{row}'] = 'Total Compras:'
    ws_resumen[f'A{row}'].font = Font(bold=True)
    ws_resumen[f'B{row}'] = float(total_compras_blanco + total_compras_negro)
    ws_resumen[f'B{row}'].number_format = '$#,##0.00'
    ws_resumen[f'B{row}'].font = Font(bold=True)
    
    row += 2
    ws_resumen[f'A{row}'] = 'BALANCE'
    ws_resumen[f'A{row}'].font = Font(bold=True, size=12)
    balance = (total_ventas_blanco + total_ventas_negro) - (total_compras_blanco + total_compras_negro)
    ws_resumen[f'B{row}'] = float(balance)
    ws_resumen[f'B{row}'].number_format = '$#,##0.00'
    ws_resumen[f'B{row}'].font = Font(bold=True, size=12)
    
    # Hoja Ventas
    ws_ventas = wb.create_sheet("Ventas")
    headers = ['Pedido', 'Cliente', 'Fecha', 'Total', 'Seña', 'Saldo', 'Estado', 'Tipo']
    for col, header in enumerate(headers, 1):
        cell = ws_ventas.cell(1, col, header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center')
    
    for row, venta in enumerate(ventas_query.select_related('cliente'), 2):
        ws_ventas.cell(row, 1, venta.numero_pedido)
        ws_ventas.cell(row, 2, str(venta.cliente))
        ws_ventas.cell(row, 3, venta.fecha_pago.strftime('%d/%m/%Y') if venta.fecha_pago else '-')
        ws_ventas.cell(row, 4, float(venta.valor_total)).number_format = '$#,##0.00'
        ws_ventas.cell(row, 5, float(venta.sena)).number_format = '$#,##0.00'
        ws_ventas.cell(row, 6, float(venta.saldo)).number_format = '$#,##0.00'
        ws_ventas.cell(row, 7, venta.get_estado_display())
        ws_ventas.cell(row, 8, 'Blanco' if venta.con_factura else 'Negro')
    
    # Hoja Compras
    ws_compras = wb.create_sheet("Compras")
    headers = ['Pedido', 'Cuenta', 'Tipo', 'Fecha', 'Importe', 'Tipo Operación', 'Descripción']
    for col, header in enumerate(headers, 1):
        cell = ws_compras.cell(1, col, header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center')
    
    for row, compra in enumerate(compras_query.select_related('cuenta', 'cuenta__tipo_cuenta'), 2):
        ws_compras.cell(row, 1, compra.numero_pedido)
        ws_compras.cell(row, 2, compra.cuenta.nombre)
        ws_compras.cell(row, 3, compra.cuenta.tipo_cuenta.get_tipo_display())
        ws_compras.cell(row, 4, compra.fecha_pago.strftime('%d/%m/%Y'))
        ws_compras.cell(row, 5, float(compra.importe_abonado)).number_format = '$#,##0.00'
        ws_compras.cell(row, 6, 'Blanco' if compra.con_factura else 'Negro')
        ws_compras.cell(row, 7, compra.descripcion or '-')
    
    # Ajustar anchos
    for ws in [ws_resumen, ws_ventas, ws_compras]:
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            ws.column_dimensions[column_letter].width = min(max_length + 2, 50)
    
    # Respuesta HTTP
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=reporte_comercial.xlsx'
    wb.save(response)
    return response