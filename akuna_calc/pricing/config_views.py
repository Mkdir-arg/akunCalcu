"""Vistas de configuración para ABMs de pricing."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Max
from django.http import JsonResponse
from .models import Extrusora, Linea, Producto, Marco, Hoja, Interior, Perfil, Accesorio, Vidrio, Tratamiento
from .forms import (
    ExtrusoraForm, LineaForm, ProductoForm, MarcoForm, HojaForm, InteriorForm,
    PerfilCreateForm, PerfilEditForm,
    AccesorioCreateForm, AccesorioEditForm,
    VidrioCreateForm, VidrioEditForm,
    TratamientoForm,
)


def is_staff(user):
    return user.is_staff


def _next_id(model):
    max_id = model.objects.aggregate(Max('id'))['id__max'] or 0
    return max_id + 1


# ─── EXTRUSORAS ───────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_staff)
def extrusoras_config(request):
    extrusoras = Extrusora.objects.exclude(bloqueado='Si')
    return render(request, 'pricing/config/extrusoras.html', {'extrusoras': extrusoras})


@login_required
@user_passes_test(is_staff)
def extrusora_create(request):
    form = ExtrusoraForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.id = _next_id(Extrusora)
        obj.save()
        messages.success(request, 'Extrusora creada correctamente.')
        return redirect('config-extrusoras')
    return render(request, 'pricing/config/extrusora_form.html', {'form': form, 'titulo': 'Nueva Extrusora', 'cancel_url': 'config-extrusoras'})


@login_required
@user_passes_test(is_staff)
def extrusora_edit(request, pk):
    obj = get_object_or_404(Extrusora, pk=pk)
    form = ExtrusoraForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Extrusora actualizada correctamente.')
        return redirect('config-extrusoras')
    return render(request, 'pricing/config/extrusora_form.html', {'form': form, 'titulo': 'Editar Extrusora', 'cancel_url': 'config-extrusoras', 'object': obj})


@login_required
@user_passes_test(is_staff)
def extrusora_delete(request, pk):
    obj = get_object_or_404(Extrusora, pk=pk)
    if request.method == 'POST':
        obj.bloqueado = 'Si'
        obj.save()
        messages.success(request, 'Extrusora desactivada.')
    return redirect('config-extrusoras')


# ─── LÍNEAS ───────────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_staff)
def lineas_config(request):
    lineas = Linea.objects.select_related('extrusora').exclude(bloqueado='Si')
    extrusoras = Extrusora.objects.exclude(bloqueado='Si')
    return render(request, 'pricing/config/lineas.html', {'lineas': lineas, 'extrusoras': extrusoras})


@login_required
@user_passes_test(is_staff)
def linea_create(request):
    form = LineaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.id = _next_id(Linea)
        obj.save()
        messages.success(request, 'Línea creada correctamente.')
        return redirect('config-lineas')
    return render(request, 'pricing/config/linea_form.html', {'form': form, 'titulo': 'Nueva Línea', 'cancel_url': 'config-lineas'})


@login_required
@user_passes_test(is_staff)
def linea_edit(request, pk):
    obj = get_object_or_404(Linea, pk=pk)
    form = LineaForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Línea actualizada correctamente.')
        return redirect('config-lineas')
    return render(request, 'pricing/config/linea_form.html', {'form': form, 'titulo': 'Editar Línea', 'cancel_url': 'config-lineas', 'object': obj})


@login_required
@user_passes_test(is_staff)
def linea_delete(request, pk):
    obj = get_object_or_404(Linea, pk=pk)
    if request.method == 'POST':
        obj.bloqueado = 'Si'
        obj.save()
        messages.success(request, 'Línea desactivada.')
    return redirect('config-lineas')


# ─── PRODUCTOS ────────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_staff)
def productos_config(request):
    productos = Producto.objects.select_related('linea', 'extrusora').exclude(bloqueado='Si')
    lineas = Linea.objects.exclude(bloqueado='Si')
    return render(request, 'pricing/config/productos.html', {'productos': productos, 'lineas': lineas})


@login_required
@user_passes_test(is_staff)
def producto_create(request):
    form = ProductoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.id = _next_id(Producto)
        obj.save()
        messages.success(request, 'Producto creado correctamente.')
        return redirect('config-productos')
    return render(request, 'pricing/config/producto_form.html', {'form': form, 'titulo': 'Nuevo Producto', 'cancel_url': 'config-productos'})


@login_required
@user_passes_test(is_staff)
def producto_edit(request, pk):
    obj = get_object_or_404(Producto, pk=pk)
    form = ProductoForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Producto actualizado correctamente.')
        return redirect('config-productos')
    return render(request, 'pricing/config/producto_form.html', {'form': form, 'titulo': 'Editar Producto', 'cancel_url': 'config-productos', 'object': obj})


@login_required
@user_passes_test(is_staff)
def producto_delete(request, pk):
    obj = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        obj.bloqueado = 'Si'
        obj.save()
        messages.success(request, 'Producto desactivado.')
    return redirect('config-productos')


# ─── MARCOS ───────────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_staff)
def marcos_config(request):
    marcos = Marco.objects.select_related('producto').exclude(bloqueado='Si')
    productos = Producto.objects.exclude(bloqueado='Si')
    return render(request, 'pricing/config/marcos.html', {'marcos': marcos, 'productos': productos})


@login_required
@user_passes_test(is_staff)
def marco_create(request):
    form = MarcoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.id = _next_id(Marco)
        obj.save()
        
        # Guardar fórmulas si existen
        if 'formula_cantidad_0' in request.POST:
            from .models import DespiecePerfilesMarco
            index = 0
            while f'formula_cantidad_{index}' in request.POST:
                variable = request.POST.get(f'formula_variable_{index}')
                operador = request.POST.get(f'formula_operador_{index}')
                valor = request.POST.get(f'formula_valor_{index}')
                formula_texto = f"{variable} {operador} {valor}"
                
                try:
                    max_id = DespiecePerfilesMarco.objects.aggregate(Max('id'))['id__max'] or 0
                    DespiecePerfilesMarco.objects.create(
                        id=max_id + 1,
                        marco=obj,
                        formula_cantidad=request.POST.get(f'formula_cantidad_{index}'),
                        formula_perfil=formula_texto,
                        angulo=request.POST.get(f'formula_angulo_{index}'),
                        perfil=request.POST.get(f'formula_perfil_{index}')
                    )
                except Exception as e:
                    messages.warning(request, f'No se pudieron guardar las fórmulas: {str(e)}')
                    break
                index += 1
        
        messages.success(request, 'Marco creado correctamente.')
        return redirect('config-marcos')
    return render(request, 'pricing/config/marco_form.html', {'form': form, 'titulo': 'Nuevo Marco', 'cancel_url': 'config-marcos'})


@login_required
@user_passes_test(is_staff)
def marco_edit(request, pk):
    obj = get_object_or_404(Marco, pk=pk)
    form = MarcoForm(request.POST or None, instance=obj)
    
    from .models import DespiecePerfilesMarco
    formulas = []
    try:
        formulas = list(DespiecePerfilesMarco.objects.filter(marco=obj))
    except:
        pass
    
    if request.method == 'POST' and form.is_valid():
        form.save()
        
        # Eliminar fórmulas existentes y crear nuevas
        if 'formula_cantidad_0' in request.POST:
            try:
                DespiecePerfilesMarco.objects.filter(marco=obj).delete()
                index = 0
                while f'formula_cantidad_{index}' in request.POST:
                    variable = request.POST.get(f'formula_variable_{index}')
                    operador = request.POST.get(f'formula_operador_{index}')
                    valor = request.POST.get(f'formula_valor_{index}')
                    formula_texto = f"{variable} {operador} {valor}"
                    
                    max_id = DespiecePerfilesMarco.objects.aggregate(Max('id'))['id__max'] or 0
                    DespiecePerfilesMarco.objects.create(
                        id=max_id + 1,
                        marco=obj,
                        formula_cantidad=request.POST.get(f'formula_cantidad_{index}'),
                        formula_perfil=formula_texto,
                        angulo=request.POST.get(f'formula_angulo_{index}'),
                        perfil=request.POST.get(f'formula_perfil_{index}')
                    )
                    index += 1
            except Exception as e:
                messages.warning(request, f'No se pudieron guardar las fórmulas: {str(e)}')
        
        messages.success(request, 'Marco actualizado correctamente.')
        return redirect('config-marcos')
    return render(request, 'pricing/config/marco_form.html', {'form': form, 'titulo': 'Editar Marco', 'cancel_url': 'config-marcos', 'object': obj, 'formulas': formulas})


@login_required
@user_passes_test(is_staff)
def marco_delete(request, pk):
    obj = get_object_or_404(Marco, pk=pk)
    if request.method == 'POST':
        obj.bloqueado = 'Si'
        obj.save()
        messages.success(request, 'Marco desactivado.')
    return redirect('config-marcos')


@login_required
@user_passes_test(is_staff)
def marco_formulas_guardar(request, pk):
    """Guarda las fórmulas de un marco via AJAX sin redirigir."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    obj = get_object_or_404(Marco, pk=pk)
    from .models import DespiecePerfilesMarco

    try:
        DespiecePerfilesMarco.objects.filter(marco=obj).delete()
        index = 0
        guardadas = 0
        while f'formula_cantidad_{index}' in request.POST:
            variable = request.POST.get(f'formula_variable_{index}', '')
            operador = request.POST.get(f'formula_operador_{index}', '')
            valor = request.POST.get(f'formula_valor_{index}', '')
            formula_texto = f"{variable} {operador} {valor}"

            max_id = DespiecePerfilesMarco.objects.aggregate(Max('id'))['id__max'] or 0
            DespiecePerfilesMarco.objects.create(
                id=max_id + 1,
                marco=obj,
                formula_cantidad=request.POST.get(f'formula_cantidad_{index}'),
                formula_perfil=formula_texto,
                angulo=request.POST.get(f'formula_angulo_{index}'),
                perfil=request.POST.get(f'formula_perfil_{index}'),
            )
            guardadas += 1
            index += 1

        return JsonResponse({'ok': True, 'guardadas': guardadas})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ─── HOJAS ────────────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_staff)
