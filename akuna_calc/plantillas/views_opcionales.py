from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Max
from .models import OpcionalFabrica, FormulaOpcional
from .forms import OpcionalFabricaForm


@login_required
def opcional_list(request):
    opcionales = OpcionalFabrica.objects.all().order_by('codigo')
    return render(request, 'plantillas/opcional_list.html', {'opcionales': opcionales})


@login_required
def opcional_create(request):
    if request.method == 'POST':
        form = OpcionalFabricaForm(request.POST)
        if form.is_valid():
            opcional = form.save()
            messages.success(request, f'Opcional {opcional.codigo} creado correctamente.')
            return redirect('plantillas:opcional_edit', pk=opcional.pk)
    else:
        form = OpcionalFabricaForm()
    
    return render(request, 'plantillas/opcional_form.html', {
        'form': form,
        'titulo': 'Crear Opcional'
    })


@login_required
def opcional_edit(request, pk):
    from productos.models import Producto as ProductoSimple
    from pricing.models import Perfil, Hoja, Vidrio, Extrusora, Linea, Producto
    from .models import RelacionProductoOpcional
    
    opcional = get_object_or_404(OpcionalFabrica, pk=pk)
    formulas = FormulaOpcional.objects.filter(opcional=opcional).order_by('orden')
    relaciones = RelacionProductoOpcional.objects.filter(opcional=opcional).order_by('orden')
    
    # Obtener datos para los selectores
    perfiles = Perfil.objects.filter(bloqueado__isnull=True).order_by('codigo')[:200]
    hojas = Hoja.objects.filter(bloqueado__isnull=True).order_by('descripcion')[:200]
    vidrios = Vidrio.objects.filter(bloqueado__isnull=True).order_by('codigo')[:200]
    extrusoras = Extrusora.objects.filter(bloqueado__isnull=True).order_by('nombre')
    lineas = Linea.objects.filter(bloqueado__isnull=True).order_by('nombre')
    productos = Producto.objects.filter(bloqueado__isnull=True).order_by('descripcion')[:200]
    
    if request.method == 'POST':
        form = OpcionalFabricaForm(request.POST, instance=opcional)
        if form.is_valid():
            form.save()
            messages.success(request, f'Opcional {opcional.codigo} actualizado correctamente.')
            return redirect('plantillas:opcional_list')
    else:
        form = OpcionalFabricaForm(instance=opcional)
    
    return render(request, 'plantillas/opcional_form.html', {
        'form': form,
        'titulo': 'Editar Opcional',
        'opcional': opcional,
        'formulas': formulas,
        'relaciones': relaciones,
        'perfiles': perfiles,
        'hojas': hojas,
        'vidrios': vidrios,
        'extrusoras': extrusoras,
        'lineas': lineas,
        'productos': productos
    })


@login_required
def opcional_toggle(request, pk):
    opcional = get_object_or_404(OpcionalFabrica, pk=pk)
    opcional.activo = not opcional.activo
    opcional.save()
    estado = 'activado' if opcional.activo else 'desactivado'
    messages.success(request, f'Opcional {opcional.codigo} {estado}.')
    return redirect('plantillas:opcional_list')


@login_required
def opcional_formulas_guardar(request, pk):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    opcional = get_object_or_404(OpcionalFabrica, pk=pk)
    
    try:
        FormulaOpcional.objects.filter(opcional=opcional).delete()
        
        index = 0
        guardadas = 0
        while f'cantidad_{index}' in request.POST:
            cantidad = request.POST.get(f'cantidad_{index}', '').strip()
            formula = request.POST.get(f'formula_{index}', '').strip()
            angulo = request.POST.get(f'angulo_{index}', '').strip()
            tipo_relacionador = request.POST.get(f'tipo_relacionador_{index}', 'perfil').strip()
            perfil = request.POST.get(f'perfil_{index}', '').strip()
            
            if cantidad and formula:
                FormulaOpcional.objects.create(
                    opcional=opcional,
                    cantidad=cantidad,
                    formula=formula,
                    angulo=angulo,
                    tipo_relacionador=tipo_relacionador,
                    perfil=perfil,
                    precio=0,  # El precio se toma del producto/perfil
                    orden=index
                )
                guardadas += 1
            
            index += 1
        
        return JsonResponse({'ok': True, 'guardadas': guardadas})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def opcional_relaciones_guardar(request, pk):
    from .models import RelacionProductoOpcional
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    opcional = get_object_or_404(OpcionalFabrica, pk=pk)
    
    try:
        RelacionProductoOpcional.objects.filter(opcional=opcional).delete()
        
        index = 0
        guardadas = 0
        while f'extrusora_{index}' in request.POST:
            extrusora_id = request.POST.get(f'extrusora_{index}', '').strip()
            linea_id = request.POST.get(f'linea_{index}', '').strip()
            producto_id = request.POST.get(f'producto_{index}', '').strip()
            cantidad = request.POST.get(f'cantidad_{index}', '1').strip()
            
            if extrusora_id and linea_id and producto_id:
                RelacionProductoOpcional.objects.create(
                    opcional=opcional,
                    extrusora_id=int(extrusora_id),
                    linea_id=int(linea_id),
                    producto_id=int(producto_id),
                    cantidad=int(cantidad) if cantidad else 1,
                    orden=index
                )
                guardadas += 1
            
            index += 1
        
        return JsonResponse({'ok': True, 'guardadas': guardadas})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
