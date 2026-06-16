"""Vistas de configuración para ABMs de pricing."""

import logging
from functools import lru_cache
from urllib.parse import urlencode

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import IntegrityError, connection, transaction
from django.db.models import Max, Q
from django.http import Http404, JsonResponse
from plantillas.models import AccesorioOpcional

from .models import (
    Extrusora,
    Linea,
    Producto,
    Marco,
    Hoja,
    Interior,
    Perfil,
    Accesorio,
    Vidrio,
    Tratamiento,
    DespieceAccesoriosMarco,
    DespieceAccesoriosHoja,
    DespieceAccesoriosInterior,
    DespieceAccesoriosMosquitero,
    DespieceAccesoriosContravidrio,
    DespieceAccesoriosContravidrioExterior,
    DespieceAccesoriosCruces,
    DespieceAccesoriosVidrioRepartido,
)
from .forms import (
    ExtrusoraForm, LineaForm, ProductoForm, MarcoForm, HojaForm, InteriorForm,
    PerfilCreateForm, PerfilEditForm, PerfilBulkPriceForm,
    AccesorioCreateForm, AccesorioEditForm,
    VidrioCreateForm, VidrioEditForm,
    TratamientoForm,
)

logger = logging.getLogger(__name__)

_ACCESORIO_REFERENCE_MODELS = (
    DespieceAccesoriosMarco,
    DespieceAccesoriosHoja,
    DespieceAccesoriosInterior,
    DespieceAccesoriosMosquitero,
    DespieceAccesoriosContravidrio,
    DespieceAccesoriosContravidrioExterior,
    DespieceAccesoriosCruces,
    DespieceAccesoriosVidrioRepartido,
    AccesorioOpcional,
)


def is_staff(user):
    return user.is_staff


def _resolve_ordering(request, allowed_sort_fields, default_sort):
    sort = request.GET.get('sort', default_sort)
    if sort not in allowed_sort_fields:
        sort = default_sort

    direction = 'desc' if request.GET.get('dir') == 'desc' else 'asc'
    sort_fields = allowed_sort_fields[sort]
    if isinstance(sort_fields, str):
        sort_fields = (sort_fields,)

    ordering = [f'-{field}' if direction == 'desc' else field for field in sort_fields]
    return sort, direction, ordering


def _next_id(model):
    max_id = model.objects.aggregate(Max('id'))['id__max'] or 0
    return max_id + 1


def _guardar_nuevo_con_id(obj, model):
    """Guarda una entidad legacy nueva asignando el id a mano (tablas sin autoincremental).

    Si dos altas concurrentes calculan el mismo id, reintenta con uno nuevo.
    """
    for intento in range(3):
        try:
            with transaction.atomic():
                obj.id = _next_id(model)
                obj.save(force_insert=True)
            return obj
        except IntegrityError:
            if intento == 2:
                raise


def _reemplazar_filas_despiece(model, parent_field, parent_obj, filas):
    """Reemplaza atómicamente las filas de despiece de una entidad legacy.

    Las tablas de despiece no tienen PK autoincremental, por lo que el id se
    asigna a mano. Para evitar que dos guardados concurrentes (autosave de dos
    pestañas/usuarios) borren y recreen pisándose entre sí:
    - Se bloquea la fila del padre (select_for_update) para serializar los
      guardados sobre la misma entidad.
    - Todo el borrar+recrear ocurre en una transacción: o se guarda completo
      o no se toca nada.
    - Ante colisión de id con un guardado sobre otra entidad, se reintenta.
    """
    for intento in range(3):
        try:
            with transaction.atomic():
                parent_obj.__class__.objects.select_for_update().get(pk=parent_obj.pk)
                model.objects.filter(**{parent_field: parent_obj}).delete()
                max_id = model.objects.aggregate(Max('id'))['id__max'] or 0
                objetos = [
                    model(id=max_id + offset, **{parent_field: parent_obj}, **fila)
                    for offset, fila in enumerate(filas, start=1)
                ]
                model.objects.bulk_create(objetos)
            return len(objetos)
        except IntegrityError:
            if intento == 2:
                raise
    return 0


def _build_current_querystring(request, allowed_keys=None):
    query_items = []
    for key in allowed_keys or []:
        value = request.GET.get(key)
        if value:
            query_items.append((key, value))
    return urlencode(query_items)


def _redirect_to_perfiles_list(request):
    querystring = _build_current_querystring(request, allowed_keys=['sort', 'dir', 'linea'])
    if querystring:
        return redirect(f'{request.path}?{querystring}')
    return redirect('config-perfiles')


def _update_perfiles_precio(codigos, nuevo_precio):
    codigos_unicos = list(dict.fromkeys(codigo for codigo in codigos if codigo))
    if not codigos_unicos:
        return 0

    return (
        Perfil.objects.exclude(bloqueado='Si')
        .filter(codigo__in=codigos_unicos)
        .update(precio_kg=nuevo_precio)
    )


@lru_cache(maxsize=1)
def _get_existing_table_names():
    return frozenset(connection.introspection.table_names())


