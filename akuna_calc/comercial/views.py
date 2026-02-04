from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.http import JsonResponse
from datetime import datetime
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
            venta = form.save()
            
            # Procesar percepciones
            from .models import Percepcion
            for key in request.POST:
                if key.startswith('percepcion_tipo_'):
                    id_percepcion = key.split('_')[-1]
                    tipo = request.POST.get(f'percepcion_tipo_{id_percepcion}')
                    observaciones = request.POST.get(f'percepcion_obs_{id_percepcion}', '')
                    importe = request.POST.get(f'percepcion_importe_{id_percepcion}')
                    
                    if tipo and importe:
                        try:
                            from decimal import Decimal
                            Percepcion.objects.create(
                                venta=venta,
                                tipo=tipo,
                                observaciones=observaciones,
                                importe=Decimal(importe)
                            )
                        except:
                            pass
            
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
            venta = form.save()
            
            # Eliminar percepciones existentes y crear nuevas
            from .models import Percepcion
            venta.percepciones.all().delete()
            
            for key in request.POST:
                if key.startswith('percepcion_tipo_'):
                    id_percepcion = key.split('_')[-1]
                    tipo = request.POST.get(f'percepcion_tipo_{id_percepcion}')
                    observaciones = request.POST.get(f'percepcion_obs_{id_percepcion}', '')
                    importe = request.POST.get(f'percepcion_importe_{id_percepcion}')
                    
                    if tipo and importe:
                        try:
                            from decimal import Decimal
                            Percepcion.objects.create(
                                venta=venta,
                                tipo=tipo,
                                observaciones=observaciones,
                                importe=Decimal(importe)
                            )
                        except:
                            pass
            
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
            from decimal import Decimal
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
            
            # Procesar retenciones
            from .models import Retencion
            for key in request.POST:
                if key.startswith('retencion_tipo_'):
                    id_retencion = key.split('_')[-1]
                    tipo = request.POST.get(f'retencion_tipo_{id_retencion}')
                    concepto = request.POST.get(f'retencion_concepto_{id_retencion}', '')
                    nro_comprob = request.POST.get(f'retencion_nro_comprob_{id_retencion}', '')
                    importe_isar = request.POST.get(f'retencion_isar_{id_retencion}', '0')
                    importe_retenido = request.POST.get(f'retencion_retenido_{id_retencion}')
                    fecha_comprob = request.POST.get(f'retencion_fecha_{id_retencion}', None)
                    
                    if tipo and importe_retenido:
                        try:
                            Retencion.objects.create(
                                pago=pago,
                                tipo=tipo,
                                concepto=concepto,
                                numero_comprobante=nro_comprob,
                                importe_isar=Decimal(importe_isar) if importe_isar else Decimal('0'),
                                importe_retenido=Decimal(importe_retenido),
                                fecha_comprobante=fecha_comprob if fecha_comprob else None
                            )
                        except:
                            pass
            
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
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import inch, cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    from decimal import Decimal
    from django.conf import settings
    import os
    
    venta = get_object_or_404(Venta.objects.select_related('cliente').prefetch_related('pagos__retenciones', 'percepciones'), pk=pk)
    pagos = venta.pagos.all().order_by('-fecha_pago')
    total_pagado = venta.sena + sum(p.monto for p in pagos)
    
    # Crear respuesta HTTP
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="factura_{venta.numero_pedido}.pdf"'
    
    # Crear PDF
    doc = SimpleDocTemplate(response, pagesize=A4, topMargin=1*cm, bottomMargin=1*cm, leftMargin=1.5*cm, rightMargin=1.5*cm)
    elements = []
    styles = getSampleStyleSheet()
    
    # Estilos personalizados
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Normal'],
        fontSize=32,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=6,
        alignment=TA_RIGHT,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#7f8c8d'),
        alignment=TA_RIGHT
    )
    
    # Header con logo y título
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'AKUN-LOGO.png')
    try:
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=3.5*cm, height=1.8*cm, kind='proportional')
            header_data = [[logo, Paragraph('FACTURA', title_style)]]
        else:
            raise FileNotFoundError
    except:
        header_data = [[
            Paragraph('<b><font size=16 color="#3498db">AKUN</font></b><br/><font size=8 color="#7f8c8d">ABERTURAS</font>', styles['Normal']),
            Paragraph('FACTURA', title_style)
        ]]
    
    header_table = Table(header_data, colWidths=[4*cm, 14*cm])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(header_table)
    
    # Número de factura
    elements.append(Spacer(1, 0.3*cm))
    numero_info = Paragraph(f'<font size=9 color="#7f8c8d">N. {venta.numero_pedido}<br/>Del {venta.created_at.strftime("%d/%m/%Y")}</font>', subtitle_style)
    elements.append(numero_info)
    
    elements.append(Spacer(1, 1*cm))
    
    # Información del Cliente y Venta
    cliente_info = Paragraph(f'''
        <font size=10><b>CLIENTE</b></font><br/>
        <font size=9>{venta.cliente.get_nombre_completo()}</font><br/>
        <font size=8 color="#7f8c8d">
        {f"CUIT: {venta.cliente.cuit}<br/>" if venta.cliente.cuit else ""}
        {f"DNI: {venta.cliente.dni}<br/>" if venta.cliente.dni else ""}
        Condición IVA: {venta.cliente.get_condicion_iva_display()}<br/>
        {venta.cliente.direccion}, {venta.cliente.localidad}<br/>
        {f"Tel: {venta.cliente.telefono}<br/>" if venta.cliente.telefono else ""}
        {f"Email: {venta.cliente.email}" if venta.cliente.email else ""}
        </font>
    ''', styles['Normal'])
    
    venta_info = Paragraph(f'''
        <font size=10><b>DATOS DE LA VENTA</b></font><br/>
        <font size=8 color="#7f8c8d">
        Estado: <b>{venta.get_estado_display()}</b><br/>
        Tipo: <b>{"Factura " + venta.tipo_factura if venta.tipo_factura else "Sin factura"}</b><br/>
        {f"N° Factura: {venta.numero_factura}<br/>" if venta.numero_factura else ""}
        Operación: <b>{"En Blanco" if venta.con_factura else "En Negro"}</b><br/>
        {f"Forma de Pago: {venta.get_forma_pago_display()}<br/>" if venta.forma_pago else ""}
        {f"Fecha de Pago: {venta.fecha_pago.strftime('%d/%m/%Y')}<br/>" if venta.fecha_pago else ""}
        </font>
    ''', styles['Normal'])
    
    info_table = Table([[cliente_info, venta_info]], colWidths=[9*cm, 9*cm])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(info_table)
    
    elements.append(Spacer(1, 0.5*cm))
    
    # Resumen Financiero
    resumen_data = [[
        Paragraph('<font size=9><b>CONCEPTO</b></font>', styles['Normal']),
        Paragraph('<font size=9><b>MONTO</b></font>', ParagraphStyle('Right', parent=styles['Normal'], alignment=TA_RIGHT))
    ]]
    
    resumen_data.append([
        Paragraph('<font size=9>Valor Total</font>', styles['Normal']),
        Paragraph(f'<font size=9>${venta.valor_total:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.') + '</font>', ParagraphStyle('Right', parent=styles['Normal'], alignment=TA_RIGHT))
    ])
    
    if venta.percepciones.exists():
        for percepcion in venta.percepciones.all():
            resumen_data.append([
                Paragraph(f'<font size=8 color="#3498db">+ Percepción {percepcion.get_tipo_display()}</font>', styles['Normal']),
                Paragraph(f'<font size=8 color="#3498db">${percepcion.importe:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.') + '</font>', ParagraphStyle('Right', parent=styles['Normal'], alignment=TA_RIGHT))
            ])
    
    if venta.tiene_retenciones:
        resumen_data.append([
            Paragraph(f'<font size=8 color="#e74c3c">- Retenciones del Cliente</font>', styles['Normal']),
            Paragraph(f'<font size=8 color="#e74c3c">-${venta.monto_retenciones:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.') + '</font>', ParagraphStyle('Right', parent=styles['Normal'], alignment=TA_RIGHT))
        ])
    
    resumen_data.append([
        Paragraph('<font size=9><b>Seña Pagada</b></font>', styles['Normal']),
        Paragraph(f'<font size=9 color="#27ae60"><b>${venta.sena:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.') + '</b></font>', ParagraphStyle('Right', parent=styles['Normal'], alignment=TA_RIGHT))
    ])
    
    resumen_data.append([
        Paragraph('<font size=9><b>Total Pagado</b></font>', styles['Normal']),
        Paragraph(f'<font size=9 color="#27ae60"><b>${total_pagado:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.') + '</b></font>', ParagraphStyle('Right', parent=styles['Normal'], alignment=TA_RIGHT))
    ])
    
    resumen_data.append([
        Paragraph('<font size=10><b>SALDO PENDIENTE</b></font>', styles['Normal']),
        Paragraph(f'<font size=11 color="{"#e74c3c" if venta.saldo > 0 else "#27ae60"}"><b>${venta.saldo:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.') + '</b></font>', ParagraphStyle('Right', parent=styles['Normal'], alignment=TA_RIGHT))
    ])
    
    resumen_table = Table(resumen_data, colWidths=[12*cm, 5.5*cm])
    resumen_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ecf0f1')),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#bdc3c7')),
        ('LINEABOVE', (0, -1), (-1, -1), 1.5, colors.HexColor('#2c3e50')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(resumen_table)
    
    elements.append(Spacer(1, 0.8*cm))
    
    # Tabla de items
    items_data = [['Cantidad', 'Descripción', 'Precio', 'IVA', 'Importe']]
    
    # Item principal
    items_data.append([
        '1,00',
        f'Pedido {venta.numero_pedido}',
        f'${venta.valor_total:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'),
        '21%',
        f'${venta.valor_total:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    ])
    
    # Agregar percepciones como items
    for percepcion in venta.percepciones.all():
        items_data.append([
            '1,00',
            f'Percepción {percepcion.get_tipo_display()}',
            f'${percepcion.importe:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'),
            '-',
            f'${percepcion.importe:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
        ])
    
    # Agregar filas vacías
    for _ in range(max(0, 8 - len(items_data))):
        items_data.append(['', '', '', '', ''])
    
    items_table = Table(items_data, colWidths=[2*cm, 8*cm, 2.5*cm, 2*cm, 3*cm])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#2c3e50')),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#2c3e50')),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#2c3e50')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ecf0f1')),
    ]))
    elements.append(items_table)
    
    elements.append(Spacer(1, 0.5*cm))
    
    # Historial de Pagos
    if pagos.exists() or venta.sena > 0:
        elements.append(Paragraph('<font size=11><b>Historial de Pagos</b></font>', styles['Normal']))
        elements.append(Spacer(1, 0.3*cm))
        
        pagos_data = [['Fecha', 'Monto', 'Forma de Pago', 'Observaciones']]
        
        # Seña inicial
        pagos_data.append([
            venta.created_at.strftime('%d/%m/%Y'),
            f"${venta.sena:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
            'Seña Inicial',
            'Pago inicial de la venta'
        ])
        
        # Pagos adicionales
        for pago in pagos:
            monto_str = f"${pago.monto:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            if pago.retenciones.exists():
                total_ret = pago.get_total_retenciones()
                neto = pago.get_monto_neto()
                monto_str += f"\nRet: ${total_ret:,.2f} → Neto: ${neto:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            
            obs = pago.observaciones or '-'
            if pago.retenciones.exists():
                obs += '\n' + ', '.join([f"{r.get_tipo_display()}: ${r.importe_retenido:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') for r in pago.retenciones.all()])
            
            pagos_data.append([
                pago.fecha_pago.strftime('%d/%m/%Y'),
                monto_str,
                pago.get_forma_pago_display(),
                obs
            ])
        
        pagos_table = Table(pagos_data, colWidths=[2.5*cm, 4*cm, 3*cm, 8*cm])
        pagos_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ecf0f1')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
        ]))
        elements.append(pagos_table)
        elements.append(Spacer(1, 0.5*cm))
    
    # Footer con dirección y totales
    total_con_percepciones = venta.get_total_con_percepciones()
    
    footer_data = [[
        Paragraph('<font size=8 color="#7f8c8d"><b>Dirección:</b><br/>Elpidio González 5326, C1408 Cdad. Autónoma<br/>de Buenos Aires, Argentina<br/><b>Teléfono:</b> +54 11 4228-6559</font>', styles['Normal']),
        Table([
            ['Imponible', f'${venta.valor_total:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')],
            ['IVA', 'xxxxx'],
            ['Total', f'${total_con_percepciones:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')]
        ], colWidths=[3*cm, 3*cm], style=TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, 1), 9),
            ('FONTSIZE', (0, 2), (-1, 2), 11),
            ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
    ]]
    
    footer_table = Table(footer_data, colWidths=[9*cm, 6*cm])
    footer_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(footer_table)
    
    elements.append(Spacer(1, 1*cm))
    
    # Pie de página
    elements.append(Paragraph('<font size=8 color="#7f8c8d">AKUN ABERTURAS</font>', ParagraphStyle('Footer', parent=styles['Normal'], alignment=TA_CENTER, fontSize=8, textColor=colors.HexColor('#7f8c8d'))))
    
    # Construir PDF
    doc.build(elements)
    return response


