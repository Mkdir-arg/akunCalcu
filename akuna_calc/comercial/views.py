from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.http import JsonResponse
from datetime import datetime
from decimal import Decimal
from .models import Cliente, Venta, Cuenta, Compra, TipoCuenta, TipoGasto, PagoVenta
from .forms import ClienteForm, VentaForm, CuentaForm, CompraForm, ReporteForm


@login_required
def dashboard_comercial(request):
    from datetime import datetime, timedelta
    from django.db.models.functions import TruncMonth
    import json
    from django.core.serializers.json import DjangoJSONEncoder
    
    # Estadísticas generales
    total_ventas = Venta.objects.filter(deleted_at__isnull=True).aggregate(Sum('valor_total'))['valor_total__sum'] or 0
    total_compras = Compra.objects.filter(deleted_at__isnull=True).aggregate(Sum('importe_abonado'))['importe_abonado__sum'] or 0
    ventas_pendientes = Venta.objects.filter(deleted_at__isnull=True, estado='pendiente').count()
    
    # Últimos 6 meses
    hace_6_meses = datetime.now() - timedelta(days=180)
    
    # Ventas por mes
    ventas_por_mes = Venta.objects.filter(deleted_at__isnull=True, created_at__gte=hace_6_meses).annotate(
        mes=TruncMonth('created_at')
    ).values('mes').annotate(
        total=Sum('valor_total')
    ).order_by('mes')
    
    # Compras por mes
    compras_por_mes = Compra.objects.filter(deleted_at__isnull=True, fecha_pago__gte=hace_6_meses).annotate(
        mes=TruncMonth('fecha_pago')
    ).values('mes').annotate(
        total=Sum('importe_abonado')
    ).order_by('mes')
    
    # Top 5 clientes
    top_clientes = Venta.objects.filter(deleted_at__isnull=True).values('cliente__nombre', 'cliente__apellido').annotate(
        total=Sum('valor_total')
    ).order_by('-total')[:5]
    
    # Compras por tipo de cuenta
    compras_por_tipo_raw = Compra.objects.filter(deleted_at__isnull=True).values('cuenta__tipo_cuenta__id', 'cuenta__tipo_cuenta__tipo').annotate(
        total=Sum('importe_abonado')
    ).order_by('-total')
    
    # Formatear datos para el gráfico
    compras_por_tipo = []
    for item in compras_por_tipo_raw:
        tipo_cuenta = TipoCuenta.objects.filter(id=item['cuenta__tipo_cuenta__id']).first()
        if tipo_cuenta:
            compras_por_tipo.append({
                'tipo': tipo_cuenta.get_tipo_display(),
                'total': float(item['total'])
            })
    
    context = {
        'total_ventas': total_ventas,
        'total_compras': total_compras,
        'ventas_pendientes': ventas_pendientes,
        'clientes_count': Cliente.objects.filter(deleted_at__isnull=True).count(),
        'ventas_por_mes': json.dumps(list(ventas_por_mes), cls=DjangoJSONEncoder),
        'compras_por_mes': json.dumps(list(compras_por_mes), cls=DjangoJSONEncoder),
        'top_clientes': list(top_clientes),
        'compras_por_tipo': json.dumps(compras_por_tipo),
    }
    return render(request, 'comercial/dashboard.html', context)