def _rename_accesorio_codigo_references(old_codigo, new_codigo):
    if not old_codigo or old_codigo == new_codigo:
        return

    existing_tables = _get_existing_table_names()

    for model in _ACCESORIO_REFERENCE_MODELS:
        table_name = model._meta.db_table
        if table_name not in existing_tables:
            logger.warning(
                "Se omite actualización de referencias para accesorio %s: tabla legacy ausente %s",
                old_codigo,
                table_name,
            )
            continue
        model.objects.filter(accesorio=old_codigo).update(accesorio=new_codigo)


def _save_accesorio_edit(old_codigo, old_tipo, cleaned_data):
    new_codigo = cleaned_data['codigo']
    new_tipo = cleaned_data['tipo']
    
    with transaction.atomic():
        # Si cambió el código o el tipo, necesitamos eliminar y recrear
        if old_codigo != new_codigo or old_tipo != new_tipo:
            # Primero actualizar todas las referencias
            _rename_accesorio_codigo_references(old_codigo, new_codigo)
            
            # Eliminar el registro viejo
            Accesorio.objects.filter(codigo=old_codigo, tipo=old_tipo).delete()
            
            # Crear el nuevo registro con el nuevo código y tipo
            Accesorio.objects.create(
                codigo=new_codigo,
                tipo=new_tipo,
                descripcion=cleaned_data['descripcion'],
                cant=cleaned_data['cant'],
                tipo_calculo=cleaned_data['tipo_calculo'],
                formula_calculo=cleaned_data['formula_calculo'],
                precio=cleaned_data['precio'],
            )
        else:
            # Si no cambió la clave, solo actualizar los demás campos
            update_data = {
                'descripcion': cleaned_data['descripcion'],
                'cant': cleaned_data['cant'],
                'tipo_calculo': cleaned_data['tipo_calculo'],
                'formula_calculo': cleaned_data['formula_calculo'],
                'precio': cleaned_data['precio'],
            }
            updated_rows = Accesorio.objects.filter(codigo=old_codigo, tipo=old_tipo).update(**update_data)
            if not updated_rows:
                raise Accesorio.DoesNotExist(f"{old_codigo} ({old_tipo})")


def _get_accesorio_from_request(request, codigo=None, tipo=None):
    resolved_codigo = codigo if codigo is not None else request.GET.get('codigo')
    resolved_tipo = tipo if tipo is not None else request.GET.get('tipo')

    if not resolved_codigo:
        raise Http404('Accesorio no especificado.')

    queryset = Accesorio.objects.filter(codigo=resolved_codigo)
    if resolved_tipo in (None, ''):
        accesorio = queryset.filter(Q(tipo='') | Q(tipo__isnull=True)).first()
        if accesorio is None:
            raise Http404(f'{resolved_codigo} (sin tipo)')
        return accesorio

    return get_object_or_404(queryset, tipo=resolved_tipo)


# ─── EXTRUSORAS ───────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_staff)
def extrusoras_config(request):
    allowed_sort_fields = {
        'nombre': ('nombre', 'id'),
        'estado': ('bloqueado', 'nombre', 'id'),
    }
    sort, dir_, ordering = _resolve_ordering(request, allowed_sort_fields, 'nombre')
    extrusoras = Extrusora.objects.exclude(bloqueado='Si').order_by(*ordering)
    return render(request, 'pricing/config/extrusoras.html', {
        'extrusoras': extrusoras,
        'sort': sort,
        'dir': dir_,
    })


@login_required
@user_passes_test(is_staff)
def extrusora_create(request):
    form = ExtrusoraForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        _guardar_nuevo_con_id(obj, Extrusora)
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
    allowed_sort_fields = {
        'nombre': ('nombre', 'id'),
        'extrusora': ('extrusora__nombre', 'nombre', 'id'),
        'estado': ('bloqueado', 'nombre', 'id'),
    }
    sort, dir_, ordering = _resolve_ordering(request, allowed_sort_fields, 'nombre')
    lineas = Linea.objects.select_related('extrusora').exclude(bloqueado='Si').order_by(*ordering)
    extrusoras = Extrusora.objects.exclude(bloqueado='Si')
    return render(request, 'pricing/config/lineas.html', {
        'lineas': lineas,
        'extrusoras': extrusoras,
        'sort': sort,
        'dir': dir_,
    })


@login_required
@user_passes_test(is_staff)
def linea_create(request):
    form = LineaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        _guardar_nuevo_con_id(obj, Linea)
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
    allowed_sort_fields = {
        'descripcion': ('descripcion', 'id'),
        'extrusora': ('extrusora__nombre', 'descripcion', 'id'),
        'linea': ('linea__nombre', 'descripcion', 'id'),
        'estado': ('bloqueado', 'descripcion', 'id'),
    }
    sort, dir_, ordering = _resolve_ordering(request, allowed_sort_fields, 'descripcion')
    productos = Producto.objects.select_related('linea', 'extrusora').exclude(bloqueado='Si').order_by(*ordering)
    lineas = Linea.objects.exclude(bloqueado='Si')
    return render(request, 'pricing/config/productos.html', {
        'productos': productos,
        'lineas': lineas,
        'sort': sort,
        'dir': dir_,
    })


