from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json

from .models import ProductoPlantilla, CampoPlantilla, CalculoEjecucion, PedidoFabrica, PedidoFabricaItem
from .forms import ProductoPlantillaForm, CampoPlantillaForm
from .services.formula_engine import FormulaEngine


# ============ ABM PLANTILLAS ============

@login_required
def plantilla_list(request):
    """Listado de plantillas"""
    plantillas = ProductoPlantilla.objects.all()
    return render(request, 'plantillas/plantilla_list.html', {'plantillas': plantillas})


@login_required
def plantilla_create(request):
    """Crear plantilla"""
    if request.method == 'POST':
        form = ProductoPlantillaForm(request.POST)
        if form.is_valid():
            plantilla = form.save()
            messages.success(request, f'Plantilla "{plantilla.nombre}" creada exitosamente')
            return redirect('plantillas:plantilla_campos', pk=plantilla.pk)
    else:
        form = ProductoPlantillaForm()
    
    return render(request, 'plantillas/plantilla_form.html', {'form': form, 'title': 'Nueva Plantilla'})


@login_required
def plantilla_edit(request, pk):
    """Editar plantilla"""
    plantilla = get_object_or_404(ProductoPlantilla, pk=pk)
    
    if request.method == 'POST':
        form = ProductoPlantillaForm(request.POST, instance=plantilla)
        if form.is_valid():
            form.save()
            messages.success(request, 'Plantilla actualizada exitosamente')
            return redirect('plantillas:plantilla_list')
    else:
        form = ProductoPlantillaForm(instance=plantilla)
    
    return render(request, 'plantillas/plantilla_form.html', {
        'form': form,
        'title': 'Editar Plantilla',
        'plantilla': plantilla
    })


@login_required
def plantilla_toggle(request, pk):
    """Activar/desactivar plantilla"""
    plantilla = get_object_or_404(ProductoPlantilla, pk=pk)
    plantilla.activo = not plantilla.activo
    plantilla.save()
    
    estado = 'activada' if plantilla.activo else 'desactivada'
    messages.success(request, f'Plantilla "{plantilla.nombre}" {estado}')
    return redirect('plantillas:plantilla_list')


# ============ CONFIGURADOR DE CAMPOS ============

@login_required
def plantilla_campos(request, pk):
    """Configurador de campos de una plantilla"""
    plantilla = get_object_or_404(ProductoPlantilla, pk=pk)
    campos = plantilla.campos.all().order_by('orden', 'id')
    
    # Detectar campos con variables pendientes
    available_vars = set(campos.values_list('clave', flat=True))
    warnings = {}
    for campo in campos:
        if campo.modo == 'CALCULADO' and campo.formula:
            from .services.formula_engine import FormulaEngine
            valid, error = FormulaEngine.validate_formula(campo.formula, available_vars, strict=True)
            if not valid:
                warnings[campo.id] = error
    
    return render(request, 'plantillas/plantilla_campos.html', {
        'plantilla': plantilla,
        'campos': campos,
        'warnings': warnings
    })


@login_required
def campo_create(request, plantilla_pk):
    """Crear campo"""
    plantilla = get_object_or_404(ProductoPlantilla, pk=plantilla_pk)
    
    if request.method == 'POST':
        form = CampoPlantillaForm(request.POST, plantilla=plantilla)
        if form.is_valid():
            campo = form.save(commit=False)
            campo.plantilla = plantilla
            campo.save()
            messages.success(request, f'Campo "{campo.nombre_visible}" creado exitosamente')
            return redirect('plantillas:plantilla_campos', pk=plantilla.pk)
    else:
        # Orden automático
        max_orden = plantilla.campos.count()
        form = CampoPlantillaForm(plantilla=plantilla, initial={'orden': max_orden + 1})
    
    return render(request, 'plantillas/campo_form.html', {
        'form': form,
        'plantilla': plantilla,
        'title': 'Nuevo Campo'
    })


@login_required
def campo_edit(request, pk):
    """Editar campo"""
    campo = get_object_or_404(CampoPlantilla, pk=pk)
    plantilla = campo.plantilla
    
    if request.method == 'POST':
        form = CampoPlantillaForm(request.POST, instance=campo, plantilla=plantilla)
        if form.is_valid():
            form.save()
            messages.success(request, 'Campo actualizado exitosamente')
            return redirect('plantillas:plantilla_campos', pk=plantilla.pk)
    else:
        form = CampoPlantillaForm(instance=campo, plantilla=plantilla)
    
    return render(request, 'plantillas/campo_form.html', {
        'form': form,
        'plantilla': plantilla,
        'campo': campo,
        'title': 'Editar Campo'
    })