def hojas_config(request):
    hojas = Hoja.objects.select_related('marco').exclude(bloqueado='Si')
    marcos = Marco.objects.exclude(bloqueado='Si')
    return render(request, 'pricing/config/hojas.html', {'hojas': hojas, 'marcos': marcos})


@login_required
@user_passes_test(is_staff)
def hoja_create(request):
    form = HojaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.id = _next_id(Hoja)
        obj.cantidad = 1  # Valor por defecto
        obj.save()
        messages.success(request, 'Hoja creada correctamente.')
        return redirect('config-hoja-edit', pk=obj.id)
    return render(request, 'pricing/config/hoja_form.html', {'form': form, 'titulo': 'Nueva Hoja', 'cancel_url': 'config-hojas'})


@login_required
@user_passes_test(is_staff)
def hoja_edit(request, pk):
    obj = get_object_or_404(Hoja, pk=pk)
    form = HojaForm(request.POST or None, instance=obj)
    
    from .models import DespiecePerfilesHoja
    import json
    
    formulas = []
    try:
        formulas = list(DespiecePerfilesHoja.objects.filter(hoja=obj))
    except:
        pass
    
    perfiles = Perfil.objects.exclude(bloqueado='Si').filter(tipo_perfil='Hojas').values('codigo', 'descripcion')
    perfiles_json = json.dumps(list(perfiles))
    
    if request.method == 'POST':
        # Si es una petición AJAX para guardar solo fórmulas
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'HTTP_X_REQUESTED_WITH' in request.META:
            try:
                DespiecePerfilesHoja.objects.filter(hoja=obj).delete()
                index = 0
                guardadas = 0
                while f'perfil_{index}' in request.POST:
                    perfil = request.POST.get(f'perfil_{index}')
                    cantidad = request.POST.get(f'cantidad_{index}')
                    variable = request.POST.get(f'formula_variable_{index}')
                    operador = request.POST.get(f'formula_operador_{index}')
                    valor = request.POST.get(f'formula_valor_{index}')
                    angulo = request.POST.get(f'angulo_{index}')
                    
                    if perfil and cantidad and variable and operador and valor:
                        formula_texto = f"{variable} {operador} {valor}"
                        max_id = DespiecePerfilesHoja.objects.aggregate(Max('id'))['id__max'] or 0
                        DespiecePerfilesHoja.objects.create(
                            id=max_id + 1,
                            hoja=obj,
                            perfil=perfil,
                            formula_cantidad=cantidad,
                            formula_perfil=formula_texto,
                            angulo=angulo or ''
                        )
                        guardadas += 1
                    index += 1
                return JsonResponse({'ok': True, 'guardadas': guardadas})
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)
        
        # Guardado normal del formulario
        if form.is_valid():
            form.save()
            
            # Guardar fórmulas con formato estructurado
            if 'perfil_0' in request.POST:
                try:
                    DespiecePerfilesHoja.objects.filter(hoja=obj).delete()
                    index = 0
                    while f'perfil_{index}' in request.POST:
                        perfil = request.POST.get(f'perfil_{index}')
                        cantidad = request.POST.get(f'cantidad_{index}')
                        variable = request.POST.get(f'formula_variable_{index}')
                        operador = request.POST.get(f'formula_operador_{index}')
                        valor = request.POST.get(f'formula_valor_{index}')
                        angulo = request.POST.get(f'angulo_{index}')
                        
                        if perfil and cantidad and variable and operador and valor:
                            formula_texto = f"{variable} {operador} {valor}"
                            max_id = DespiecePerfilesHoja.objects.aggregate(Max('id'))['id__max'] or 0
                            DespiecePerfilesHoja.objects.create(
                                id=max_id + 1,
                                hoja=obj,
                                perfil=perfil,
                                formula_cantidad=cantidad,
                                formula_perfil=formula_texto,
                                angulo=angulo or ''
                            )
                        index += 1
                except Exception as e:
                    messages.warning(request, f'No se pudieron guardar las fórmulas: {str(e)}')
            
            messages.success(request, 'Hoja actualizada correctamente.')
            return redirect('config-hojas')
    
    return render(request, 'pricing/config/hoja_form.html', {
        'form': form, 
        'titulo': 'Editar Hoja', 
        'cancel_url': 'config-hojas', 
        'object': obj, 
        'hoja': obj, 
        'formulas': formulas,
        'perfiles': perfiles,
        'perfiles_json': perfiles_json
    })


