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
    from productos.models import Producto
    opcional = get_object_or_404(OpcionalFabrica, pk=pk)
    formulas = FormulaOpcional.objects.filter(opcional=opcional).order_by('orden')
    perfiles = Producto.objects.filter(activo=True).order_by('nombre')
    
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
        'perfiles': perfiles
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
            perfil = request.POST.get(f'perfil_{index}', '').strip()
            precio = request.POST.get(f'precio_{index}', '0').strip()
            
            if cantidad and formula:
                try:
                    precio_decimal = float(precio) if precio else 0
                except ValueError:
                    precio_decimal = 0
                
                FormulaOpcional.objects.create(
                    opcional=opcional,
                    cantidad=cantidad,
                    formula=formula,
                    angulo=angulo,
                    perfil=perfil,
                    precio=precio_decimal,
                    orden=index
                )
                guardadas += 1
            
            index += 1
        
        return JsonResponse({'ok': True, 'guardadas': guardadas})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
