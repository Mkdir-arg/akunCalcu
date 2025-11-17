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
    cotizaciones = Cotizacion.objects.all()
    return render(request, 'productos/cotizacion_list.html', {'cotizaciones': cotizaciones})

@login_required
def cotizacion_detail(request, pk):
    cotizacion = get_object_or_404(Cotizacion, pk=pk)
    return render(request, 'productos/cotizacion_detail.html', {'cotizacion': cotizacion})