@login_required
def campo_delete(request, pk):
    """Eliminar campo"""
    campo = get_object_or_404(CampoPlantilla, pk=pk)
    plantilla = campo.plantilla
    
    # Verificar si otro campo lo usa
    campos_dependientes = []
    for c in plantilla.campos.exclude(pk=campo.pk):
        if c.formula and campo.clave in c.formula.upper():
            campos_dependientes.append(c.nombre_visible)
    
    if campos_dependientes:
        messages.error(request, f'No se puede eliminar. Los siguientes campos lo usan: {", ".join(campos_dependientes)}')
    else:
        nombre = campo.nombre_visible
        campo.delete()
        messages.success(request, f'Campo "{nombre}" eliminado')
    
    return redirect('plantillas:plantilla_campos', pk=plantilla.pk)


# ============ PROBAR PLANTILLA ============

@login_required
def plantilla_probar(request, pk):
    """Probar cálculo de plantilla"""
    plantilla = get_object_or_404(ProductoPlantilla, pk=pk)
    campos = plantilla.campos.all().order_by('orden', 'id')
    
    outputs = {}
    errores = {}
    inputs = {}
    
    if request.method == 'POST':
        # Recoger SOLO inputs manuales
        for campo in campos:
            if campo.modo == 'MANUAL':
                value = request.POST.get(campo.clave, '')
                # Normalizar decimales
                if campo.tipo == 'number' and isinstance(value, str):
                    value = value.replace(',', '.')
                inputs[campo.clave] = value
        
        # Calcular
        outputs, errores = FormulaEngine.calculate(list(campos), inputs)
    
    return render(request, 'plantillas/plantilla_probar.html', {
        'plantilla': plantilla,
        'campos': campos,
        'outputs': outputs,
        'errores': errores,
        'inputs': inputs
    })


# ============ PANTALLA OPERATIVA ============

@login_required
def calcular_index(request):
    """Pantalla principal de cálculo"""
    plantillas = ProductoPlantilla.objects.filter(activo=True)
    return render(request, 'plantillas/calcular_index.html', {'plantillas': plantillas})


@login_required
def calcular_ejecutar(request, pk):
    """Ejecutar cálculo de una plantilla"""
    plantilla = get_object_or_404(ProductoPlantilla, pk=pk, activo=True)
    campos = plantilla.campos.all().order_by('orden', 'id')
    
    outputs = {}
    errores = {}
    inputs = {}
    
    if request.method == 'POST':
        # Recoger SOLO inputs manuales (seguridad: ignorar outputs posteados)
        for campo in campos:
            if campo.modo == 'MANUAL':
                value = request.POST.get(campo.clave, '')
                # Normalizar input: convertir coma a punto para decimales
                if campo.tipo == 'number' and isinstance(value, str):
                    value = value.replace(',', '.')
                inputs[campo.clave] = value
        
        # Calcular (el motor genera los outputs, no vienen del form)
        outputs, errores = FormulaEngine.calculate(list(campos), inputs)
        
        # Guardar ejecución
        if not errores:
            CalculoEjecucion.objects.create(
                plantilla=plantilla,
                inputs_json=json.dumps(inputs),
                outputs_json=json.dumps(outputs),
                errores_json=json.dumps(errores),
                usuario=request.user
            )
            messages.success(request, 'Cálculo realizado exitosamente')
    
    return render(request, 'plantillas/calcular_ejecutar.html', {
        'plantilla': plantilla,
        'campos': campos,
        'outputs': outputs,
        'errores': errores,
        'inputs': inputs
    })


# ============ API AJAX ============

