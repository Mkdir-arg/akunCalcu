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
        fields = ['extrusora', 'linea', 'descripcion', 'cantidad_hojas', 'horas_hombre']
        labels = {
            'descripcion': 'Nombre',
            'cantidad_hojas': 'Cantidad de Hojas',
            'horas_hombre': 'Horas Hombre',
        }
        widgets = {
            'extrusora': forms.Select(attrs={'class': _select_class + ' no-select2'}),
            'linea': forms.Select(attrs={'class': _select_class + ' no-select2'}),
            'descripcion': forms.TextInput(attrs={'class': _input_class}),
            'cantidad_hojas': forms.NumberInput(attrs={'class': _input_class, 'value': '1'}),
            'horas_hombre': forms.NumberInput(attrs={'class': _input_class, 'step': '0.1', 'value': '0'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.extrusora:
            self.fields['linea'].queryset = Linea.objects.filter(extrusora=self.instance.extrusora)
        elif self.data:
            ext_id = self.data.get('extrusora')
            self.fields['linea'].queryset = Linea.objects.filter(extrusora_id=ext_id) if ext_id else Linea.objects.none()
        else:
            self.fields['linea'].queryset = Linea.objects.none()


class MarcoForm(forms.ModelForm):
    extrusora = forms.ModelChoiceField(
        queryset=Extrusora.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': _select_class + ' no-select2'}),
        label='Extrusora'
    )
    linea = forms.ModelChoiceField(
        queryset=Linea.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': _select_class + ' no-select2'}),
        label='Línea'
    )
    
    class Meta:
        model = Marco
        fields = ['producto', 'descripcion']
        labels = {
            'descripcion': 'Nombre',
        }
        widgets = {
            'producto': forms.Select(attrs={'class': _select_class + ' no-select2'}),
            'descripcion': forms.TextInput(attrs={'class': _input_class}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.order_fields(['extrusora', 'linea', 'producto', 'descripcion'])

        if self.instance and self.instance.pk and self.instance.producto:
            self.fields['extrusora'].initial = self.instance.producto.extrusora
            self.fields['linea'].queryset = Linea.objects.filter(extrusora=self.instance.producto.extrusora)
            self.fields['linea'].initial = self.instance.producto.linea
            self.fields['producto'].queryset = Producto.objects.filter(linea=self.instance.producto.linea)
        elif self.data:
            ext_id = self.data.get('extrusora')
            linea_id = self.data.get('linea')
            self.fields['linea'].queryset = Linea.objects.filter(extrusora_id=ext_id) if ext_id else Linea.objects.none()
            self.fields['producto'].queryset = Producto.objects.filter(linea_id=linea_id) if linea_id else Producto.objects.none()
        else:
            self.fields['linea'].queryset = Linea.objects.none()
            self.fields['producto'].queryset = Producto.objects.none()


class HojaForm(forms.ModelForm):
    extrusora = forms.ModelChoiceField(
        queryset=Extrusora.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': _select_class + ' no-select2'}),
        label='Extrusora'
    )
    linea = forms.ModelChoiceField(
        queryset=Linea.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': _select_class + ' no-select2'}),
        label='Línea'
    )
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': _select_class + ' no-select2'}),
        label='Producto'
    )
    
    class Meta:
        model = Hoja
        fields = ['marco', 'descripcion', 'cantidad']
        labels = {
            'descripcion': 'Nombre',
        }
        widgets = {
            'marco': forms.Select(attrs={'class': _select_class + ' no-select2'}),
            'descripcion': forms.TextInput(attrs={'class': _input_class}),
            'cantidad': forms.NumberInput(attrs={'class': _input_class}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.order_fields(['extrusora', 'linea', 'producto', 'marco', 'descripcion', 'cantidad'])

        if self.instance and self.instance.pk and self.instance.marco:
            self.fields['extrusora'].initial = self.instance.marco.producto.extrusora
            self.fields['linea'].queryset = Linea.objects.filter(extrusora=self.instance.marco.producto.extrusora)
            self.fields['linea'].initial = self.instance.marco.producto.linea
            self.fields['producto'].queryset = Producto.objects.filter(linea=self.instance.marco.producto.linea)
            self.fields['producto'].initial = self.instance.marco.producto
            self.fields['marco'].queryset = Marco.objects.filter(producto=self.instance.marco.producto)
        elif self.data:
            ext_id = self.data.get('extrusora')
            linea_id = self.data.get('linea')
            producto_id = self.data.get('producto')
            self.fields['linea'].queryset = Linea.objects.filter(extrusora_id=ext_id) if ext_id else Linea.objects.none()
            self.fields['producto'].queryset = Producto.objects.filter(linea_id=linea_id) if linea_id else Producto.objects.none()
            self.fields['marco'].queryset = Marco.objects.filter(producto_id=producto_id) if producto_id else Marco.objects.none()
        else:
            self.fields['linea'].queryset = Linea.objects.none()
            self.fields['producto'].queryset = Producto.objects.none()
            self.fields['marco'].queryset = Marco.objects.none()


class InteriorForm(forms.ModelForm):
    extrusora = forms.ModelChoiceField(
        queryset=Extrusora.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': _select_class + ' no-select2', 'disabled': 'disabled'}),
        label='Extrusora'
    )
    linea = forms.ModelChoiceField(
        queryset=Linea.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': _select_class + ' no-select2', 'disabled': 'disabled'}),
        label='Línea'
    )
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': _select_class + ' no-select2', 'disabled': 'disabled'}),
        label='Producto'
    )
    marco = forms.ModelChoiceField(
        queryset=Marco.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': _select_class + ' no-select2', 'disabled': 'disabled'}),
        label='Marco'
    )
    
    class Meta:
        model = Interior
        fields = ['hoja', 'descripcion']
        labels = {
            'descripcion': 'Nombre',
        }
        widgets = {
            'hoja': forms.Select(attrs={'class': _select_class + ' no-select2'}),
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
        fields = ['codigo', 'linea', 'descripcion', 'peso_metro', 'long_tira', 'precio_kg', 'moneda', 'tipo_perfil']
        labels = {
            'linea': 'Línea',
            'peso_metro': 'KG x Metro',
            'long_tira': 'Largo',
            'precio_kg': 'Precio x KG',
        }
        widgets = {
            'codigo': forms.TextInput(attrs={'class': _input_class}),
            'linea': forms.Select(attrs={'class': _select_class}),
            'descripcion': forms.TextInput(attrs={'class': _input_class}),
            'peso_metro': forms.NumberInput(attrs={'class': _input_class, 'step': '0.001'}),
            'long_tira': forms.NumberInput(attrs={'class': _input_class}),
            'precio_kg': forms.NumberInput(attrs={'class': _input_class, 'step': '0.01'}),
        }


class PerfilEditForm(forms.ModelForm):
    MONEDA_CHOICES = [
        (1, 'Peso'),
        (2, 'Dólar'),
    ]
    
    TIPO_PERFIL_CHOICES = [
        ('Marco', 'Marco'),
        ('Hojas', 'Hojas'),
    ]
    
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
        fields = ['linea', 'descripcion', 'peso_metro', 'long_tira', 'precio_kg', 'moneda', 'tipo_perfil']
        labels = {
            'linea': 'Línea',
            'peso_metro': 'KG x Metro',
            'long_tira': 'Largo',
            'precio_kg': 'Precio x KG',
        }
        widgets = {
            'linea': forms.Select(attrs={'class': _select_class}),
            'descripcion': forms.TextInput(attrs={'class': _input_class}),
            'peso_metro': forms.NumberInput(attrs={'class': _input_class, 'step': '0.001'}),
            'long_tira': forms.NumberInput(attrs={'class': _input_class}),
            'precio_kg': forms.NumberInput(attrs={'class': _input_class, 'step': '0.01'}),
        }


class AccesorioCreateForm(forms.ModelForm):
    TIPO_CHOICES = [
        ('', '---------'),
        ('hoja', 'Hoja'),
        ('marco', 'Marco'),
    ]
    
    TIPO_CALCULO_CHOICES = [
        ('unidad', 'Unidad'),
        ('formula', 'Fórmula'),
    ]
    
    tipo = forms.ChoiceField(
        choices=TIPO_CHOICES,
        widget=forms.Select(attrs={'class': _select_class}),
        label='Tipo',
        required=False
    )
    
    tipo_calculo = forms.ChoiceField(
        choices=TIPO_CALCULO_CHOICES,
        widget=forms.Select(attrs={'class': _select_class, 'id': 'id_tipo_calculo'}),
        label='Tipo de Cálculo',
        initial='unidad'
    )
    
    class Meta:
        model = Accesorio
        fields = ['codigo', 'descripcion', 'cant', 'tipo', 'tipo_calculo', 'formula_calculo', 'precio']
        labels = {
            'cant': 'Cantidad',
            'formula_calculo': 'Fórmula de Cálculo',
        }
        widgets = {
            'codigo': forms.TextInput(attrs={'class': _input_class}),
            'descripcion': forms.TextInput(attrs={'class': _input_class}),
            'cant': forms.NumberInput(attrs={'class': _input_class, 'value': '1'}),
            'formula_calculo': forms.TextInput(attrs={'class': _input_class, 'placeholder': 'Ej: (Ancho * 2) + (Alto * 2)'}),
            'precio': forms.NumberInput(attrs={'class': _input_class, 'step': '0.01'}),
        }


class AccesorioEditForm(forms.ModelForm):
    TIPO_CHOICES = [
        ('', '---------'),
        ('hoja', 'Hoja'),
        ('marco', 'Marco'),
    ]
    
    TIPO_CALCULO_CHOICES = [
        ('unidad', 'Unidad'),
        ('formula', 'Fórmula'),
    ]
    
    tipo = forms.ChoiceField(
        choices=TIPO_CHOICES,
        widget=forms.Select(attrs={'class': _select_class}),
        label='Tipo',
        required=False
    )
    
    tipo_calculo = forms.ChoiceField(
        choices=TIPO_CALCULO_CHOICES,
        widget=forms.Select(attrs={'class': _select_class, 'id': 'id_tipo_calculo'}),
        label='Tipo de Cálculo'
    )
    
    class Meta:
        model = Accesorio
        fields = ['descripcion', 'cant', 'tipo', 'tipo_calculo', 'formula_calculo', 'precio']
        labels = {
            'cant': 'Cantidad',
            'formula_calculo': 'Fórmula de Cálculo',
        }
        widgets = {
            'descripcion': forms.TextInput(attrs={'class': _input_class}),
            'cant': forms.NumberInput(attrs={'class': _input_class}),
            'formula_calculo': forms.TextInput(attrs={'class': _input_class, 'placeholder': 'Ej: (Ancho * 2) + (Alto * 2)'}),
            'precio': forms.NumberInput(attrs={'class': _input_class, 'step': '0.01'}),
        }


class VidrioCreateForm(forms.ModelForm):
    class Meta:
        model = Vidrio
        fields = ['codigo', 'descripcion', 'precio']
        labels = {'precio': 'Precio / m²'}
        widgets = {
            'codigo': forms.TextInput(attrs={'class': _input_class}),
            'descripcion': forms.TextInput(attrs={'class': _input_class}),
            'precio': forms.NumberInput(attrs={'class': _input_class, 'step': '0.01'}),
        }


class VidrioEditForm(forms.ModelForm):
    class Meta:
        model = Vidrio
        fields = ['descripcion', 'precio']
        labels = {'precio': 'Precio / m²'}
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