@login_required
@user_passes_test(is_staff)
def producto_create(request):
    form = ProductoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        _guardar_nuevo_con_id(obj, Producto)
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
    allowed_sort_fields = {
        'descripcion': ('descripcion', 'id'),
        'extrusora': ('producto__extrusora__nombre', 'descripcion', 'id'),
        'linea': ('producto__linea__nombre', 'descripcion', 'id'),
        'producto': ('producto__descripcion', 'descripcion', 'id'),
        'estado': ('bloqueado', 'descripcion', 'id'),
    }
    sort, dir_, ordering = _resolve_ordering(request, allowed_sort_fields, 'descripcion')
    marcos = Marco.objects.select_related('producto', 'producto__extrusora', 'producto__linea').exclude(bloqueado='Si').order_by(*ordering)
    productos = Producto.objects.exclude(bloqueado='Si')
    return render(request, 'pricing/config/marcos.html', {
        'marcos': marcos,
        'productos': productos,
        'sort': sort,
        'dir': dir_,
    })


@login_required
@user_passes_test(is_staff)
def marco_create(request):
    form = MarcoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        _guardar_nuevo_con_id(obj, Marco)
        
        # Guardar fórmulas si existen
        if 'formula_cantidad_0' in request.POST:
            from .models import DespiecePerfilesMarco
            try:
                filas = []
                fila_incompleta = None
                index = 0
                while f'formula_cantidad_{index}' in request.POST:
                    variable = (request.POST.get(f'formula_variable_{index}') or '').strip()
                    operador = (request.POST.get(f'formula_operador_{index}') or '').strip()
                    valor = (request.POST.get(f'formula_valor_{index}') or '').strip()
                    cantidad = (request.POST.get(f'formula_cantidad_{index}') or '').strip()
                    angulo = (request.POST.get(f'formula_angulo_{index}') or '').strip()
                    perfil = (request.POST.get(f'formula_perfil_{index}') or '').strip()

                    if perfil and cantidad and valor:
                        filas.append({
                            'formula_cantidad': cantidad,
                            'formula_perfil': f"{variable} {operador} {valor}",
                            'angulo': angulo,
                            'perfil': perfil,
                        })
                    elif perfil or valor:
                        fila_incompleta = index + 1
                        break
                    index += 1
                if fila_incompleta:
                    messages.warning(request, f'Fórmulas NO guardadas: la fila {fila_incompleta} está incompleta.')
                else:
                    _reemplazar_filas_despiece(DespiecePerfilesMarco, 'marco', obj, filas)
            except Exception as e:
                messages.warning(request, f'No se pudieron guardar las fórmulas: {str(e)}')
        
        messages.success(request, 'Marco creado correctamente.')
        return redirect('config-marcos')
    return render(request, 'pricing/config/marco_form.html', {'form': form, 'titulo': 'Nuevo Marco', 'cancel_url': 'config-marcos'})


