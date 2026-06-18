from django import forms
from django.utils import timezone
from datetime import timedelta

from comercial.models import Cliente
from .models import Presupuesto, ItemPresupuesto, ComentarioPresupuesto


class PresupuestoForm(forms.ModelForm):
    class Meta:
        model = Presupuesto
        fields = ['cliente', 'tipo_material', 'fecha_expiracion', 'notas']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'}),
            'tipo_material': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'}),
            'fecha_expiracion': forms.DateInput(
                attrs={'type': 'date', 'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'},
                format='%Y-%m-%d',
            ),
            'notas': forms.Textarea(attrs={'rows': 3, 'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cliente'].queryset = Cliente.objects.filter(deleted_at__isnull=True).order_by('apellido', 'nombre')
        self.fields['notas'].required = False
        if not self.instance.pk:
            self.fields['fecha_expiracion'].initial = (timezone.now() + timedelta(days=30)).strftime('%Y-%m-%d')


class PresupuestoConfiguracionObraForm(forms.ModelForm):
    class Meta:
        model = Presupuesto
        fields = ['tipo_obra', 'modalidad_sena', 'recargo_obra_nueva', 'recargo_renovacion_unitario', 'aplicar_iva']
        widgets = {
            'tipo_obra': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'}),
            'modalidad_sena': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'}),
            'recargo_obra_nueva': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'}),
            'recargo_renovacion_unitario': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'}),
            'aplicar_iva': forms.CheckboxInput(attrs={'class': 'w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tipo_obra'].required = True
        self.fields['tipo_obra'].empty_label = None
        self.fields['tipo_obra'].widget.choices = [('', 'Seleccionar...'), *Presupuesto.TIPO_OBRA_CHOICES]
        self.fields['modalidad_sena'].required = True
        self.fields['recargo_obra_nueva'].required = False
        self.fields['recargo_renovacion_unitario'].required = False

    def clean(self):
        cleaned_data = super().clean()
        tipo_obra = cleaned_data.get('tipo_obra')
        recargo_obra_nueva = cleaned_data.get('recargo_obra_nueva')
        recargo_renovacion_unitario = cleaned_data.get('recargo_renovacion_unitario')

        if not tipo_obra:
            raise forms.ValidationError('Debes seleccionar obra nueva o renovación antes de agregar ítems.')

        if tipo_obra == 'obra_nueva':
            if recargo_obra_nueva is None:
                self.add_error('recargo_obra_nueva', 'Ingresa el valor adicional de obra nueva.')
            cleaned_data['recargo_renovacion_unitario'] = 0

        if tipo_obra == 'renovacion':
            if recargo_renovacion_unitario is None:
                self.add_error('recargo_renovacion_unitario', 'Ingresa el valor fijo por unidad para renovación.')
            cleaned_data['recargo_obra_nueva'] = 0

        return cleaned_data


class ItemPresupuestoForm(forms.ModelForm):
    class Meta:
        model = ItemPresupuesto
        fields = ['descripcion', 'cantidad', 'ancho_mm', 'alto_mm', 'margen_porcentaje', 'precio_unitario', 'resultado_json']
        widgets = {
            'descripcion': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'}),
            'cantidad': forms.NumberInput(attrs={'min': 1, 'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'}),
            'ancho_mm': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'}),
            'alto_mm': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'}),
            'margen_porcentaje': forms.NumberInput(attrs={'step': '0.01', 'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'}),
            'precio_unitario': forms.NumberInput(attrs={'step': '0.01', 'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'}),
            'resultado_json': forms.HiddenInput(),
        }


class ComentarioForm(forms.ModelForm):
    class Meta:
        model = ComentarioPresupuesto
        fields = ['texto', 'prioridad']
        widgets = {
            'texto': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Escribir comentario...',
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 resize-none',
            }),
            'prioridad': forms.RadioSelect(attrs={
                'class': 'prioridad-radio',
            }),
        }