@login_required
@user_passes_test(is_staff)
def hoja_delete(request, pk):
    obj = get_object_or_404(Hoja, pk=pk)
    if request.method == 'POST':
        obj.bloqueado = 'Si'
        obj.save()
        messages.success(request, 'Hoja desactivada.')
    return redirect('config-hojas')


# ─── INTERIORES ───────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_staff)
def interiores_config(request):
    interiores = Interior.objects.select_related('hoja').exclude(bloqueado='Si')
    hojas = Hoja.objects.exclude(bloqueado='Si')
    return render(request, 'pricing/config/interiores.html', {'interiores': interiores, 'hojas': hojas})


@login_required
@user_passes_test(is_staff)
def interior_create(request):
    form = InteriorForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.id = _next_id(Interior)
        obj.save()
        messages.success(request, 'Interior creado correctamente.')
        return redirect('config-interiores')
    return render(request, 'pricing/config/interior_form.html', {'form': form, 'titulo': 'Nuevo Interior', 'cancel_url': 'config-interiores'})


@login_required
@user_passes_test(is_staff)
def interior_edit(request, pk):
    obj = get_object_or_404(Interior, pk=pk)
    form = InteriorForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Interior actualizado correctamente.')
        return redirect('config-interiores')
    return render(request, 'pricing/config/interior_form.html', {'form': form, 'titulo': 'Editar Interior', 'cancel_url': 'config-interiores', 'object': obj})