@login_required
@user_passes_test(is_staff)
def marco_edit(request, pk):
    import json as _json
    obj = get_object_or_404(Marco, pk=pk)
    form = MarcoForm(request.POST or None, instance=obj)

    from .models import DespiecePerfilesMarco, DespieceAccesoriosMarco
    formulas = []
    accesorios_marco = []
    try:
        formulas = list(DespiecePerfilesMarco.objects.filter(marco=obj))
        accesorios_marco = list(DespieceAccesoriosMarco.objects.filter(marco=obj))
    except:
        pass

    accesorios_marco_json = _json.dumps([
        {'accesorio': a.accesorio, 'obligatorio': a.obligatorio or 'No'}
        for a in accesorios_marco
    ])

    if request.method == 'POST':
        # AJAX: guardar solo accesorios
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and 'save_accesorios' in request.POST:
            try:
                filas = []
                index = 0
                while f'accesorio_{index}' in request.POST:
                    accesorio = request.POST.get(f'accesorio_{index}')
                    obligatorio = 'Si' if request.POST.get(f'obligatorio_{index}') == 'on' else 'No'
                    if accesorio:
                        filas.append({
                            'accesorio': accesorio,
                            'formula_cantidad': '1',
                            'obligatorio': obligatorio,
                        })
                    index += 1
                guardadas = _reemplazar_filas_despiece(DespieceAccesoriosMarco, 'marco', obj, filas)
                return JsonResponse({'ok': True, 'guardadas': guardadas})
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)

        if form.is_valid():
            form.save()

            # Eliminar fórmulas existentes y crear nuevas
            if 'formula_cantidad_0' in request.POST:
                try:
                    filas = []
                    fila_incompleta = None
                    index = 0
                    while f'formula_cantidad_{index}' in request.POST:
                        variable = (request.POST.get(f'formula_variable_{index}') or '').strip()
                        operador = (request.POST.get(f'formula_operador_{index}') or '').strip()
                        valor = (request.POST.get(f'formula_valor_{index}') or '').strip()
                        cantidad = (request.POST.get(f'formula_cantidad_{index}') or '').strip()
                        angulo = (request.POST.get(f'formula_angulo_{index}') or '').strip()
                        perfil = (request.POST.get(f'formula_perfil_{index}') or '').strip()

                        if perfil and cantidad and valor:
                            filas.append({
                                'formula_cantidad': cantidad,
                                'formula_perfil': f"{variable} {operador} {valor}",
                                'angulo': angulo,
                                'perfil': perfil,
                            })
                        elif perfil or valor:
                            fila_incompleta = index + 1
                            break
                        index += 1
                    if fila_incompleta:
                        messages.warning(request, f'Fórmulas NO guardadas: la fila {fila_incompleta} está incompleta. Se conservaron las fórmulas anteriores.')
                    else:
                        _reemplazar_filas_despiece(DespiecePerfilesMarco, 'marco', obj, filas)
                except Exception as e:
                    messages.warning(request, f'No se pudieron guardar las fórmulas: {str(e)}')

            # Guardar accesorios
            if 'accesorio_0' in request.POST:
                try:
                    filas = []
                    index = 0
                    while f'accesorio_{index}' in request.POST:
                        accesorio = request.POST.get(f'accesorio_{index}')
                        obligatorio = 'Si' if request.POST.get(f'obligatorio_{index}') == 'on' else 'No'
                        if accesorio:
                            filas.append({
                                'accesorio': accesorio,
                                'formula_cantidad': '1',
                                'obligatorio': obligatorio,
                            })
                        index += 1
                    _reemplazar_filas_despiece(DespieceAccesoriosMarco, 'marco', obj, filas)
                except Exception as e:
                    messages.warning(request, f'No se pudieron guardar los accesorios: {str(e)}')

            messages.success(request, 'Marco actualizado correctamente.')
            return redirect('config-marcos')

    return render(request, 'pricing/config/marco_form.html', {
        'form': form,
        'titulo': 'Editar Marco',
        'cancel_url': 'config-marcos',
        'object': obj,
        'formulas': formulas,
        'accesorios_marco_json': accesorios_marco_json,
    })


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
        filas = []
        index = 0
        while f'formula_cantidad_{index}' in request.POST:
            variable = (request.POST.get(f'formula_variable_{index}') or '').strip()
            operador = (request.POST.get(f'formula_operador_{index}') or '').strip()
            valor = (request.POST.get(f'formula_valor_{index}') or '').strip()
            cantidad = (request.POST.get(f'formula_cantidad_{index}') or '').strip()
            angulo = (request.POST.get(f'formula_angulo_{index}') or '').strip()
            perfil = (request.POST.get(f'formula_perfil_{index}') or '').strip()

            if perfil and cantidad and valor:
                filas.append({
                    'formula_cantidad': cantidad,
                    'formula_perfil': f"{variable} {operador} {valor}",
                    'angulo': angulo,
                    'perfil': perfil,
                })
            elif perfil or valor:
                # Fila a medio completar: no tocar nada para no perder datos
                return JsonResponse(
                    {'error': f'Fila {index + 1} incompleta (perfil, cantidad y valor son obligatorios). No se guardó nada.'},
                    status=400,
                )
            index += 1

        guardadas = _reemplazar_filas_despiece(DespiecePerfilesMarco, 'marco', obj, filas)
        return JsonResponse({'ok': True, 'guardadas': guardadas})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ─── HOJAS ────────────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_staff)
def hojas_config(request):
    allowed_sort_fields = {
        'descripcion': ('descripcion', 'id'),
        'extrusora': ('marco__producto__extrusora__nombre', 'descripcion', 'id'),
        'linea': ('marco__producto__linea__nombre', 'descripcion', 'id'),
        'producto': ('marco__producto__descripcion', 'descripcion', 'id'),
        'marco': ('marco__descripcion', 'descripcion', 'id'),
        'cantidad': ('cantidad', 'descripcion', 'id'),
        'estado': ('bloqueado', 'descripcion', 'id'),
    }
    sort, dir_, ordering = _resolve_ordering(request, allowed_sort_fields, 'descripcion')
    hojas = Hoja.objects.select_related(
        'marco',
        'marco__producto',
        'marco__producto__extrusora',
        'marco__producto__linea',
    ).exclude(bloqueado='Si').order_by(*ordering)
    marcos = Marco.objects.exclude(bloqueado='Si')
    return render(request, 'pricing/config/hojas.html', {
        'hojas': hojas,
        'marcos': marcos,
        'sort': sort,
        'dir': dir_,
    })


@login_required
@user_passes_test(is_staff)
def hoja_create(request):
    import json
    form = HojaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.cantidad = 1  # Valor por defecto
        _guardar_nuevo_con_id(obj, Hoja)
        messages.success(request, 'Hoja creada correctamente.')
        return redirect('config-hoja-edit', pk=obj.id)
    perfiles_json = json.dumps(list(Perfil.objects.exclude(bloqueado='Si').filter(tipo_perfil='Hojas').values('codigo', 'descripcion')))
    return render(request, 'pricing/config/hoja_form.html', {
        'form': form,
        'titulo': 'Nueva Hoja',
        'cancel_url': 'config-hojas',
        'es_edicion': False,
        'perfiles_json': perfiles_json,
        'accesorios_hoja_json': '[]',
    })


