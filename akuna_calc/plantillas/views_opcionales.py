from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Count, Max
from .models import OpcionalFabrica, FormulaOpcional
from .forms import OpcionalFabricaForm


@login_required
def opcional_list(request):
    allowed_sort_fields = {
        'codigo': ('codigo', 'id'),
        'nombre': ('nombre', 'id'),
        'descripcion': ('descripcion', 'codigo', 'id'),
        'formulas': ('formulas_count', 'codigo', 'id'),
    }
    sort = request.GET.get('sort', 'codigo')
    if sort not in allowed_sort_fields:
        sort = 'codigo'

    direction = 'desc' if request.GET.get('dir') == 'desc' else 'asc'
    ordering = [
        f'-{field}' if direction == 'desc' else field
        for field in allowed_sort_fields[sort]
    ]

    opcionales = (
        OpcionalFabrica.objects
        .filter(activo=True)
        .annotate(formulas_count=Count('formulas'))
        .order_by(*ordering)
    )
    return render(request, 'plantillas/opcional_list.html', {
        'opcionales': opcionales,
        'sort': sort,
        'dir': direction,
    })


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
    from pricing.models import Perfil, Hoja, Vidrio, Extrusora, Linea, Producto, Accesorio
    from .models import RelacionProductoOpcional, AccesorioOpcional
    
    opcional = get_object_or_404(OpcionalFabrica, pk=pk)
    formulas = FormulaOpcional.objects.filter(opcional=opcional).order_by('orden')
    relaciones = RelacionProductoOpcional.objects.filter(opcional=opcional).order_by('orden')
    accesorios = AccesorioOpcional.objects.filter(opcional=opcional).order_by('orden')
    
    # Obtener datos para los selectores
    perfiles = Perfil.objects.exclude(bloqueado='Si').order_by('codigo')
    hojas = Hoja.objects.exclude(bloqueado='Si').order_by('descripcion')[:200]
    vidrios = Vidrio.objects.exclude(bloqueado='Si').order_by('codigo')[:200]
    extrusoras = Extrusora.objects.exclude(bloqueado='Si').order_by('nombre')
    lineas = Linea.objects.exclude(bloqueado='Si').order_by('nombre')
    productos = Producto.objects.exclude(bloqueado='Si').order_by('descripcion')[:200]
    accesorios_list = Accesorio.objects.exclude(bloqueado='Si').order_by('codigo')[:200]
    
    # Mapa producto_id -> {extrusora_id, linea_id} para inicializar selects
    productos_map = {str(p.id): {'extrusora_id': str(p.extrusora_id), 'linea_id': str(p.linea_id)} for p in productos}
    import json
    productos_map_json = json.dumps(productos_map)
    
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
        'accesorios': accesorios,
        'perfiles': perfiles,
        'hojas': hojas,
        'vidrios': vidrios,
        'extrusoras': extrusoras,
        'lineas': lineas,
        'productos': productos,
        'accesorios_list': accesorios_list,
        'productos_map_json': productos_map_json
    })


@login_required
def opcional_delete(request, pk):
    opcional = get_object_or_404(OpcionalFabrica, pk=pk)
    opcional.activo = False
    opcional.save()
    messages.success(request, f'Opcional {opcional.codigo} eliminado.')
    return redirect('plantillas:opcional_list')


