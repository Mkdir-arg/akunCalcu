from django import forms
from .models import Cliente, Venta, Cuenta, Compra, TipoCuenta, TipoGasto


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = '__all__'
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'apellido': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'razon_social': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'cuit': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'dni': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'condicion_iva': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'direccion': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'rows': 3}),
            'localidad': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'telefono': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'}),
        }


class VentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        exclude = ['saldo', 'created_at', 'updated_at']
        widgets = {
            'numero_pedido': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'Ej: PVC, 001, etc.'}),
            'cliente': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'valor_total': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'step': '0.01'}),
            'tiene_retenciones': forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50', 'id': 'id_tiene_retenciones'}),
            'monto_retenciones': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'step': '0.01', 'id': 'id_monto_retenciones'}),
            'sena': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'step': '0.01'}),
            'fecha_pago': forms.DateInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'type': 'date'}),
            'forma_pago': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'con_factura': forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50'}),
            'tipo_factura': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'numero_factura': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'estado': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'observaciones': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'rows': 3}),
        }
        labels = {
            'con_factura': 'Venta en blanco (con factura)',
            'tiene_retenciones': 'Tiene retenciones',
            'monto_retenciones': 'Monto de retenciones',
            'sena': 'Seña',
        }


class CuentaForm(forms.ModelForm):
    class Meta:
        model = Cuenta
        fields = '__all__'
        widgets = {
            'tipo_cuenta': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'nombre': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'razon_social': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'telefono': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'direccion': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'rows': 3}),
            'activo': forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50'}),
        }


class CompraForm(forms.ModelForm):
    tipo_cuenta_filter = forms.ModelChoiceField(
        queryset=TipoCuenta.objects.filter(activo=True, deleted_at__isnull=True),
        required=False,
        empty_label="Seleccione tipo de cuenta...",
        widget=forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'id': 'id_tipo_cuenta_filter'}),
        label='Tipo de Cuenta'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si estamos editando, cargar todas las cuentas activas
        if self.instance and self.instance.pk:
            self.fields['cuenta'].queryset = Cuenta.objects.filter(activo=True, deleted_at__isnull=True)
            self.fields['tipo_gasto'].queryset = TipoGasto.objects.filter(activo=True, deleted_at__isnull=True)
    
    class Meta:
        model = Compra
        exclude = ['created_at', 'created_by']
        widgets = {
            'numero_pedido': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'cuenta': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'id': 'id_cuenta'}),
            'tipo_gasto': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'id': 'id_tipo_gasto'}),
            'fecha_pago': forms.DateInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'type': 'date'}),
            'importe_abonado': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'step': '0.01'}),
            'con_factura': forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50'}),
            'numero_factura': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'descripcion': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'rows': 3}),
            'comprobante': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'}),
        }
        labels = {
            'con_factura': 'Compra en blanco (con factura)',
            'tipo_gasto': 'Tipo de Gasto',
        }


class ReporteForm(forms.Form):
    TIPO_FACTURA_CHOICES = [
        ('blanco', 'Blanco'),
        ('negro', 'Negro'),
    ]
    
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'type': 'date'})
    )
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'type': 'date'})
    )
    cliente = forms.ModelMultipleChoiceField(
        queryset=Cliente.objects.filter(deleted_at__isnull=True),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'id': 'id_cliente'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Obtener razones sociales únicas y no vacías
        razones = Cliente.objects.filter(
            deleted_at__isnull=True,
            razon_social__isnull=False
        ).exclude(razon_social='').values_list('razon_social', flat=True).distinct().order_by('razon_social')
        
        self.fields['razon_social'] = forms.MultipleChoiceField(
            choices=[(r, r) for r in razones],
            required=False,
            widget=forms.SelectMultiple(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'id': 'id_razon_social'})
        )
    
    estado_venta = forms.MultipleChoiceField(
        choices=Venta.ESTADO_CHOICES,
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'id': 'id_estado_venta'})
    )
    tipo_factura = forms.MultipleChoiceField(
        choices=TIPO_FACTURA_CHOICES,
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'id': 'id_tipo_factura'})
    )