# VENTAS
@login_required
def ventas_list(request):
    from django.core.paginator import Paginator
    from django.db.models import Case, When, Value, IntegerField
    
    ventas = Venta.objects.filter(deleted_at__isnull=True).select_related('cliente').all()
    
    # Filtros
    estado = request.GET.get('estado', '')
    con_factura = request.GET.get('con_factura', '')
    buscar = request.GET.get('q', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    orden = request.GET.get('orden', '-created_at')
    
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
            Q(cliente__razon_social__icontains=buscar) |
            Q(numero_factura__icontains=buscar)
        )
    
    if fecha_desde:
        ventas = ventas.filter(created_at__date__gte=fecha_desde)
    
    if fecha_hasta:
        ventas = ventas.filter(created_at__date__lte=fecha_hasta)
    
    # Ordenamiento especial para numero_factura (manejar valores vacíos)
    if orden in ['numero_factura', '-numero_factura']:
        ventas = ventas.annotate(
            factura_order=Case(
                When(numero_factura='', then=Value(1)),
                default=Value(0),
                output_field=IntegerField()
            )
        )
        if orden == 'numero_factura':
            ventas = ventas.order_by('factura_order', 'numero_factura')
        else:
            ventas = ventas.order_by('factura_order', '-numero_factura')
    else:
        # Ordenamiento normal
        ventas = ventas.order_by(orden)
    
    # Paginación
    paginator = Paginator(ventas, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'ventas': page_obj,
        'page_obj': page_obj,
        'estados': Venta.ESTADO_CHOICES,
        'filtro_estado': estado,
        'filtro_factura': con_factura,
        'buscar': buscar,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'orden_actual': orden
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


@login_required
def venta_delete(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    if request.method == 'POST':
        venta.delete()  # Eliminado lógico
        messages.success(request, 'Venta eliminada exitosamente.')
        return redirect('comercial:ventas_list')
    return redirect('comercial:ventas_list')


@login_required
def venta_detail(request, pk):
    venta = get_object_or_404(Venta.objects.select_related('cliente').prefetch_related('pagos'), pk=pk)
    pagos = venta.pagos.all().order_by('-fecha_pago')
    
    context = {
        'venta': venta,
        'pagos': pagos,
        'total_pagado': venta.sena + sum(p.monto for p in pagos)
    }
    return render(request, 'comercial/ventas/detail.html', context)


@login_required
def registrar_pago(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    
    if request.method == 'POST':
        monto = request.POST.get('monto')
        fecha_pago = request.POST.get('fecha_pago')
        forma_pago = request.POST.get('forma_pago')
        numero_factura = request.POST.get('numero_factura', '')
        observaciones = request.POST.get('observaciones', '')
        
        try:
            monto_decimal = Decimal(monto)
            
            if monto_decimal <= 0:
                messages.error(request, 'El monto debe ser mayor a 0')
                return redirect('comercial:venta_detail', pk=pk)
            
            if monto_decimal > venta.saldo:
                messages.error(request, f'El monto no puede ser mayor al saldo pendiente (${venta.saldo})')
                return redirect('comercial:venta_detail', pk=pk)
            
            pago = PagoVenta.objects.create(
                venta=venta,
                monto=monto_decimal,
                fecha_pago=fecha_pago,
                forma_pago=forma_pago,
                numero_factura=numero_factura,
                observaciones=observaciones,
                created_by=request.user
            )
            
            # Recalcular saldo
            venta.save()
            
            messages.success(request, f'Pago de ${monto_decimal} registrado exitosamente')
            return redirect('comercial:venta_detail', pk=pk)
            
        except Exception as e:
            messages.error(request, f'Error al registrar el pago: {str(e)}')
            return redirect('comercial:venta_detail', pk=pk)
    
    return redirect('comercial:venta_detail', pk=pk)


@login_required
def generar_pdf_venta(request, pk):
    from django.http import HttpResponse
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    from reportlab.pdfgen import canvas
    
    venta = get_object_or_404(Venta.objects.select_related('cliente').prefetch_related('pagos'), pk=pk)
    pagos = venta.pagos.all().order_by('-fecha_pago')
    total_pagado = venta.sena + sum(p.monto for p in pagos)
    
    # Crear respuesta HTTP
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="venta_{venta.numero_pedido}.pdf"'
    
    # Crear PDF
    doc = SimpleDocTemplate(response, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    styles = getSampleStyleSheet()
    
    # Estilos personalizados
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#64748b'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=12,
        spaceBefore=20,
        fontName='Helvetica-Bold'
    )
    
    # Encabezado
    elements.append(Paragraph("AKUNA ABERTURAS", title_style))
    elements.append(Paragraph("Detalle de Venta", subtitle_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Información de la venta
    info_data = [
        ['Pedido N°:', venta.numero_pedido, 'Fecha:', venta.created_at.strftime('%d/%m/%Y')],
        ['Cliente:', f"{venta.cliente}", 'Estado:', venta.get_estado_display()],
    ]
    
    if venta.numero_factura:
        info_data.append(['Factura:', venta.get_numero_factura_display(), 'Tipo:', 'Blanco' if venta.con_factura else 'Negro'])
    
    info_table = Table(info_data, colWidths=[1.2*inch, 2.5*inch, 1*inch, 1.8*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#f1f5f9')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1e293b')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Resumen financiero
    elements.append(Paragraph("Resumen Financiero", heading_style))
    
    def format_currency(value):
        return f"${value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    resumen_data = [
        ['Concepto', 'Monto'],
        ['Valor Total', format_currency(venta.valor_total)],
        ['Seña Inicial', format_currency(venta.sena)],
        ['Pagos Adicionales', format_currency(sum(p.monto for p in pagos))],
        ['Total Pagado', format_currency(total_pagado)],
        ['Saldo Pendiente', format_currency(venta.saldo)],
    ]
    
    resumen_table = Table(resumen_data, colWidths=[4*inch, 2.5*inch])
    resumen_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#dbeafe')),
        ('BACKGROUND', (0, 4), (-1, 4), colors.HexColor('#dcfce7')),
        ('FONTNAME', (0, 4), (-1, 4), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 5), (-1, 5), colors.HexColor('#fef3c7') if venta.saldo > 0 else colors.HexColor('#dcfce7')),
        ('FONTNAME', (0, 5), (-1, 5), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 5), (-1, 5), 12),
    ]))
    elements.append(resumen_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Historial de pagos
    if pagos.exists() or venta.sena > 0:
        elements.append(Paragraph("Historial de Pagos", heading_style))
        
        pagos_data = [['Fecha', 'Concepto', 'Forma de Pago', 'N° Factura', 'Monto']]
        
        # Seña inicial
        pagos_data.append([
            venta.created_at.strftime('%d/%m/%Y'),
            'Seña Inicial',
            '-',
            venta.numero_factura or '-',
            format_currency(venta.sena)
        ])
        
        # Pagos adicionales
        for pago in pagos:
            pagos_data.append([
                pago.fecha_pago.strftime('%d/%m/%Y'),
                'Pago',
                pago.get_forma_pago_display(),
                pago.numero_factura or '-',
                format_currency(pago.monto)
            ])
        
        pagos_table = Table(pagos_data, colWidths=[1.1*inch, 1.5*inch, 1.3*inch, 1.3*inch, 1.3*inch])
        pagos_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (4, 0), (4, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ]))
        elements.append(pagos_table)
    
    # Pie de página
    elements.append(Spacer(1, 0.5*inch))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#64748b'),
        alignment=TA_CENTER
    )
    elements.append(Paragraph(f"Documento generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}", footer_style))
    elements.append(Paragraph("Akuna Aberturas - Sistema de Gestión", footer_style))
    
    # Construir PDF
    doc.build(elements)
    return response