@login_required
def opcional_formulas_guardar(request, pk):
    from pricing.models import Perfil, Producto

    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    opcional = get_object_or_404(OpcionalFabrica, pk=pk)
    
    try:
        nuevas_formulas = []
        index = 0
        while f'cantidad_{index}' in request.POST:
            cantidad = request.POST.get(f'cantidad_{index}', '').strip()
            formula_texto = request.POST.get(f'formula_{index}', '').strip()
            perfil = request.POST.get(f'perfil_{index}', '').strip()
            
            if not any([cantidad, formula_texto, perfil]):
                index += 1
                continue

            if not cantidad or not formula_texto:
                return JsonResponse({'error': f'Completa cantidad y fórmula en la fila {index + 1}.'}, status=400)

            if opcional.tipo == 'mosquitero':
                if not perfil:
                    return JsonResponse({'error': f'Selecciona un producto en la fila {index + 1}.'}, status=400)
                if not Producto.objects.exclude(bloqueado='Si').filter(pk=perfil).exists():
                    return JsonResponse({'error': f'El producto seleccionado en la fila {index + 1} no existe.'}, status=400)
            else:
                if not perfil:
                    return JsonResponse({'error': f'Selecciona un perfil en la fila {index + 1}.'}, status=400)

                perfil_obj = Perfil.objects.exclude(bloqueado='Si').filter(pk=perfil).first()
                if not perfil_obj:
                    return JsonResponse({'error': f'El perfil seleccionado en la fila {index + 1} no existe.'}, status=400)

                if opcional.tipo == 'premarco':
                    if not opcional.linea_id:
                        return JsonResponse({'error': 'Guarda primero la línea del opcional Premarco.'}, status=400)
                    if perfil_obj.linea_id != opcional.linea_id:
                        return JsonResponse({'error': f'El perfil de la fila {index + 1} no pertenece a la línea seleccionada.'}, status=400)

            nuevas_formulas.append(FormulaOpcional(
                    opcional=opcional,
                    cantidad=cantidad,
                    formula=formula_texto,
                    angulo='',
                    tipo_relacionador='perfil',
                    perfil=perfil,
                    precio=0,
                    orden=index
                ))
            
            index += 1

        with transaction.atomic():
            OpcionalFabrica.objects.select_for_update().get(pk=opcional.pk)
            FormulaOpcional.objects.filter(opcional=opcional).delete()
            FormulaOpcional.objects.bulk_create(nuevas_formulas)
        
        return JsonResponse({'ok': True, 'guardadas': len(nuevas_formulas)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def opcional_accesorios_guardar(request, pk):
    from .models import AccesorioOpcional
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    opcional = get_object_or_404(OpcionalFabrica, pk=pk)
    
    try:
        nuevos_accesorios = []
        index = 0
        while f'cantidad_acc_{index}' in request.POST:
            cantidad = request.POST.get(f'cantidad_acc_{index}', '').strip()
            accesorio = request.POST.get(f'accesorio_{index}', '').strip()

            if cantidad and accesorio:
                nuevos_accesorios.append(AccesorioOpcional(
                    opcional=opcional,
                    cantidad=cantidad,
                    accesorio=accesorio,
                    orden=index
                ))

            index += 1

        with transaction.atomic():
            OpcionalFabrica.objects.select_for_update().get(pk=opcional.pk)
            AccesorioOpcional.objects.filter(opcional=opcional).delete()
            AccesorioOpcional.objects.bulk_create(nuevos_accesorios)

        return JsonResponse({'ok': True, 'guardadas': len(nuevos_accesorios)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def opcional_relaciones_guardar(request, pk):
    from .models import RelacionProductoOpcional
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    opcional = get_object_or_404(OpcionalFabrica, pk=pk)
    
    try:
        nuevas_relaciones = []
        index = 0
        while f'extrusora_{index}' in request.POST:
            extrusora_id = request.POST.get(f'extrusora_{index}', '').strip()
            linea_id = request.POST.get(f'linea_{index}', '').strip()
            producto_id = request.POST.get(f'producto_{index}', '').strip()
            cantidad = request.POST.get(f'cantidad_{index}', '1').strip()

            if extrusora_id and linea_id and producto_id:
                nuevas_relaciones.append(RelacionProductoOpcional(
                    opcional=opcional,
                    extrusora_id=int(extrusora_id),
                    linea_id=int(linea_id),
                    producto_id=int(producto_id),
                    cantidad=int(cantidad) if cantidad else 1,
                    orden=index
                ))

            index += 1

        with transaction.atomic():
            OpcionalFabrica.objects.select_for_update().get(pk=opcional.pk)
            RelacionProductoOpcional.objects.filter(opcional=opcional).delete()
            RelacionProductoOpcional.objects.bulk_create(nuevas_relaciones)

        return JsonResponse({'ok': True, 'guardadas': len(nuevas_relaciones)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
