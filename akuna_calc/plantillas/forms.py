from django import forms

from pricing.models import Linea

from .models import ProductoPlantilla, CampoPlantilla, OpcionalFabrica, FormulaOpcional
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