# CLIENTES
@login_required
def clientes_list(request):
    clientes = Cliente.objects.filter(deleted_at__isnull=True).all()
    
    # Filtros
    buscar = request.GET.get('q', '')
    if buscar:
        clientes = clientes.filter(
            Q(nombre__icontains=buscar) | 
            Q(apellido__icontains=buscar) | 
            Q(razon_social__icontains=buscar) |
            Q(localidad__icontains=buscar)
        )
    
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


@login_required
def cliente_delete(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        # Contar ventas relacionadas
        ventas_relacionadas = Venta.objects.filter(cliente=cliente, deleted_at__isnull=True).count()
        
        # Eliminar el cliente (lógico)
        cliente.delete()
        
        if ventas_relacionadas > 0:
            messages.success(request, f'Cliente eliminado. Hay {ventas_relacionadas} ventas que usaban este cliente.')
        else:
            messages.success(request, 'Cliente eliminado exitosamente.')
        
        return redirect('comercial:clientes_list')
    return redirect('comercial:clientes_list')


# COMPRAS
@login_required
def compras_list(request):
    from django.core.paginator import Paginator
    
    compras = Compra.objects.filter(deleted_at__isnull=True).select_related('cuenta', 'cuenta__tipo_cuenta').all()
    
    # Filtros
    tipo_cuenta = request.GET.get('tipo_cuenta', '')
    con_factura = request.GET.get('con_factura', '')
    buscar = request.GET.get('q', '')
    
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
        'buscar': buscar,
        'titulo': 'Gastos'
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
            messages.success(request, 'Gasto registrado exitosamente.')
            return redirect('comercial:compras_list')
    else:
        form = CompraForm()
    
    # Pasar tipos de cuenta al contexto
    context = {
        'form': form,
        'title': 'Nuevo Gasto',
        'tipos_cuenta': TipoCuenta.objects.filter(activo=True, deleted_at__isnull=True)
    }
    return render(request, 'comercial/compras/form.html', context)


@login_required
def compra_edit(request, pk):
    compra = get_object_or_404(Compra, pk=pk)
    if request.method == 'POST':
        form = CompraForm(request.POST, instance=compra)
        if form.is_valid():
            form.save()
            messages.success(request, 'Gasto actualizado exitosamente.')
            return redirect('comercial:compras_list')
    else:
        form = CompraForm(instance=compra)
        # Pre-seleccionar el tipo de cuenta
        if compra.cuenta:
            form.fields['tipo_cuenta_filter'].initial = compra.cuenta.tipo_cuenta
    
    context = {
        'form': form,
        'title': 'Editar Gasto',
        'tipos_cuenta': TipoCuenta.objects.filter(activo=True, deleted_at__isnull=True),
        'compra': compra
    }
    return render(request, 'comercial/compras/form.html', context)


@login_required
def compra_delete(request, pk):
    compra = get_object_or_404(Compra, pk=pk)
    if request.method == 'POST':
        compra.delete()  # Eliminado lógico
        messages.success(request, 'Gasto eliminado exitosamente.')
        return redirect('comercial:compras_list')
    return redirect('comercial:compras_list')


# CUENTAS
@login_required
def cuentas_list(request):
    cuentas = Cuenta.objects.filter(deleted_at__isnull=True).select_related('tipo_cuenta').all()
    
    # Filtros
    buscar = request.GET.get('q', '')
    tipo_cuenta_id = request.GET.get('tipo_cuenta', '')
    estado = request.GET.get('estado', '')
    
    if buscar:
        cuentas = cuentas.filter(
            Q(nombre__icontains=buscar) | Q(razon_social__icontains=buscar)
        )
    
    if tipo_cuenta_id:
        cuentas = cuentas.filter(tipo_cuenta_id=tipo_cuenta_id)
    
    if estado == 'activo':
        cuentas = cuentas.filter(activo=True)
    elif estado == 'inactivo':
        cuentas = cuentas.filter(activo=False)
    
    tipos_cuenta_filtro = TipoCuenta.objects.filter(activo=True, deleted_at__isnull=True)
    
    return render(request, 'comercial/cuentas/list.html', {
        'cuentas': cuentas,
        'tipos_cuenta_filtro': tipos_cuenta_filtro
    })


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


@login_required
def cuenta_delete(request, pk):
    cuenta = get_object_or_404(Cuenta, pk=pk)
    if request.method == 'POST':
        # Contar compras relacionadas
        compras_relacionadas = Compra.objects.filter(cuenta=cuenta, deleted_at__isnull=True).count()
        
        # Eliminar la cuenta (lógico)
        cuenta.delete()
        
        if compras_relacionadas > 0:
            messages.success(request, f'Cuenta eliminada. Hay {compras_relacionadas} compras que usaban esta cuenta.')
        else:
            messages.success(request, 'Cuenta eliminada exitosamente.')
        
        return redirect('comercial:cuentas_list')
    return redirect('comercial:cuentas_list')


# TIPOS DE CUENTA
@login_required
def tipos_cuenta_list(request):
    tipos = TipoCuenta.objects.filter(deleted_at__isnull=True).all()
    
    # Filtros
    buscar = request.GET.get('q', '')
    estado = request.GET.get('estado', '')
    
    if buscar:
        tipos = tipos.filter(
            Q(descripcion__icontains=buscar) | Q(tipo__icontains=buscar)
        )
    
    if estado == 'activo':
        tipos = tipos.filter(activo=True)
    elif estado == 'inactivo':
        tipos = tipos.filter(activo=False)
    
    return render(request, 'comercial/tipos_cuenta/list.html', {'tipos': tipos})


@login_required
def tipo_cuenta_create(request):
    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        descripcion = request.POST.get('descripcion')
        activo = request.POST.get('activo') == 'on'
        
        if tipo and descripcion:
            # Verificar si existe un registro eliminado
            tipo_existente = TipoCuenta.objects.filter(tipo=tipo).first()
            if tipo_existente:
                # Reactivar el registro eliminado
                tipo_existente.descripcion = descripcion
                tipo_existente.activo = activo
                tipo_existente.deleted_at = None
                tipo_existente.save()
                messages.success(request, 'Tipo de cuenta reactivado exitosamente.')
            else:
                # Crear nuevo registro
                TipoCuenta.objects.create(
                    tipo=tipo,
                    descripcion=descripcion,
                    activo=activo
                )
                messages.success(request, 'Tipo de cuenta creado exitosamente.')
            return redirect('comercial:tipos_cuenta_list')
    
    return render(request, 'comercial/tipos_cuenta/form.html', {'title': 'Nuevo Tipo de Cuenta'})


@login_required
def tipo_cuenta_edit(request, pk):
    tipo = get_object_or_404(TipoCuenta, pk=pk)
    
    if request.method == 'POST':
        tipo.tipo = request.POST.get('tipo')
        tipo.descripcion = request.POST.get('descripcion')
        tipo.activo = request.POST.get('activo') == 'on'
        tipo.save()
        messages.success(request, 'Tipo de cuenta actualizado exitosamente.')
        return redirect('comercial:tipos_cuenta_list')
    
    return render(request, 'comercial/tipos_cuenta/form.html', {'tipo': tipo, 'title': 'Editar Tipo de Cuenta'})


@login_required
def tipo_cuenta_delete(request, pk):
    tipo = get_object_or_404(TipoCuenta, pk=pk)
    if request.method == 'POST':
        # Desactivar cuentas relacionadas
        cuentas_afectadas = Cuenta.objects.filter(tipo_cuenta=tipo, deleted_at__isnull=True)
        for cuenta in cuentas_afectadas:
            cuenta.delete()  # Eliminado lógico
        
        # Desactivar tipos de gasto relacionados
        tipos_gasto_afectados = TipoGasto.objects.filter(tipo_cuenta=tipo, deleted_at__isnull=True)
        for tipo_gasto in tipos_gasto_afectados:
            tipo_gasto.delete()  # Eliminado lógico
        
        # Eliminar el tipo de cuenta
        tipo.delete()
        messages.success(request, f'Tipo de cuenta eliminado. Se desactivaron {cuentas_afectadas.count()} cuentas y {tipos_gasto_afectados.count()} tipos de gasto.')
        return redirect('comercial:tipos_cuenta_list')
    return redirect('comercial:tipos_cuenta_list')


# TIPOS DE GASTO
@login_required
def tipos_gasto_list(request):
    tipos = TipoGasto.objects.filter(deleted_at__isnull=True).select_related('tipo_cuenta').all()
    
    # Filtros
    buscar = request.GET.get('q', '')
    tipo_cuenta_id = request.GET.get('tipo_cuenta', '')
    estado = request.GET.get('estado', '')
    
    if buscar:
        tipos = tipos.filter(
            Q(nombre__icontains=buscar) | Q(descripcion__icontains=buscar)
        )
    
    if tipo_cuenta_id:
        tipos = tipos.filter(tipo_cuenta_id=tipo_cuenta_id)
    
    if estado == 'activo':
        tipos = tipos.filter(activo=True)
    elif estado == 'inactivo':
        tipos = tipos.filter(activo=False)
    
    tipos_cuenta_filtro = TipoCuenta.objects.filter(activo=True, deleted_at__isnull=True)
    
    return render(request, 'comercial/tipos_gasto/list.html', {
        'tipos': tipos,
        'tipos_cuenta_filtro': tipos_cuenta_filtro
    })


@login_required
def tipo_gasto_create(request):
    if request.method == 'POST':
        tipo_cuenta_id = request.POST.get('tipo_cuenta')
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion', '')
        
        if tipo_cuenta_id and nombre:
            TipoGasto.objects.create(
                tipo_cuenta_id=tipo_cuenta_id,
                nombre=nombre,
                descripcion=descripcion
            )
            messages.success(request, 'Tipo de gasto creado exitosamente.')
            return redirect('comercial:tipos_gasto_list')
    
    tipos_cuenta = TipoCuenta.objects.filter(activo=True, deleted_at__isnull=True)
    return render(request, 'comercial/tipos_gasto/form.html', {'tipos_cuenta': tipos_cuenta, 'title': 'Nuevo Tipo de Gasto'})


@login_required
def tipo_gasto_edit(request, pk):
    tipo = get_object_or_404(TipoGasto, pk=pk)
    
    if request.method == 'POST':
        tipo_cuenta_id = request.POST.get('tipo_cuenta')
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion', '')
        
        if tipo_cuenta_id and nombre:
            tipo.tipo_cuenta_id = tipo_cuenta_id
            tipo.nombre = nombre
            tipo.descripcion = descripcion
            tipo.save()
            messages.success(request, 'Tipo de gasto actualizado exitosamente.')
            return redirect('comercial:tipos_gasto_list')
    
    tipos_cuenta = TipoCuenta.objects.filter(activo=True, deleted_at__isnull=True)
    return render(request, 'comercial/tipos_gasto/form.html', {'tipos_cuenta': tipos_cuenta, 'tipo': tipo, 'title': 'Editar Tipo de Gasto'})


@login_required
def tipo_gasto_delete(request, pk):
    tipo = get_object_or_404(TipoGasto, pk=pk)
    if request.method == 'POST':
        # Contar compras relacionadas
        compras_relacionadas = Compra.objects.filter(tipo_gasto=tipo, deleted_at__isnull=True).count()
        
        # Eliminar el tipo de gasto (lógico)
        tipo.delete()
        
        if compras_relacionadas > 0:
            messages.success(request, f'Tipo de gasto eliminado. Hay {compras_relacionadas} compras que usaban este tipo.')
        else:
            messages.success(request, 'Tipo de gasto eliminado exitosamente.')
        
        return redirect('comercial:tipos_gasto_list')
    return redirect('comercial:tipos_gasto_list')


# REPORTES
@login_required
def reportes(request):
    form = ReporteForm()
    reporte_data = None
    
    if request.method == 'POST':
        form = ReporteForm(request.POST)
        if form.is_valid():
            mes = form.cleaned_data.get('mes')
            anio = form.cleaned_data.get('anio')
            tipo_cuenta = form.cleaned_data.get('tipo_cuenta')
            cliente = form.cleaned_data.get('cliente')
            estado_venta = form.cleaned_data.get('estado_venta')
            monto_min = form.cleaned_data.get('monto_min')
            monto_max = form.cleaned_data.get('monto_max')
            
            # Filtrar compras
            compras_query = Compra.objects.filter(deleted_at__isnull=True)
            if mes:
                compras_query = compras_query.filter(fecha_pago__month__in=mes)
            if anio:
                compras_query = compras_query.filter(fecha_pago__year__in=anio)
            if tipo_cuenta:
                compras_query = compras_query.filter(cuenta__tipo_cuenta__in=tipo_cuenta)
            
            # Filtrar ventas
            ventas_query = Venta.objects.filter(deleted_at__isnull=True)
            if mes:
                ventas_query = ventas_query.filter(fecha_pago__month__in=mes)
            if anio:
                ventas_query = ventas_query.filter(fecha_pago__year__in=anio)
            if cliente:
                ventas_query = ventas_query.filter(cliente__in=cliente)
            if estado_venta:
                ventas_query = ventas_query.filter(estado__in=estado_venta)
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
                if tipo_cuenta and tipo not in tipo_cuenta:
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
                'mes': list(mes) if mes else None,
                'anio': list(anio) if anio else None,
                'tipo_cuenta_id': [tc.id for tc in tipo_cuenta] if tipo_cuenta else None,
                'cliente_id': [c.id for c in cliente] if cliente else None,
                'estado_venta': list(estado_venta) if estado_venta else None,
                'monto_min': str(monto_min) if monto_min else None,
                'monto_max': str(monto_max) if monto_max else None,
            }
    
    context = {
        'form': form,
        'reporte_data': reporte_data,
    }
    return render(request, 'comercial/reportes/reportes.html', context)