@login_required
@user_passes_test(is_staff)
def interior_delete(request, pk):
    obj = get_object_or_404(Interior, pk=pk)
    if request.method == 'POST':
        obj.bloqueado = 'Si'
        obj.save()
        messages.success(request, 'Interior desactivado.')
    return redirect('config-interiores')


# ─── PERFILES ─────────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_staff)
def perfiles_config(request):
    perfiles = Perfil.objects.exclude(bloqueado='Si')[:200]
    return render(request, 'pricing/config/perfiles.html', {'perfiles': perfiles})


@login_required
@user_passes_test(is_staff)
def perfil_create(request):
    form = PerfilCreateForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Perfil creado correctamente.')
        return redirect('config-perfiles')
    return render(request, 'pricing/config/perfil_form.html', {'form': form, 'titulo': 'Nuevo Perfil', 'cancel_url': 'config-perfiles'})


@login_required
@user_passes_test(is_staff)
def perfil_edit(request, pk):
    obj = get_object_or_404(Perfil, pk=pk)
    form = PerfilEditForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Perfil actualizado correctamente.')
        return redirect('config-perfiles')
    return render(request, 'pricing/config/perfil_form.html', {'form': form, 'titulo': 'Editar Perfil', 'cancel_url': 'config-perfiles', 'object': obj})


