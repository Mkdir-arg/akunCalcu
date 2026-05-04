from django import forms
from django.utils import timezone
from datetime import timedelta

from comercial.models import Cliente, Venta
from .models import Presupuesto, ItemPresupuesto, ComentarioPresupuesto


class PresupuestoForm(forms.ModelForm):
    class Meta:
        model = Presupuesto
        fields = ['cliente', 'fecha_expiracion', 'notas']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'}),
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
        fields = ['texto']
        widgets = {
            'texto': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Escribir comentario...',
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 resize-none',
            }),
        }


class PresupuestoVentaForm(forms.ModelForm):
    class Meta:
        model = Presupuesto
        fields = ['venta']
        widgets = {
            'venta': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500'}),
        }

    def __init__(self, *args, cliente=None, **kwargs):
        super().__init__(*args, **kwargs)
        queryset = Venta.objects.filter(pk__in=[])
        if cliente is not None:
            queryset = Venta.objects.filter(
                cliente=cliente,
                deleted_at__isnull=True,
                con_factura=True,
            ).order_by('-created_at')

        self.fields['venta'].queryset = queryset
        self.fields['venta'].required = False
        self.fields['venta'].empty_label = 'Sin venta asociada'
