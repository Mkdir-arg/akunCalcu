from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import ConfiguracionGeneral
from .forms import ValorHoraHombreForm


def is_staff(user):
    return user.is_staff


@login_required
@user_passes_test(is_staff)
def configuracion_general(request):
    valor_hora = ConfiguracionGeneral.get_valor_hora_hombre()
    return render(request, 'configuracion/general.html', {
        'valor_hora_hombre': valor_hora
    })


@login_required
@user_passes_test(is_staff)
def editar_valor_hora_hombre(request):
    if request.method == 'POST':
        form = ValorHoraHombreForm(request.POST)
        if form.is_valid():
            valor = form.cleaned_data['valor']
            ConfiguracionGeneral.set_valor_hora_hombre(valor)
            messages.success(request, f'Valor de hora hombre actualizado a ${valor}')
            return redirect('configuracion-general')
    else:
        form = ValorHoraHombreForm()
    
    return render(request, 'configuracion/valor_hora_form.html', {
        'form': form,
        'titulo': 'Configurar Valor Hora Hombre'
    })
