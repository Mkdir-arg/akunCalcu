from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from decimal import Decimal
from .models import Producto, Cotizacion, CotizacionItem
from .forms import ProductoForm

@login_required
def productos_list(request):
    productos = Producto.objects.filter(activo=True)
    return render(request, 'productos/productos_list.html', {'productos': productos})

@login_required
def producto_create(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto creado exitosamente.')
            return redirect('productos:productos_list')
    else:
        form = ProductoForm()
    return render(request, 'productos/producto_form.html', {'form': form, 'title': 'Nuevo Producto'})

@login_required
def producto_update(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto actualizado exitosamente.')
            return redirect('productos:productos_list')
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'productos/producto_form.html', {'form': form, 'title': 'Editar Producto'})

@login_required
def producto_toggle_active(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    producto.activo = not producto.activo
    producto.save()
    status = 'activado' if producto.activo else 'desactivado'
    messages.success(request, f'Producto {status} exitosamente.')
    return redirect('productos:productos_list')

@login_required
def calculadora_rapida(request):
    productos = Producto.objects.filter(activo=True)
    
    if request.method == 'POST':
        import json
        from comercial.models import Cliente
        
        try:
            data = json.loads(request.body)
            cliente_id = data.get('cliente_id')
            items = data.get('items', [])
            
            if not cliente_id:
                return JsonResponse({'success': False, 'error': 'Debe seleccionar un cliente'}, status=400)
            
            if not items:
                return JsonResponse({'success': False, 'error': 'Debe agregar al menos un producto'}, status=400)
            
            cliente = Cliente.objects.get(id=cliente_id)
            
            # Crear cotización
            cotizacion = Cotizacion.objects.create(
                usuario=request.user,
                cliente=cliente,
                total_general=Decimal('0.00')
            )
            
            total_general = Decimal('0.00')
            
            for item_data in items:
                producto = Producto.objects.get(id=item_data['producto_id'])
                alto = int(item_data['alto'])
                ancho = int(item_data['ancho'])
                cantidad = int(item_data.get('cantidad', 1))
                
                # Calcular área
                if producto.formula == 'perimetro':
                    area = Decimal(str((alto / 1000) * 2 + (ancho / 1000) * 2))
                else:
                    area = Decimal(str((alto / 1000) * (ancho / 1000)))
                
                subtotal = area * producto.precio_m2 * cantidad
                
                CotizacionItem.objects.create(
                    cotizacion=cotizacion,
                    producto=producto,
                    alto_mm=alto,
                    ancho_mm=ancho,
                    cantidad=cantidad,
                    area_m2=area,
                    subtotal=subtotal
                )
                
                total_general += subtotal
            
            cotizacion.total_general = total_general
            cotizacion.save()
            
            return JsonResponse({
                'success': True,
                'cotizacion_id': cotizacion.id,
                'redirect_url': f'/productos/cotizaciones/{cotizacion.id}/'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return render(request, 'productos/calculadora.html', {'productos': productos})

@login_required
def crear_cotizacion(request):
    productos = Producto.objects.filter(activo=True)
    
    if request.method == 'POST':
        # Crear nueva cotización
        cotizacion = Cotizacion.objects.create(
            usuario=request.user,
            total_general=Decimal('0.00')
        )
        
        total_general = Decimal('0.00')
        items_creados = 0
        
        # Procesar cada producto
        for producto in productos:
            alto_key = f'alto_{producto.id}'
            ancho_key = f'ancho_{producto.id}'
            
            alto_mm = request.POST.get(alto_key)
            ancho_mm = request.POST.get(ancho_key)
            
            if alto_mm and ancho_mm:
                try:
                    alto_mm = int(alto_mm)
                    ancho_mm = int(ancho_mm)
                    
                    if alto_mm > 0 and ancho_mm > 0:
                        # Calcular área en m²
                        area_m2 = Decimal(str(alto_mm / 1000)) * Decimal(str(ancho_mm / 1000))
                        subtotal = area_m2 * producto.precio_m2
                        
                        # Crear item de cotización
                        CotizacionItem.objects.create(
                            cotizacion=cotizacion,
                            producto=producto,
                            alto_mm=alto_mm,
                            ancho_mm=ancho_mm,
                            area_m2=area_m2,
                            subtotal=subtotal
                        )
                        
                        total_general += subtotal
                        items_creados += 1
                        
                except (ValueError, TypeError):
                    continue
        
        if items_creados > 0:
            cotizacion.total_general = total_general
            cotizacion.save()
            messages.success(request, f'Cotización creada con {items_creados} productos.')
            return redirect('productos:cotizacion_detail', pk=cotizacion.pk)
        else:
            cotizacion.delete()
            messages.error(request, 'No se ingresaron productos válidos.')
    
    return render(request, 'productos/cotizacion_form.html', {'productos': productos})

@login_required
def cotizacion_list(request):
    from django.db.models import Q, Sum, Count
    from datetime import datetime
    from decimal import Decimal
    
    cotizaciones = Cotizacion.objects.filter(deleted_at__isnull=True).select_related('usuario', 'cliente').all()
    
    # Filtros
    buscar = request.GET.get('q')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    if buscar:
        cotizaciones = cotizaciones.filter(
            Q(id__icontains=buscar) |
            Q(cliente__nombre__icontains=buscar) |
            Q(cliente__apellido__icontains=buscar)
        )
    
    if fecha_desde:
        cotizaciones = cotizaciones.filter(fecha__date__gte=fecha_desde)
    
    if fecha_hasta:
        cotizaciones = cotizaciones.filter(fecha__date__lte=fecha_hasta)
    
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
        'cotizaciones': cotizaciones,
        'buscar': buscar,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'total_cotizado_mes': total_cotizado_mes,
        'total_vendido_mes': total_vendido_mes,
        'promedio_cotizado': promedio_cotizado,
        'tasa_conversion': tasa_conversion,
    }
    return render(request, 'productos/cotizacion_list.html', context)

@login_required
def cotizacion_detail(request, pk):
    cotizacion = get_object_or_404(Cotizacion, pk=pk)
    return render(request, 'productos/cotizacion_detail.html', {'cotizacion': cotizacion})


@login_required
def cambiar_estado_cotizacion(request, pk):
    cotizacion = get_object_or_404(Cotizacion, pk=pk)
    nuevo_estado = request.POST.get('estado')
    
    if nuevo_estado in ['creado', 'vendido', 'desestimado']:
        cotizacion.estado = nuevo_estado
        cotizacion.save()
        messages.success(request, f'Estado cambiado a {cotizacion.get_estado_display()}')
    
    return redirect('productos:cotizacion_list')


@login_required
def cotizacion_delete(request, pk):
    cotizacion = get_object_or_404(Cotizacion, pk=pk)
    if request.method == 'POST':
        cotizacion.delete()  # Eliminado lógico
        messages.success(request, 'Cotización eliminada exitosamente.')
        return redirect('productos:cotizacion_list')
    return redirect('productos:cotizacion_list')