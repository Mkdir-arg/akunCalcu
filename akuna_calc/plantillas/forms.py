from django import forms
from .models import ProductoPlantilla, CampoPlantilla
from .services.formula_engine import FormulaEngine


class ProductoPlantillaForm(forms.ModelForm):
    class Meta:
        model = ProductoPlantilla
        fields = ['nombre', 'descripcion', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg'}),
            'descripcion': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border rounded-lg', 'rows': 3}),
        }


class CampoPlantillaForm(forms.ModelForm):
    class Meta:
        model = CampoPlantilla
        fields = ['nombre_visible', 'clave', 'tipo', 'unidad', 'modo', 'requerido', 'orden', 'formula', 'ayuda', 'opciones']
        widgets = {
            'nombre_visible': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg'}),
            'clave': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg', 'placeholder': 'ANCHO, ALTO, umb_dintel'}),
            'tipo': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg'}),
            'unidad': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg'}),
            'modo': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg'}),
            'orden': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg'}),
            'formula': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border rounded-lg font-mono', 'rows': 2, 'placeholder': 'ANCHO - 42'}),
            'ayuda': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg'}),
            'opciones': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg', 'placeholder': 'BALCON|VENTANA|PUERTA'}),
        }

    def __init__(self, *args, **kwargs):
        self.plantilla = kwargs.pop('plantilla', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        modo = cleaned_data.get('modo')
        formula = cleaned_data.get('formula')
        clave = cleaned_data.get('clave')

        if modo == 'CALCULADO':
            if not formula:
                raise forms.ValidationError({'formula': 'Los campos calculados requieren una fórmula'})
            
            # Validar solo sintaxis (strict=False permite variables futuras)
            valid, error = FormulaEngine.validate_formula(formula, set(), strict=False)
            if not valid:
                raise forms.ValidationError({'formula': error})

        # Validar clave única
        if self.plantilla and clave:
            existing = self.plantilla.campos.filter(clave=clave)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise forms.ValidationError({'clave': 'Ya existe un campo con esta clave'})

        return cleaned_data