@login_required
@user_passes_test(is_staff)
def hoja_edit(request, pk):
    obj = get_object_or_404(Hoja, pk=pk)
    form = HojaForm(request.POST or None, instance=obj)

    from .models import DespiecePerfilesHoja, DespieceAccesoriosHoja, Vidrio, VidrioHoja
    import json

    formulas = []
    accesorios_hoja = []
    try:
        formulas = list(DespiecePerfilesHoja.objects.filter(hoja=obj))
        accesorios_hoja = list(DespieceAccesoriosHoja.objects.filter(hoja=obj))
    except:
        pass

    relaciones_vidrio = list(
        VidrioHoja.objects
        .filter(hoja_id=obj.id)
        .select_related('vidrio')
        .order_by('vidrio_id')
    )
    vidrios_relacionados = []
    vidrios_relacionados_ids = set()

    for relacion in relaciones_vidrio:
        vidrios_relacionados.append({
            'relacion_id': relacion.id,
            'vidrio_codigo': relacion.vidrio_id,
            'vidrio_descripcion': relacion.vidrio.descripcion or '',
            'rebaje_ancho': relacion.rebaje_ancho or relacion.vidrio.rebaje_ancho or '',
            'rebaje_alto': relacion.rebaje_alto or relacion.vidrio.rebaje_alto or '',
        })
        vidrios_relacionados_ids.add(relacion.vidrio_id)

    for vidrio in Vidrio.objects.filter(hoja_id=obj.id).order_by('codigo'):
        if vidrio.codigo in vidrios_relacionados_ids:
            continue
        vidrios_relacionados.append({
            'relacion_id': '',
            'vidrio_codigo': vidrio.codigo,
            'vidrio_descripcion': vidrio.descripcion or '',
            'rebaje_ancho': vidrio.rebaje_ancho or '',
            'rebaje_alto': vidrio.rebaje_alto or '',
        })

    perfiles = Perfil.objects.exclude(bloqueado='Si').filter(tipo_perfil='Hojas').values('codigo', 'descripcion')
    perfiles_json = json.dumps(list(perfiles))
    accesorios_hoja_json = json.dumps([
        {'accesorio': a.accesorio, 'obligatorio': a.obligatorio or 'No'}
        for a in accesorios_hoja
    ])

    if request.method == 'POST':
        # Si es una petición AJAX para guardar solo fórmulas o accesorios
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'HTTP_X_REQUESTED_WITH' in request.META:
            # Guardar fórmula de vidrio
            if 'save_vidrio_formula' in request.POST:
                if not vidrios_relacionados:
                    return JsonResponse({'error': 'No hay vidrio asociado a esta hoja'}, status=400)
                try:
                    relaciones_existentes = {
                        str(relacion.id): relacion
                        for relacion in VidrioHoja.objects.filter(hoja_id=obj.id)
                    }
                    guardadas = 0
                    index = 0

                    while f'vidrio_codigo_{index}' in request.POST:
                        vidrio_codigo = (request.POST.get(f'vidrio_codigo_{index}') or '').strip()
                        relacion_id = (request.POST.get(f'relacion_id_{index}') or '').strip()
                        rebaje_ancho = (request.POST.get(f'rebaje_ancho_{index}') or '').strip()
                        rebaje_alto = (request.POST.get(f'rebaje_alto_{index}') or '').strip()

                        if not vidrio_codigo:
                            index += 1
                            continue

                        if relacion_id:
                            relacion = relaciones_existentes.get(relacion_id)
                            if not relacion:
                                return JsonResponse({'error': f'No se encontró la relación de vidrio {vidrio_codigo}.'}, status=400)
                        else:
                            relacion, _ = VidrioHoja.objects.get_or_create(
                                hoja=obj,
                                vidrio_id=vidrio_codigo,
                            )

                        relacion.rebaje_ancho = rebaje_ancho
                        relacion.rebaje_alto = rebaje_alto
                        relacion.save(update_fields=['rebaje_ancho', 'rebaje_alto'])
                        guardadas += 1
                        index += 1

                    return JsonResponse({'ok': True, 'guardadas': guardadas})
                except Exception as e:
                    return JsonResponse({'error': str(e)}, status=500)

            # Guardar accesorios
            if 'save_accesorios' in request.POST:
                try:
                    accesorios_recibidos = [
                        key for key in request.POST.keys() if key.startswith('accesorio_')
                    ]
                    logger.warning(
                        "save_accesorios recibido hoja_id=%s filas=%s",
                        obj.id,
                        len(accesorios_recibidos),
                    )
                    filas = []
                    index = 0
                    while f'accesorio_{index}' in request.POST:
                        accesorio = request.POST.get(f'accesorio_{index}')
                        obligatorio = 'Si' if request.POST.get(f'obligatorio_{index}') == 'on' else 'No'

                        if accesorio:
                            filas.append({
                                'accesorio': accesorio,
                                'formula_cantidad': '1',
                                'obligatorio': obligatorio,
                            })
                        index += 1
                    guardadas = _reemplazar_filas_despiece(DespieceAccesoriosHoja, 'hoja', obj, filas)
                    logger.warning(
                        "save_accesorios guardado hoja_id=%s guardadas=%s",
                        obj.id,
                        guardadas,
                    )
                    return JsonResponse({'ok': True, 'guardadas': guardadas})
                except Exception as e:
                    logger.exception(
                        "Error en save_accesorios hoja_id=%s: %s",
                        obj.id,
                        str(e),
                    )
                    return JsonResponse({'error': str(e)}, status=500)
            
            # Guardar fórmulas
            try:
                filas = []
                index = 0
                while f'perfil_{index}' in request.POST:
                    perfil = (request.POST.get(f'perfil_{index}') or '').strip()
                    cantidad = (request.POST.get(f'cantidad_{index}') or '').strip()
                    formula = (request.POST.get(f'formula_{index}') or '').strip()
                    angulo = (request.POST.get(f'angulo_{index}') or '').strip()

                    if perfil and cantidad and formula:
                        filas.append({
                            'perfil': perfil,
                            'formula_cantidad': cantidad,
                            'formula_perfil': formula,
                            'angulo': angulo or '',
                        })
                    elif perfil or formula:
                        # Fila a medio completar: no tocar nada para no perder datos
                        return JsonResponse(
                            {'error': f'Fila {index + 1} incompleta (perfil, cantidad y fórmula son obligatorios). No se guardó nada.'},
                            status=400,
                        )
                    index += 1
                guardadas = _reemplazar_filas_despiece(DespiecePerfilesHoja, 'hoja', obj, filas)
                return JsonResponse({'ok': True, 'guardadas': guardadas})
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)
        
        # Guardado normal del formulario
        if form.is_valid():
            form.save()
            
            # Guardar fórmulas
            if 'perfil_0' in request.POST:
                try:
                    filas = []
                    fila_incompleta = None
                    index = 0
                    while f'perfil_{index}' in request.POST:
                        perfil = (request.POST.get(f'perfil_{index}') or '').strip()
                        cantidad = (request.POST.get(f'cantidad_{index}') or '').strip()
                        formula = (request.POST.get(f'formula_{index}') or '').strip()
                        angulo = (request.POST.get(f'angulo_{index}') or '').strip()

                        if perfil and cantidad and formula:
                            filas.append({
                                'perfil': perfil,
                                'formula_cantidad': cantidad,
                                'formula_perfil': formula,
                                'angulo': angulo or '',
                            })
                        elif perfil or formula:
                            fila_incompleta = index + 1
                            break
                        index += 1
                    if fila_incompleta:
                        messages.warning(request, f'Fórmulas NO guardadas: la fila {fila_incompleta} está incompleta. Se conservaron las fórmulas anteriores.')
                    else:
                        _reemplazar_filas_despiece(DespiecePerfilesHoja, 'hoja', obj, filas)
                except Exception as e:
                    messages.warning(request, f'No se pudieron guardar las fórmulas: {str(e)}')
            
            # Guardar accesorios
            if 'accesorio_0' in request.POST:
                try:
                    filas = []
                    index = 0
                    while f'accesorio_{index}' in request.POST:
                        accesorio = request.POST.get(f'accesorio_{index}')
                        obligatorio = 'Si' if f'obligatorio_{index}' in request.POST else 'No'

                        if accesorio:
                            filas.append({
                                'accesorio': accesorio,
                                'formula_cantidad': '1',
                                'obligatorio': obligatorio,
                            })
                        index += 1
                    _reemplazar_filas_despiece(DespieceAccesoriosHoja, 'hoja', obj, filas)
                except Exception as e:
                    messages.warning(request, f'No se pudieron guardar los accesorios: {str(e)}')

            # Guardar fórmulas de vidrio
            relacion_ids = request.POST.getlist('relacion_id')
            vidrio_codigos = request.POST.getlist('vidrio_codigo')
            rebaje_anchos = request.POST.getlist('rebaje_ancho')
            rebaje_altos = request.POST.getlist('rebaje_alto')
            if vidrio_codigos:
                try:
                    relaciones_existentes = {
                        str(r.id): r
                        for r in VidrioHoja.objects.filter(hoja_id=obj.id)
                    }
                    for i, vidrio_codigo in enumerate(vidrio_codigos):
                        vidrio_codigo = vidrio_codigo.strip()
                        if not vidrio_codigo:
                            continue
                        relacion_id = (relacion_ids[i] if i < len(relacion_ids) else '').strip()
                        rebaje_ancho = (rebaje_anchos[i] if i < len(rebaje_anchos) else '').strip()
                        rebaje_alto = (rebaje_altos[i] if i < len(rebaje_altos) else '').strip()
                        if relacion_id:
                            relacion = relaciones_existentes.get(relacion_id)
                            if relacion:
                                relacion.rebaje_ancho = rebaje_ancho
                                relacion.rebaje_alto = rebaje_alto
                                relacion.save(update_fields=['rebaje_ancho', 'rebaje_alto'])
                        else:
                            VidrioHoja.objects.filter(
                                hoja=obj, vidrio_id=vidrio_codigo
                            ).update(rebaje_ancho=rebaje_ancho, rebaje_alto=rebaje_alto)
                except Exception as e:
                    messages.warning(request, f'No se pudieron guardar las fórmulas de vidrio: {str(e)}')

            messages.success(request, 'Hoja actualizada correctamente.')
            return redirect('config-hojas')
    
    return render(request, 'pricing/config/hoja_form.html', {
        'form': form,
        'titulo': 'Editar Hoja',
        'cancel_url': 'config-hojas',
        'es_edicion': True,
        'object': obj,
        'hoja': obj,
        'formulas': formulas,
        'accesorios_hoja': accesorios_hoja,
        'perfiles': perfiles,
        'perfiles_json': perfiles_json,
        'accesorios_hoja_json': accesorios_hoja_json,
        'vidrios_relacionados': vidrios_relacionados,
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
    allowed_sort_fields = {
        'descripcion': ('descripcion', 'id'),
        'extrusora': ('hoja__marco__producto__extrusora__nombre', 'descripcion', 'id'),
        'linea': ('hoja__marco__producto__linea__nombre', 'descripcion', 'id'),
        'producto': ('hoja__marco__producto__descripcion', 'descripcion', 'id'),
        'marco': ('hoja__marco__descripcion', 'descripcion', 'id'),
        'hoja': ('hoja__descripcion', 'descripcion', 'id'),
        'estado': ('bloqueado', 'descripcion', 'id'),
    }
    sort, dir_, ordering = _resolve_ordering(request, allowed_sort_fields, 'descripcion')
    interiores = Interior.objects.select_related(
        'hoja',
        'hoja__marco',
        'hoja__marco__producto',
        'hoja__marco__producto__extrusora',
        'hoja__marco__producto__linea',
    ).exclude(bloqueado='Si').order_by(*ordering)
    hojas = Hoja.objects.exclude(bloqueado='Si')
    return render(request, 'pricing/config/interiores.html', {
        'interiores': interiores,
        'hojas': hojas,
        'sort': sort,
        'dir': dir_,
    })


@login_required
@user_passes_test(is_staff)
def interior_create(request):
    form = InteriorForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        _guardar_nuevo_con_id(obj, Interior)
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
    allowed_sort_fields = {
        'codigo': ('codigo',),
        'linea': ('linea__nombre', 'codigo'),
        'descripcion': ('descripcion', 'codigo'),
        'precio_kg': ('precio_kg', 'codigo'),
        'tipo': ('tipo_perfil', 'codigo'),
        'estado': ('bloqueado', 'codigo'),
    }
    sort, dir_, ordering = _resolve_ordering(request, allowed_sort_fields, 'codigo')
    selected_linea_id = request.GET.get('linea', '').strip()
    bulk_form = PerfilBulkPriceForm()

    if request.method == 'POST':
        bulk_form = PerfilBulkPriceForm(request.POST)
        codigos_seleccionados = request.POST.getlist('perfiles_seleccionados')

        if bulk_form.is_valid():
            if not codigos_seleccionados:
                messages.error(request, 'Selecciona al menos un perfil para actualizar el precio.')
            else:
                actualizados = _update_perfiles_precio(
                    codigos_seleccionados,
                    bulk_form.cleaned_data['precio_kg'],
                )
                if actualizados:
                    messages.success(request, f'Se actualizaron {actualizados} perfiles correctamente.')
                else:
                    messages.error(request, 'No se encontraron perfiles activos para actualizar.')
            return _redirect_to_perfiles_list(request)

    perfiles_qs = Perfil.objects.select_related('linea').exclude(bloqueado='Si')
    if selected_linea_id:
        perfiles_qs = perfiles_qs.filter(linea_id=selected_linea_id)

    perfiles = perfiles_qs.order_by(*ordering)[:200]
    lineas = Linea.objects.exclude(bloqueado='Si').order_by('nombre')

    return render(request, 'pricing/config/perfiles.html', {
        'perfiles': perfiles,
        'sort': sort,
        'dir': dir_,
        'bulk_form': bulk_form,
        'lineas': lineas,
        'selected_linea_id': selected_linea_id,
        'linea_query': f'&linea={selected_linea_id}' if selected_linea_id else '',
    })


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
    allowed_sort_fields = {
        'codigo': ('codigo', 'tipo'),
        'descripcion': ('descripcion', 'codigo', 'tipo'),
        'precio': ('precio', 'codigo', 'tipo'),
        'tipo': ('tipo', 'codigo'),
        'estado': ('bloqueado', 'codigo', 'tipo'),
    }
    sort, dir_, ordering = _resolve_ordering(request, allowed_sort_fields, 'codigo')
    accesorios = Accesorio.objects.exclude(bloqueado='Si').order_by(*ordering)[:200]
    return render(request, 'pricing/config/accesorios.html', {
        'accesorios': accesorios,
        'sort': sort,
        'dir': dir_,
    })


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
def accesorio_edit(request, codigo=None, tipo=None):
    obj = _get_accesorio_from_request(request, codigo=codigo, tipo=tipo)
    original_codigo = obj.codigo
    original_tipo = obj.tipo
    form = AccesorioEditForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        _save_accesorio_edit(original_codigo, original_tipo, form.cleaned_data)
        messages.success(request, 'Accesorio actualizado correctamente.')
        return redirect('config-accesorios')
    return render(request, 'pricing/config/accesorio_form.html', {'form': form, 'titulo': 'Editar Accesorio', 'cancel_url': 'config-accesorios', 'object': obj})


@login_required
@user_passes_test(is_staff)
def accesorio_delete(request, codigo=None, tipo=None):
    obj = _get_accesorio_from_request(request, codigo=codigo, tipo=tipo)
    if request.method == 'POST':
        Accesorio.objects.filter(codigo=obj.codigo, tipo=obj.tipo).update(bloqueado='Si')
        messages.success(request, 'Accesorio desactivado.')
    return redirect('config-accesorios')


# ─── VIDRIOS ──────────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_staff)
def vidrios_config(request):
    allowed_sort_fields = {
        'codigo': ('codigo',),
        'descripcion': ('descripcion', 'codigo'),
        'precio': ('precio', 'codigo'),
        'estado': ('bloqueado', 'codigo'),
    }
    sort, dir_, ordering = _resolve_ordering(request, allowed_sort_fields, 'codigo')
    vidrios = Vidrio.objects.exclude(bloqueado='Si').order_by(*ordering)
    return render(request, 'pricing/config/vidrios.html', {
        'vidrios': vidrios,
        'sort': sort,
        'dir': dir_,
    })


@login_required
@user_passes_test(is_staff)
def vidrio_create(request):
    form = VidrioCreateForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Vidrio creado correctamente.')
        return redirect('config-vidrio-edit', pk=form.instance.codigo)
    return render(request, 'pricing/config/vidrio_form.html', {'form': form, 'titulo': 'Nuevo Vidrio', 'cancel_url': 'config-vidrios'})


@login_required
@user_passes_test(is_staff)
def vidrio_edit(request, pk):
    import json as _json
    obj = get_object_or_404(Vidrio, pk=pk)
    form = VidrioEditForm(request.POST or None, instance=obj)

    from .models import VidrioHoja
    relaciones = list(VidrioHoja.objects.filter(vidrio=obj).select_related('hoja'))
    hojas = Hoja.objects.exclude(bloqueado='Si')

    if request.method == 'POST':
        # AJAX: guardar relaciones de hojas
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                hoja_ids = []
                hoja_ids_vistos = set()
                index = 0
                while f'hoja_{index}' in request.POST:
                    hoja_id_raw = (request.POST.get(f'hoja_{index}') or '').strip()
                    if hoja_id_raw:
                        try:
                            hoja_id = int(hoja_id_raw)
                        except ValueError:
                            return JsonResponse({'error': f'Hoja inválida: {hoja_id_raw}'}, status=400)

                        if hoja_id not in hoja_ids_vistos:
                            hoja_ids.append(hoja_id)
                            hoja_ids_vistos.add(hoja_id)
                    index += 1

                hojas_validas = set(Hoja.objects.filter(id__in=hoja_ids).values_list('id', flat=True))
                hojas_invalidas = [hoja_id for hoja_id in hoja_ids if hoja_id not in hojas_validas]
                if hojas_invalidas:
                    return JsonResponse({'error': f'Hay hojas inválidas en la selección: {", ".join(str(h) for h in hojas_invalidas)}'}, status=400)

                with transaction.atomic():
                    Vidrio.objects.select_for_update().get(pk=obj.pk)
                    VidrioHoja.objects.filter(vidrio=obj).delete()
                    VidrioHoja.objects.bulk_create([
                        VidrioHoja(vidrio=obj, hoja_id=hoja_id)
                        for hoja_id in hoja_ids
                    ])
                return JsonResponse({'ok': True, 'guardadas': len(hoja_ids)})
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)

        if form.is_valid():
            form.save()
            # Guardar relaciones de hojas
            hoja_ids_raw = request.POST.getlist('hoja')
            if hoja_ids_raw:
                try:
                    hoja_ids = []
                    hoja_ids_vistos = set()
                    for hoja_id_raw in hoja_ids_raw:
                        hoja_id_raw = hoja_id_raw.strip()
                        if hoja_id_raw:
                            hoja_id = int(hoja_id_raw)
                            if hoja_id not in hoja_ids_vistos:
                                hoja_ids.append(hoja_id)
                                hoja_ids_vistos.add(hoja_id)
                    with transaction.atomic():
                        VidrioHoja.objects.filter(vidrio=obj).delete()
                        VidrioHoja.objects.bulk_create([
                            VidrioHoja(vidrio=obj, hoja_id=hoja_id)
                            for hoja_id in hoja_ids
                        ])
                except Exception as e:
                    messages.warning(request, f'No se pudieron guardar las relaciones de hojas: {str(e)}')
            messages.success(request, 'Vidrio actualizado correctamente.')
            return redirect('config-vidrios')

    return render(request, 'pricing/config/vidrio_form.html', {
        'form': form,
        'titulo': 'Editar Vidrio',
        'cancel_url': 'config-vidrios',
        'object': obj,
        'relaciones': relaciones,
        'hojas': hojas,
    })


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
    allowed_sort_fields = {
        'descripcion': ('descripcion', 'id'),
        'precio_kg': ('precio_kg', 'descripcion', 'id'),
        'estado': ('bloqueado', 'descripcion', 'id'),
    }
    sort, dir_, ordering = _resolve_ordering(request, allowed_sort_fields, 'descripcion')
    tratamientos = Tratamiento.objects.exclude(bloqueado='Si').order_by(*ordering)
    return render(request, 'pricing/config/tratamientos.html', {
        'tratamientos': tratamientos,
        'sort': sort,
        'dir': dir_,
    })


@login_required
@user_passes_test(is_staff)
def tratamiento_create(request):
    form = TratamientoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        _guardar_nuevo_con_id(obj, Tratamiento)
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
