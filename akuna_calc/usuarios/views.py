from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.contrib import messages
from .forms import UserCreateForm, UserUpdateForm

User = get_user_model()

def is_staff(user):
    return user.is_staff

@login_required
@user_passes_test(is_staff)
def user_list(request):
    users = User.objects.filter(is_active=True).order_by('username')
    return render(request, 'usuarios/user_list.html', {'users': users})

@login_required
@user_passes_test(is_staff)
def user_create(request):
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuario creado exitosamente.')
            return redirect('user_list')
    else:
        form = UserCreateForm()
    return render(request, 'usuarios/user_form.html', {'form': form, 'title': 'Nuevo Usuario'})

@login_required
@user_passes_test(is_staff)
def user_update(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuario actualizado exitosamente.')
            return redirect('user_list')
    else:
        form = UserUpdateForm(instance=user)
    return render(request, 'usuarios/user_form.html', {'form': form, 'title': 'Editar Usuario'})

@login_required
@user_passes_test(is_staff)
def user_toggle(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.is_active = not user.is_active
    user.save()
    status = 'activado' if user.is_active else 'desactivado'
    messages.success(request, f'Usuario {status} exitosamente.')
    return redirect('user_list')
