from django import forms

from plantillas.models import PedidoFabrica
from .models import PlanCorte
from .services.plan import DESPUNTE_POR_DEFECTO, DISCO_POR_DEFECTO, ordenes_candidatas


def _corto(valor):
    return int(valor) if valor == int(valor) else valor


class ParametrosPlanForm(forms.Form):
    pedidos = forms.ModelMultipleChoiceField(queryset=PedidoFabrica.objects.none(), label='Pedidos')
    disco_mm = forms.DecimalField(label='Espesor del disco', min_value=0, max_value=50, decimal_places=1, localize=False)
    despunte_mm = forms.DecimalField(label='Despunte', min_value=0, max_value=500, decimal_places=1, localize=False)
    largo_barra_mm = forms.IntegerField(label='Largo de barra', required=False, min_value=1, max_value=20000)
    recorte_min_mm = forms.IntegerField(label='Guardar recortes desde', required=False, min_value=1, max_value=20000)
    pasar_a_corte = forms.BooleanField(label='Pasar las órdenes a la etapa Corte', required=False, initial=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ids = set(ordenes_candidatas().values_list('pedido_id', flat=True))
        self.fields['pedidos'].queryset = PedidoFabrica.objects.filter(pk__in=ids).order_by('numero')
        self.fields['pedidos'].error_messages['required'] = 'Elegí al menos un pedido.'
        ultimo = PlanCorte.objects.order_by('-numero').first()
        self.fields['disco_mm'].initial = _corto(ultimo.disco_mm) if ultimo else DISCO_POR_DEFECTO
        self.fields['despunte_mm'].initial = _corto(ultimo.despunte_mm) if ultimo else DESPUNTE_POR_DEFECTO

    def clean(self):
        datos = super().clean()
        if datos.get('despunte_mm') is not None and datos.get('largo_barra_mm') and datos['despunte_mm'] >= datos['largo_barra_mm']:
            self.add_error('despunte_mm', 'El despunte no puede ser mayor que la barra.')
        return datos

    def params(self):
        from .services.plan import normalizar_params

        d = self.cleaned_data
        return normalizar_params(d['disco_mm'], d['despunte_mm'], d.get('largo_barra_mm'), d.get('recorte_min_mm'))
