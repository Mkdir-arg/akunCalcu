from django import forms

from .models import NumeroAutorizado


class NumeroAutorizadoForm(forms.ModelForm):
    class Meta:
        model = NumeroAutorizado
        fields = ['numero', 'nombre', 'activo']
        widgets = {
            'numero': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': '5491155555555',
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Mati (opcional)',
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'h-5 w-5 text-blue-600 rounded border-gray-300 focus:ring-blue-500',
            }),
        }

    def clean_numero(self):
        numero = (self.cleaned_data.get('numero') or '').strip()
        if '@' in numero:
            numero = numero.split('@', 1)[0]
        if not numero.isdigit():
            raise forms.ValidationError("El número debe contener solo dígitos (sin '+', espacios ni símbolos).")
        return numero