@login_required
@user_passes_test(is_staff)
def perfil_delete(request, pk):
    obj = get_object_or_404(Perfil, pk=pk)
    if request.method == 'POST':
        obj.bloqueado = 'Si'
        obj.save()
        messages.success(request, 'Perfil desactivado.')
    return redirect('config-perfiles')


# ─── ACCESORIOS ───────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_staff)
def accesorios_config(request):
    accesorios = Accesorio.objects.exclude(bloqueado='Si')[:200]
    return render(request, 'pricing/config/accesorios.html', {'accesorios': accesorios})


@login_required
@user_passes_test(is_staff)
def accesorio_create(request):
    form = AccesorioCreateForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Accesorio creado correctamente.')
        return redirect('config-accesorios')
    return render(request, 'pricing/config/accesorio_form.html', {'form': form, 'titulo': 'Nuevo Accesorio', 'cancel_url': 'config-accesorios'})


@login_required
@user_passes_test(is_staff)
def accesorio_edit(request, pk):
    obj = get_object_or_404(Accesorio, pk=pk)
    form = AccesorioEditForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Accesorio actualizado correctamente.')
        return redirect('config-accesorios')
    return render(request, 'pricing/config/accesorio_form.html', {'form': form, 'titulo': 'Editar Accesorio', 'cancel_url': 'config-accesorios', 'object': obj})


@login_required
@user_passes_test(is_staff)
def accesorio_delete(request, pk):
    obj = get_object_or_404(Accesorio, pk=pk)
    if request.method == 'POST':
        obj.bloqueado = 'Si'
        obj.save()
        messages.success(request, 'Accesorio desactivado.')
    return redirect('config-accesorios')


# ─── VIDRIOS ──────────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_staff)
def vidrios_config(request):
    vidrios = Vidrio.objects.exclude(bloqueado='Si')
    return render(request, 'pricing/config/vidrios.html', {'vidrios': vidrios})


@login_required
@user_passes_test(is_staff)
def vidrio_create(request):
    form = VidrioCreateForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Vidrio creado correctamente.')
        return redirect('config-vidrios')
    return render(request, 'pricing/config/vidrio_form.html', {'form': form, 'titulo': 'Nuevo Vidrio', 'cancel_url': 'config-vidrios'})


@login_required
@user_passes_test(is_staff)
def vidrio_edit(request, pk):
    obj = get_object_or_404(Vidrio, pk=pk)
    form = VidrioEditForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Vidrio actualizado correctamente.')
        return redirect('config-vidrios')
    return render(request, 'pricing/config/vidrio_form.html', {'form': form, 'titulo': 'Editar Vidrio', 'cancel_url': 'config-vidrios', 'object': obj})


@login_required
@user_passes_test(is_staff)
def vidrio_delete(request, pk):
    obj = get_object_or_404(Vidrio, pk=pk)
    if request.method == 'POST':
        obj.bloqueado = 'Si'
        obj.save()
        messages.success(request, 'Vidrio desactivado.')
    return redirect('config-vidrios')


# ─── TRATAMIENTOS ─────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_staff)
def tratamientos_config(request):
    tratamientos = Tratamiento.objects.exclude(bloqueado='Si')
    return render(request, 'pricing/config/tratamientos.html', {'tratamientos': tratamientos})


