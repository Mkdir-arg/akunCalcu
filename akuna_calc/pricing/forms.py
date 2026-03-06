from django import forms
from .models import Extrusora, Linea, Producto, Marco, Hoja, Interior, Perfil, Accesorio, Vidrio, Tratamiento

_input_class = "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
_select_class = "w-full px-4 py-2 border border-gray-300 rounded-lg"


class ExtrusoraForm(forms.ModelForm):
    class Meta:
        model = Extrusora
        fields = ['nombre']
        widgets = {'nombre': forms.TextInput(attrs={'class': _input_class})}


class LineaForm(forms.ModelForm):
    class Meta:
        model = Linea
        fields = ['extrusora', 'nombre']
        widgets = {
            'extrusora': forms.Select(attrs={'class': _select_class}),
            'nombre': forms.TextInput(attrs={'class': _input_class}),
        }


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['extrusora', 'linea', 'descripcion']
        labels = {
            'descripcion': 'Nombre',
        }
        widgets = {
            'extrusora': forms.Select(attrs={'class': _select_class}),
            'linea': forms.Select(attrs={'class': _select_class}),
            'descripcion': forms.TextInput(attrs={'class': _input_class}),
        }


class MarcoForm(forms.ModelForm):
    extrusora = forms.ModelChoiceField(
        queryset=Extrusora.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': _select_class, 'disabled': 'disabled'}),
        label='Extrusora'
    )
    linea = forms.ModelChoiceField(
        queryset=Linea.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': _select_class, 'disabled': 'disabled'}),
        label='Línea'
    )
    
    class Meta:
        model = Marco
        fields = ['extrusora', 'linea', 'producto', 'descripcion']
        labels = {
            'descripcion': 'Nombre',
        }
        widgets = {
            'producto': forms.Select(attrs={'class': _select_class}),
            'descripcion': forms.TextInput(attrs={'class': _input_class}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.producto:
            self.fields['extrusora'].initial = self.instance.producto.extrusora
            self.fields['linea'].initial = self.instance.producto.linea


class HojaForm(forms.ModelForm):
    extrusora = forms.ModelChoiceField(
        queryset=Extrusora.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': _select_class, 'disabled': 'disabled'}),
        label='Extrusora'
    )
    linea = forms.ModelChoiceField(
        queryset=Linea.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': _select_class, 'disabled': 'disabled'}),
        label='Línea'
    )
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': _select_class, 'disabled': 'disabled'}),
        label='Producto'
    )
    
    class Meta:
        model = Hoja
        fields = ['extrusora', 'linea', 'producto', 'marco', 'descripcion', 'cantidad']
        labels = {
            'descripcion': 'Nombre',
        }
        widgets = {
            'marco': forms.Select(attrs={'class': _select_class}),
            'descripcion': forms.TextInput(attrs={'class': _input_class}),
            'cantidad': forms.NumberInput(attrs={'class': _input_class}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.marco:
            self.fields['extrusora'].initial = self.instance.marco.producto.extrusora
            self.fields['linea'].initial = self.instance.marco.producto.linea
            self.fields['producto'].initial = self.instance.marco.producto


class InteriorForm(forms.ModelForm):
    extrusora = forms.ModelChoiceField(
        queryset=Extrusora.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': _select_class, 'disabled': 'disabled'}),
        label='Extrusora'
    )
    linea = forms.ModelChoiceField(
        queryset=Linea.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': _select_class, 'disabled': 'disabled'}),
        label='Línea'
    )
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': _select_class, 'disabled': 'disabled'}),
        label='Producto'
    )
    marco = forms.ModelChoiceField(
        queryset=Marco.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': _select_class, 'disabled': 'disabled'}),
        label='Marco'
    )
    
    class Meta:
        model = Interior
        fields = ['extrusora', 'linea', 'producto', 'marco', 'hoja', 'descripcion']
        labels = {
            'descripcion': 'Nombre',
        }
        widgets = {
            'hoja': forms.Select(attrs={'class': _select_class}),
            'descripcion': forms.TextInput(attrs={'class': _input_class}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.hoja:
            self.fields['extrusora'].initial = self.instance.hoja.marco.producto.extrusora
            self.fields['linea'].initial = self.instance.hoja.marco.producto.linea
            self.fields['producto'].initial = self.instance.hoja.marco.producto
            self.fields['marco'].initial = self.instance.hoja.marco


class PerfilCreateForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['codigo', 'descripcion', 'peso_metro', 'precio_kg']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': _input_class}),
            'descripcion': forms.TextInput(attrs={'class': _input_class}),
            'peso_metro': forms.NumberInput(attrs={'class': _input_class, 'step': '0.001'}),
            'precio_kg': forms.NumberInput(attrs={'class': _input_class, 'step': '0.01'}),
        }


class PerfilEditForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['descripcion', 'peso_metro', 'precio_kg']
        widgets = {
            'descripcion': forms.TextInput(attrs={'class': _input_class}),
            'peso_metro': forms.NumberInput(attrs={'class': _input_class, 'step': '0.001'}),
            'precio_kg': forms.NumberInput(attrs={'class': _input_class, 'step': '0.01'}),
        }


class AccesorioCreateForm(forms.ModelForm):
    class Meta:
        model = Accesorio
        fields = ['codigo', 'descripcion', 'precio']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': _input_class}),
            'descripcion': forms.TextInput(attrs={'class': _input_class}),
            'precio': forms.NumberInput(attrs={'class': _input_class, 'step': '0.01'}),
        }


class AccesorioEditForm(forms.ModelForm):
    class Meta:
        model = Accesorio
        fields = ['descripcion', 'precio']
        widgets = {
            'descripcion': forms.TextInput(attrs={'class': _input_class}),
            'precio': forms.NumberInput(attrs={'class': _input_class, 'step': '0.01'}),
        }


class VidrioCreateForm(forms.ModelForm):
    class Meta:
        model = Vidrio
        fields = ['codigo', 'descripcion', 'precio']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': _input_class}),
            'descripcion': forms.TextInput(attrs={'class': _input_class}),
            'precio': forms.NumberInput(attrs={'class': _input_class, 'step': '0.01'}),
        }


class VidrioEditForm(forms.ModelForm):
    class Meta:
        model = Vidrio
        fields = ['descripcion', 'precio']
        widgets = {
            'descripcion': forms.TextInput(attrs={'class': _input_class}),
            'precio': forms.NumberInput(attrs={'class': _input_class, 'step': '0.01'}),
        }


class TratamientoForm(forms.ModelForm):
    class Meta:
        model = Tratamiento
        fields = ['descripcion', 'precio_kg']
        widgets = {
            'descripcion': forms.TextInput(attrs={'class': _input_class}),
            'precio_kg': forms.NumberInput(attrs={'class': _input_class, 'step': '0.01'}),
        }
