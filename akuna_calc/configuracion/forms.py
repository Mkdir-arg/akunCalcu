from django import forms
from .models import ConfiguracionGeneral


class ValorHoraHombreForm(forms.Form):
    valor = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
        label='Valor por Hora Hombre',
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'step': '0.01',
            'placeholder': '0.00'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            valor_actual = ConfiguracionGeneral.get_valor_hora_hombre()
            self.fields['valor'].initial = valor_actual