@login_required
@user_passes_test(is_staff)
def tratamiento_create(request):
    form = TratamientoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.id = _next_id(Tratamiento)
        obj.save()
        messages.success(request, 'Tratamiento creado correctamente.')
        return redirect('config-tratamientos')
    return render(request, 'pricing/config/tratamiento_form.html', {'form': form, 'titulo': 'Nuevo Tratamiento', 'cancel_url': 'config-tratamientos'})


@login_required
@user_passes_test(is_staff)
def tratamiento_edit(request, pk):
    obj = get_object_or_404(Tratamiento, pk=pk)
    form = TratamientoForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Tratamiento actualizado correctamente.')
        return redirect('config-tratamientos')
    return render(request, 'pricing/config/tratamiento_form.html', {'form': form, 'titulo': 'Editar Tratamiento', 'cancel_url': 'config-tratamientos', 'object': obj})


@login_required
@user_passes_test(is_staff)
def tratamiento_delete(request, pk):
    obj = get_object_or_404(Tratamiento, pk=pk)
    if request.method == 'POST':
        obj.bloqueado = 'Si'
        obj.save()
        messages.success(request, 'Tratamiento desactivado.')
    return redirect('config-tratamientos')


# ─── API ENDPOINTS ────────────────────────────────────────────────────────────

@login_required
def api_get_producto(request, pk):
    """Retorna datos del producto para autocompletar formularios."""
    try:
        producto = Producto.objects.select_related('extrusora', 'linea').get(pk=pk)
        return JsonResponse({
            'extrusora_id': producto.extrusora.id,
            'extrusora_nombre': str(producto.extrusora),
            'linea_id': producto.linea.id,
            'linea_nombre': str(producto.linea),
        })
    except Producto.DoesNotExist:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)


@login_required
def api_get_marco(request, pk):
    """Retorna datos del marco para autocompletar formularios."""
    try:
        marco = Marco.objects.select_related('producto__extrusora', 'producto__linea').get(pk=pk)
        return JsonResponse({
            'extrusora_id': marco.producto.extrusora.id,
            'extrusora_nombre': str(marco.producto.extrusora),
            'linea_id': marco.producto.linea.id,
            'linea_nombre': str(marco.producto.linea),
            'producto_id': marco.producto.id,
            'producto_nombre': str(marco.producto),
        })
    except Marco.DoesNotExist:
        return JsonResponse({'error': 'Marco no encontrado'}, status=404)


@login_required
def api_get_hoja(request, pk):
    """Retorna datos de la hoja para autocompletar formularios."""
    try:
        hoja = Hoja.objects.select_related('marco__producto__extrusora', 'marco__producto__linea').get(pk=pk)
        return JsonResponse({
            'extrusora_id': hoja.marco.producto.extrusora.id,
            'extrusora_nombre': str(hoja.marco.producto.extrusora),
            'linea_id': hoja.marco.producto.linea.id,
            'linea_nombre': str(hoja.marco.producto.linea),
            'producto_id': hoja.marco.producto.id,
            'producto_nombre': str(hoja.marco.producto),
            'marco_id': hoja.marco.id,
            'marco_nombre': str(hoja.marco),
        })
    except Hoja.DoesNotExist:
        return JsonResponse({'error': 'Hoja no encontrada'}, status=404)


@login_required
def api_get_extrusoras(request):
    """Retorna lista de extrusoras."""
    extrusoras = Extrusora.objects.filter(bloqueado__isnull=True) | Extrusora.objects.filter(bloqueado='No')
    return JsonResponse({
        'extrusoras': [{'id': e.id, 'nombre': str(e)} for e in extrusoras]
    })


@login_required
def api_get_perfiles(request):
    """Retorna lista de perfiles filtrados por tipo."""
    tipo = request.GET.get('tipo', '')
    perfiles = Perfil.objects.filter(bloqueado__isnull=True)
    if tipo:
        perfiles = perfiles.filter(tipo_perfil=tipo)
    return JsonResponse(list(perfiles.values('codigo', 'descripcion')), safe=False)
