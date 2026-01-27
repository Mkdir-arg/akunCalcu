from django import forms
from .models import Factura, FacturaItem, PuntoVenta
from comercial.models import Cliente


class FacturaForm(forms.ModelForm):
    class Meta:
        model = Factura
        fields = ['cliente', 'punto_venta', 'tipo']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-select'}),
            'punto_venta': forms.Select(attrs={'class': 'form-select'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['punto_venta'].queryset = PuntoVenta.objects.filter(activo=True)


class FacturaItemForm(forms.ModelForm):
    class Meta:
        model = FacturaItem
        fields = ['producto', 'descripcion', 'cantidad', 'precio_unitario', 'alicuota_iva']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-select'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'alicuota_iva': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si se selecciona un producto, autocompletar descripción y alícuota
        if self.instance and self.instance.producto:
            self.fields['descripcion'].initial = self.instance.producto.nombre
            self.fields['alicuota_iva'].initial = self.instance.producto.alicuota_iva


FacturaItemFormSet = forms.inlineformset_factory(
    Factura,
    FacturaItem,
    form=FacturaItemForm,
    extra=1,
    can_delete=True
)
