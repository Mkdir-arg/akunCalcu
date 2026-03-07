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
        widget=forms.Select(attrs={'class': _select_class}),
        label='Extrusora'
    )
    linea = forms.ModelChoiceField(
        queryset=Linea.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': _select_class}),
        label='Línea'
    )
    
    class Meta:
        model = Marco
        fields = ['producto', 'descripcion']
        labels = {
            'descripcion': 'Nombre',
        }
        widgets = {
            'producto': forms.Select(attrs={'class': _select_class}),
            'descripcion': forms.TextInput(attrs={'class': _input_class}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.order_fields(['extrusora', 'linea', 'producto', 'descripcion'])
        
        if self.instance and self.instance.pk and self.instance.producto:
            self.fields['extrusora'].initial = self.instance.producto.extrusora
            self.fields['linea'].initial = self.instance.producto.linea


class HojaForm(forms.ModelForm):
    extrusora = forms.ModelChoiceField(
        queryset=Extrusora.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': _select_class}),
        label='Extrusora'
    )
    linea = forms.ModelChoiceField(
        queryset=Linea.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': _select_class}),
        label='Línea'
    )
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': _select_class}),
        label='Producto'
    )
    
    class Meta:
        model = Hoja
        fields = ['marco', 'descripcion', 'cantidad']
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
        self.fields['marco'].queryset = Marco.objects.filter(bloqueado__isnull=True) | Marco.objects.filter(bloqueado='No')
        self.order_fields(['extrusora', 'linea', 'producto', 'marco', 'descripcion', 'cantidad'])
        
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
        fields = ['hoja', 'descripcion']
        labels = {
            'descripcion': 'Nombre',
        }
        widgets = {
            'hoja': forms.Select(attrs={'class': _select_class}),
            'descripcion': forms.TextInput(attrs={'class': _input_class}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.order_fields(['extrusora', 'linea', 'producto', 'marco', 'hoja', 'descripcion'])
        
        if self.instance and self.instance.pk and self.instance.hoja:
            self.fields['extrusora'].initial = self.instance.hoja.marco.producto.extrusora
            self.fields['linea'].initial = self.instance.hoja.marco.producto.linea
            self.fields['producto'].initial = self.instance.hoja.marco.producto
            self.fields['marco'].initial = self.instance.hoja.marco


class PerfilCreateForm(forms.ModelForm):
    MONEDA_CHOICES = [
        (1, 'Peso'),
        (2, 'Dólar'),
    ]
    
    TIPO_PERFIL_CHOICES = [
        ('Marco', 'Marco'),
        ('Hojas', 'Hojas'),
    ]
    
    linea_id = forms.IntegerField(
        widget=forms.Select(attrs={'class': _select_class}, choices=[]),
        label='Línea',
        required=False
    )
    
    moneda = forms.ChoiceField(
        choices=MONEDA_CHOICES,
        widget=forms.Select(attrs={'class': _select_class}),
        label='Moneda'
    )
    
    tipo_perfil = forms.ChoiceField(
        choices=[('', '---------')] + TIPO_PERFIL_CHOICES,
        widget=forms.Select(attrs={'class': _select_class}),
        label='Tipo de Perfil',
        required=False
    )
    
    class Meta:
        model = Perfil
        fields = ['codigo', 'linea_id', 'descripcion', 'peso_metro', 'long_tira', 'precio_kg', 'moneda', 'tipo_perfil']
        labels = {
            'linea_id': 'Línea',
            'peso_metro': 'KG x Metro',
            'long_tira': 'Largo',
            'precio_kg': 'Precio x KG',
        }
        widgets = {
            'codigo': forms.TextInput(attrs={'class': _input_class}),
            'descripcion': forms.TextInput(attrs={'class': _input_class}),
            'peso_metro': forms.NumberInput(attrs={'class': _input_class, 'step': '0.001'}),
            'long_tira': forms.NumberInput(attrs={'class': _input_class}),
            'precio_kg': forms.NumberInput(attrs={'class': _input_class, 'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        lineas = [(l.id, str(l)) for l in Linea.objects.all()]
        self.fields['linea_id'].widget.choices = [('', '---------')] + lineas


class PerfilEditForm(forms.ModelForm):
    MONEDA_CHOICES = [
        (1, 'Peso'),
        (2, 'Dólar'),
    ]
    
    TIPO_PERFIL_CHOICES = [
        ('Marco', 'Marco'),
        ('Hojas', 'Hojas'),
    ]
    
    linea_id = forms.IntegerField(
        widget=forms.Select(attrs={'class': _select_class}, choices=[]),
        label='Línea',
        required=False
    )
    
    moneda = forms.ChoiceField(
        choices=MONEDA_CHOICES,
        widget=forms.Select(attrs={'class': _select_class}),
        label='Moneda'
    )
    
    tipo_perfil = forms.ChoiceField(
        choices=[('', '---------')] + TIPO_PERFIL_CHOICES,
        widget=forms.Select(attrs={'class': _select_class}),
        label='Tipo de Perfil',
        required=False
    )
    
    class Meta:
        model = Perfil
        fields = ['linea_id', 'descripcion', 'peso_metro', 'long_tira', 'precio_kg', 'moneda', 'tipo_perfil']
        labels = {
            'linea_id': 'Línea',
            'peso_metro': 'KG x Metro',
            'long_tira': 'Largo',
            'precio_kg': 'Precio x KG',
        }
        widgets = {
            'descripcion': forms.TextInput(attrs={'class': _input_class}),
            'peso_metro': forms.NumberInput(attrs={'class': _input_class, 'step': '0.001'}),
            'long_tira': forms.NumberInput(attrs={'class': _input_class}),
            'precio_kg': forms.NumberInput(attrs={'class': _input_class, 'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        lineas = [(l.id, str(l)) for l in Linea.objects.all()]
        self.fields['linea_id'].widget.choices = [('', '---------')] + lineas


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
    from productos.models import Producto as ProductoComercial
    
    producto_id = forms.ModelChoiceField(
        queryset=ProductoComercial.objects.filter(activo=True, categoria='vidrios'),
        widget=forms.Select(attrs={'class': _select_class}),
        label='Producto',
        required=False
    )
    
    hoja_id = forms.IntegerField(
        widget=forms.Select(attrs={'class': _select_class}, choices=[]),
        label='Hoja',
        required=False
    )
    
    rebaje_ancho = forms.IntegerField(
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={'class': _input_class, 'placeholder': '0'}),
        label='Rebaje Ancho (mm)'
    )
    
    rebaje_alto = forms.IntegerField(
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={'class': _input_class, 'placeholder': '0'}),
        label='Rebaje Alto (mm)'
    )
    
    class Meta:
        model = Vidrio
        fields = ['codigo', 'producto_id', 'hoja_id', 'descripcion', 'rebaje_ancho', 'rebaje_alto']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': _input_class}),
            'descripcion': forms.TextInput(attrs={'class': _input_class}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        hojas = [(h.id, str(h)) for h in Hoja.objects.all()]
        self.fields['hoja_id'].widget.choices = [('', '---------')] + hojas


class VidrioEditForm(forms.ModelForm):
    from productos.models import Producto as ProductoComercial
    
    producto_id = forms.ModelChoiceField(
        queryset=ProductoComercial.objects.filter(activo=True, categoria='vidrios'),
        widget=forms.Select(attrs={'class': _select_class}),
        label='Producto',
        required=False
    )
    
    hoja_id = forms.IntegerField(
        widget=forms.Select(attrs={'class': _select_class}, choices=[]),
        label='Hoja',
        required=False
    )
    
    rebaje_ancho = forms.IntegerField(
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={'class': _input_class, 'placeholder': '0'}),
        label='Rebaje Ancho (mm)'
    )
    
    rebaje_alto = forms.IntegerField(
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={'class': _input_class, 'placeholder': '0'}),
        label='Rebaje Alto (mm)'
    )
    
    class Meta:
        model = Vidrio
        fields = ['producto_id', 'hoja_id', 'descripcion', 'rebaje_ancho', 'rebaje_alto']
        widgets = {
            'descripcion': forms.TextInput(attrs={'class': _input_class}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        hojas = [(h.id, str(h)) for h in Hoja.objects.all()]
        self.fields['hoja_id'].widget.choices = [('', '---------')] + hojas


class TratamientoForm(forms.ModelForm):
    class Meta:
        model = Tratamiento
        fields = ['descripcion', 'precio_kg']
        widgets = {
            'descripcion': forms.TextInput(attrs={'class': _input_class}),
            'precio_kg': forms.NumberInput(attrs={'class': _input_class, 'step': '0.01'}),
        }