@login_required
@require_http_methods(["POST"])
def calcular_ajax(request, pk):
    """Calcular vía AJAX para recálculo en vivo"""
    plantilla = get_object_or_404(ProductoPlantilla, pk=pk, activo=True)
    campos = plantilla.campos.all()
    
    try:
        data = json.loads(request.body)
        inputs = data.get('inputs', {})
        
        outputs, errores = FormulaEngine.calculate(list(campos), inputs)
        
        return JsonResponse({
            'success': True,
            'outputs': outputs,
            'errores': errores
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
def historial_calculos(request):
    """Historial de cálculos ejecutados"""
    ejecuciones = CalculoEjecucion.objects.select_related('plantilla', 'usuario').all()[:50]
    return render(request, 'plantillas/historial_calculos.html', {'ejecuciones': ejecuciones})


# ============ PEDIDOS DE FÁBRICA ============

@login_required
def pedido_list(request):
    """Listado de pedidos"""
    pedidos = PedidoFabrica.objects.all()
    return render(request, 'plantillas/pedido_list.html', {'pedidos': pedidos})


@login_required
def pedido_create(request):
    """Crear pedido"""
    if request.method == 'POST':
        numero = request.POST.get('numero')
        cliente = request.POST.get('cliente')
        observaciones = request.POST.get('observaciones', '')
        
        pedido = PedidoFabrica.objects.create(
            numero=numero,
            cliente=cliente,
            observaciones=observaciones,
            usuario=request.user
        )
        messages.success(request, f'Pedido {numero} creado exitosamente')
        return redirect('plantillas:pedido_detail', pk=pedido.pk)
    
    # Generar número automático
    ultimo = PedidoFabrica.objects.count() + 1
    numero_sugerido = f"PF-{ultimo:04d}"
    
    return render(request, 'plantillas/pedido_form.html', {'numero_sugerido': numero_sugerido})


@login_required
def pedido_detail(request, pk):
    """Detalle de pedido con cuadros"""
    pedido = get_object_or_404(PedidoFabrica, pk=pk)
    items = pedido.items.select_related('plantilla').prefetch_related('plantilla__campos').all()
    plantillas_activas = ProductoPlantilla.objects.filter(activo=True)
    
    return render(request, 'plantillas/pedido_detail.html', {
        'pedido': pedido,
        'items': items,
        'plantillas_activas': plantillas_activas
    })


@login_required
def pedido_add_item(request, pedido_pk):
    """Agregar item (cuadro) al pedido"""
    pedido = get_object_or_404(PedidoFabrica, pk=pedido_pk)
    
    if request.method == 'POST':
        plantilla_id = request.POST.get('plantilla_id')
        plantilla = get_object_or_404(ProductoPlantilla, pk=plantilla_id, activo=True)
        
        # Calcular orden
        max_orden = pedido.items.count()
        
        item = PedidoFabricaItem.objects.create(
            pedido=pedido,
            plantilla=plantilla,
            orden=max_orden + 1
        )
        
        messages.success(request, f'Plantilla "{plantilla.nombre}" agregada al pedido')
    
    return redirect('plantillas:pedido_detail', pk=pedido.pk)


@login_required
def pedido_item_calcular(request, item_pk):
    """Calcular un item del pedido"""
    item = get_object_or_404(PedidoFabricaItem, pk=item_pk)
    campos = item.plantilla.campos.all().order_by('orden', 'id')
    
    if request.method == 'POST':
        # Recoger SOLO inputs manuales
        inputs = {}
        for campo in campos:
            if campo.modo == 'MANUAL':
                value = request.POST.get(campo.clave, '')
                if campo.tipo == 'number' and isinstance(value, str):
                    value = value.replace(',', '.')
                inputs[campo.clave] = value
        
        # Recoger OBS y CANT
        item.obs = request.POST.get('obs', '')
        try:
            item.cantidad = int(request.POST.get('cantidad', 1))
        except ValueError:
            item.cantidad = 1
        
        # Calcular
        outputs, errores = FormulaEngine.calculate(list(campos), inputs)
        
        # Guardar
        item.inputs_json = json.dumps(inputs)
        item.outputs_json = json.dumps(outputs)
        item.errores_json = json.dumps(errores)
        item.estado = 'ERROR' if errores else 'OK'
        item.save()
        
        if errores:
            messages.warning(request, f'Item calculado con errores')
        else:
            messages.success(request, f'Item calculado exitosamente')
    
    return redirect('plantillas:pedido_detail', pk=item.pedido.pk)


@login_required
def pedido_item_duplicate(request, item_pk):
    """Duplicar item"""
    item = get_object_or_404(PedidoFabricaItem, pk=item_pk)
    
    # Crear copia
    max_orden = item.pedido.items.count()
    nuevo_item = PedidoFabricaItem.objects.create(
        pedido=item.pedido,
        plantilla=item.plantilla,
        orden=max_orden + 1,
        inputs_json=item.inputs_json,
        obs=item.obs,
        cantidad=item.cantidad,
        estado='SIN_CALCULAR'  # Requiere recalcular
    )
    
    messages.success(request, 'Item duplicado exitosamente')
    return redirect('plantillas:pedido_detail', pk=item.pedido.pk)


@login_required
def pedido_item_delete(request, item_pk):
    """Eliminar item"""
    item = get_object_or_404(PedidoFabricaItem, pk=item_pk)
    pedido_pk = item.pedido.pk
    item.delete()
    
    messages.success(request, 'Item eliminado')
    return redirect('plantillas:pedido_detail', pk=pedido_pk)
