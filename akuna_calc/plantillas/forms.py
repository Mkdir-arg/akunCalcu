from django import forms

from pricing.models import Linea

from .models import OpcionalFabrica, OrdenFabricacion


_INPUT = 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500'


class OrdenFabricacionForm(forms.ModelForm):
    class Meta:
        model = OrdenFabricacion
        fields = [
            'fecha_comprometida', 'atendido_por', 'medicion_por',
            'cliente_nombre', 'cliente_domicilio', 'cliente_piso', 'cliente_depto',
            'cliente_localidad', 'cliente_mail', 'cliente_telefono',
            'tipo_abertura', 'linea', 'color',
            'mosquitero', 'mosquitero_modelo', 'travesano', 'tipo_marco', 'marco_desarmado',
            'umbral_transitable', 'premarco', 'guia_persiana', 'tipo_guia', 'tapacinta',
            'lado', 'modelo_hoja', 'travesano_divisor', 'altura_travesano', 'cantidad_hojas',
            'tipo_vidrio', 'contramarco', 'modelo_contramarco', 'tipo_trabajo', 'altura_trabajo',
            'estructura', 'nota',
        ]
        widgets = {
            'fecha_comprometida': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': _INPUT}),
            'estructura': forms.Textarea(attrs={'rows': 2, 'class': _INPUT}),
            'nota': forms.Textarea(attrs={'rows': 6, 'class': _INPUT}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fecha_comprometida'].input_formats = ['%Y-%m-%d', '%d/%m/%Y']
        for name, field in self.fields.items():
            field.required = False
            if name not in self.Meta.widgets:
                field.widget.attrs.setdefault('class', _INPUT)


class OpcionalFabricaForm(forms.ModelForm):
    linea_id = forms.TypedChoiceField(
        required=False,
        coerce=int,
        empty_value=None,
        label='Línea',
        widget=forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg'})
    )

    class Meta:
        model = OpcionalFabrica
        fields = ['codigo', 'nombre', 'tipo', 'linea_id', 'precio_m2', 'descripcion', 'activo']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg', 'placeholder': 'OPC-001'}),
            'nombre': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg'}),
            'tipo': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg'}),
            'precio_m2': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg', 'step': '0.01', 'min': '0'}),
            'descripcion': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border rounded-lg', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        choices = [('', 'Seleccionar línea...')]
        try:
            lineas = Linea.objects.exclude(bloqueado='Si').order_by('nombre')
            choices.extend((linea.id, str(linea)) for linea in lineas)
        except Exception:
            # In test environments the legacy table may be unavailable.
            pass

        self.fields['linea_id'].choices = choices

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        linea_id = cleaned_data.get('linea_id')

        if tipo == 'premarco' and not linea_id:
            self.add_error('linea_id', 'La línea es obligatoria para un opcional de tipo Premarco.')

        if tipo != 'premarco':
            cleaned_data['linea_id'] = None

        if tipo != 'mosquitero':
            cleaned_data['precio_m2'] = 0

        return cleaned_data
