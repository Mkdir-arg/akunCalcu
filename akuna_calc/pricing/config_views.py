"""Vistas de configuración para ABMs de pricing."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Extrusora, Linea, Producto, Marco, Hoja, Interior, Perfil, Accesorio, Vidrio, Tratamiento


def is_staff(user):
    return user.is_staff


@login_required
@user_passes_test(is_staff)
def extrusoras_config(request):
    extrusoras = Extrusora.objects.all()
    return render(request, 'pricing/config/extrusoras.html', {'extrusoras': extrusoras})


@login_required
@user_passes_test(is_staff)
def lineas_config(request):
    lineas = Linea.objects.select_related('extrusora').all()
    extrusoras = Extrusora.objects.all()
    return render(request, 'pricing/config/lineas.html', {'lineas': lineas, 'extrusoras': extrusoras})


@login_required
@user_passes_test(is_staff)
def productos_config(request):
    productos = Producto.objects.select_related('linea', 'extrusora').all()
    lineas = Linea.objects.all()
    return render(request, 'pricing/config/productos.html', {'productos': productos, 'lineas': lineas})


@login_required
@user_passes_test(is_staff)
def marcos_config(request):
    marcos = Marco.objects.select_related('producto').all()
    productos = Producto.objects.all()
    return render(request, 'pricing/config/marcos.html', {'marcos': marcos, 'productos': productos})


@login_required
@user_passes_test(is_staff)
def hojas_config(request):
    hojas = Hoja.objects.select_related('marco').all()
    marcos = Marco.objects.all()
    return render(request, 'pricing/config/hojas.html', {'hojas': hojas, 'marcos': marcos})


@login_required
@user_passes_test(is_staff)
def interiores_config(request):
    interiores = Interior.objects.select_related('hoja').all()
    hojas = Hoja.objects.all()
    return render(request, 'pricing/config/interiores.html', {'interiores': interiores, 'hojas': hojas})


@login_required
@user_passes_test(is_staff)
def perfiles_config(request):
    perfiles = Perfil.objects.all()[:100]  # Limitar para performance
    return render(request, 'pricing/config/perfiles.html', {'perfiles': perfiles})


@login_required
@user_passes_test(is_staff)
def accesorios_config(request):
    accesorios = Accesorio.objects.all()[:100]
    return render(request, 'pricing/config/accesorios.html', {'accesorios': accesorios})


@login_required
@user_passes_test(is_staff)
def vidrios_config(request):
    vidrios = Vidrio.objects.all()
    return render(request, 'pricing/config/vidrios.html', {'vidrios': vidrios})


@login_required
@user_passes_test(is_staff)
def tratamientos_config(request):
    tratamientos = Tratamiento.objects.all()
    return render(request, 'pricing/config/tratamientos.html', {'tratamientos': tratamientos})
