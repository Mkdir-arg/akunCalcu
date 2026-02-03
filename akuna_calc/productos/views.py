from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from decimal import Decimal
from .models import Producto
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