# CLIENTES
@login_required
def clientes_list(request):
    clientes = Cliente.objects.filter(deleted_at__isnull=True).all()
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
        cliente.delete()  # Eliminado lógico
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


@login_required
def cuenta_delete(request, pk):
    cuenta = get_object_or_404(Cuenta, pk=pk)
    if request.method == 'POST':
        cuenta.delete()  # Eliminado lógico
        messages.success(request, 'Cuenta eliminada exitosamente.')
        return redirect('comercial:cuentas_list')
    return redirect('comercial:cuentas_list')


# TIPOS DE CUENTA
@login_required
def tipos_cuenta_list(request):
    tipos = TipoCuenta.objects.filter(deleted_at__isnull=True).all()
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
        tipo.delete()
        messages.success(request, 'Tipo de cuenta eliminado exitosamente.')
        return redirect('comercial:tipos_cuenta_list')
    return redirect('comercial:tipos_cuenta_list')


# TIPOS DE GASTO
@login_required
def tipos_gasto_list(request):
    tipos = TipoGasto.objects.filter(deleted_at__isnull=True).select_related('tipo_cuenta').all()
    return render(request, 'comercial/tipos_gasto/list.html', {'tipos': tipos})


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
        tipo.delete()
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
    if request.method == 'POST':
        import json
        pago = get_object_or_404(PagoVenta, pk=pk)
        
        try:
            data = json.loads(request.body)
            monto = Decimal(data.get('monto'))
            fecha_pago = data.get('fecha_pago')
            forma_pago = data.get('forma_pago')
            numero_factura = data.get('numero_factura', '')
            observaciones = data.get('observaciones', '')
            
            if monto <= 0:
                return JsonResponse({'success': False, 'error': 'El monto debe ser mayor a 0'}, status=400)
            
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