@login_required
def get_tipos_gasto_by_cuenta(request):
    cuenta_id = request.GET.get('cuenta_id')
    if cuenta_id:
        cuenta = Cuenta.objects.filter(id=cuenta_id).first()
        if cuenta:
            tipos_gasto = TipoGasto.objects.filter(
                tipo_cuenta=cuenta.tipo_cuenta,
                activo=True,
                deleted_at__isnull=True
            ).values('id', 'nombre')
            return JsonResponse(list(tipos_gasto), safe=False)
    return JsonResponse([], safe=False)


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
def editar_pago(request, pk):
    import json
    from datetime import datetime
    
    if request.method == 'POST':
        pago = get_object_or_404(PagoVenta, pk=pk)
        
        try:
            data = json.loads(request.body)
            monto = Decimal(str(data.get('monto')))
            fecha_pago_str = data.get('fecha_pago')
            forma_pago = data.get('forma_pago')
            numero_factura = data.get('numero_factura', '')
            observaciones = data.get('observaciones', '')
            
            if monto <= 0:
                return JsonResponse({'success': False, 'error': 'El monto debe ser mayor a 0'}, status=400)
            
            # Convertir fecha string a objeto date
            if isinstance(fecha_pago_str, str):
                fecha_pago = datetime.strptime(fecha_pago_str, '%Y-%m-%d').date()
            else:
                fecha_pago = fecha_pago_str
            
            pago.monto = monto
            pago.fecha_pago = fecha_pago
            pago.forma_pago = forma_pago
            pago.numero_factura = numero_factura
            pago.observaciones = observaciones
            pago.save()
            
            # Recalcular saldo de la venta
            pago.venta.save()
            
            return JsonResponse({
                'success': True,
                'pago': {
                    'id': pago.id,
                    'monto': float(pago.monto),
                    'fecha_pago': pago.fecha_pago.strftime('%d/%m/%Y'),
                    'forma_pago': pago.get_forma_pago_display(),
                    'numero_factura': pago.numero_factura or '-',
                    'observaciones': pago.observaciones or '-'
                },
                'saldo': float(pago.venta.saldo)
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)


@login_required
def exportar_reporte_excel(request):
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill
    from django.http import HttpResponse
    
    # Recuperar filtros de la sesión
    filtros = request.session.get('reporte_filtros', {})
    
    # Aplicar filtros
    mes = filtros.get('mes')
    anio = filtros.get('anio')
    tipo_cuenta_id = filtros.get('tipo_cuenta_id')
    cliente_id = filtros.get('cliente_id')
    estado_venta = filtros.get('estado_venta')
    monto_min = Decimal(str(filtros.get('monto_min'))) if filtros.get('monto_min') else None
    monto_max = Decimal(str(filtros.get('monto_max'))) if filtros.get('monto_max') else None
    
    # Filtrar ventas
    ventas_query = Venta.objects.filter(deleted_at__isnull=True)
    if mes:
        ventas_query = ventas_query.filter(fecha_pago__month__in=mes)
    if anio:
        ventas_query = ventas_query.filter(fecha_pago__year__in=anio)
    if cliente_id:
        ventas_query = ventas_query.filter(cliente_id__in=cliente_id)
    if estado_venta:
        ventas_query = ventas_query.filter(estado__in=estado_venta)
    if monto_min:
        ventas_query = ventas_query.filter(valor_total__gte=monto_min)
    if monto_max:
        ventas_query = ventas_query.filter(valor_total__lte=monto_max)
    
    # Filtrar compras
    compras_query = Compra.objects.filter(deleted_at__isnull=True)
    if mes:
        compras_query = compras_query.filter(fecha_pago__month__in=mes)
    if anio:
        compras_query = compras_query.filter(fecha_pago__year__in=anio)
    if tipo_cuenta_id:
        compras_query = compras_query.filter(cuenta__tipo_cuenta_id__in=tipo_cuenta_id)
    
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

