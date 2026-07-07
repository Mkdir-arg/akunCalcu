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


class DatosEmpresaForm(forms.Form):
    _INPUT = 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'

    empresa_nombre = forms.CharField(max_length=200, required=False, label='Nombre de la empresa',
                                     widget=forms.TextInput(attrs={'class': _INPUT}))
    empresa_direccion = forms.CharField(max_length=200, required=False, label='Dirección',
                                        widget=forms.TextInput(attrs={'class': _INPUT}))
    empresa_telefonos = forms.CharField(max_length=200, required=False, label='Teléfonos',
                                        widget=forms.TextInput(attrs={'class': _INPUT}))
    empresa_web = forms.CharField(max_length=200, required=False, label='Sitio web',
                                  widget=forms.TextInput(attrs={'class': _INPUT}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            datos = ConfiguracionGeneral.get_datos_empresa()
            for clave, valor in datos.items():
                self.fields[clave].initial = valor

    def guardar(self):
        descripciones = {
            'empresa_nombre': 'Nombre de la empresa (pie de documentos)',
            'empresa_direccion': 'Dirección de contacto (pie de documentos)',
            'empresa_telefonos': 'Teléfonos de contacto (pie de documentos)',
            'empresa_web': 'Sitio web (pie de documentos)',
        }
        for clave, descripcion in descripciones.items():
            ConfiguracionGeneral.set_valor(clave, self.cleaned_data.get(clave, ''), descripcion)
