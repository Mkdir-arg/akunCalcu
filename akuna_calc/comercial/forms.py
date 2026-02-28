from django import forms
from django.db.models import Q
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
        cuenta_actual_id = None
        tipo_gasto_actual_id = None
        tipo_cuenta_actual_id = None

        if self.instance and self.instance.pk:
            cuenta_actual_id = self.instance.cuenta_id
            tipo_gasto_actual_id = self.instance.tipo_gasto_id
            tipo_cuenta_actual_id = self.instance.cuenta.tipo_cuenta_id if self.instance.cuenta_id else None
            self.fields['tipo_cuenta_filter'].initial = tipo_cuenta_actual_id

        # Para edición y para re-render por errores de validación, mantener la selección del POST.
        if self.is_bound:
            tipo_cuenta_post = self.data.get('tipo_cuenta_filter')
            if tipo_cuenta_post:
                tipo_cuenta_actual_id = tipo_cuenta_post
            cuenta_post = self.data.get('cuenta')
            if cuenta_post:
                cuenta_actual_id = cuenta_post
            tipo_gasto_post = self.data.get('tipo_gasto')
            if tipo_gasto_post:
                tipo_gasto_actual_id = tipo_gasto_post

        cuentas_qs = Cuenta.objects.filter(activo=True, deleted_at__isnull=True)
        tipos_gasto_qs = TipoGasto.objects.filter(activo=True, deleted_at__isnull=True)
        tipos_cuenta_qs = TipoCuenta.objects.filter(activo=True, deleted_at__isnull=True)

        # Incluir los valores actuales por si fueron desactivados, para no perder selección al editar.
        if cuenta_actual_id:
            cuentas_qs = Cuenta.objects.filter(
                Q(activo=True, deleted_at__isnull=True) | Q(pk=cuenta_actual_id)
            )
        if tipo_gasto_actual_id:
            tipos_gasto_qs = TipoGasto.objects.filter(
                Q(activo=True, deleted_at__isnull=True) | Q(pk=tipo_gasto_actual_id)
            )
        if tipo_cuenta_actual_id:
            tipos_cuenta_qs = TipoCuenta.objects.filter(
                Q(activo=True, deleted_at__isnull=True) | Q(pk=tipo_cuenta_actual_id)
            )

        self.fields['cuenta'].queryset = cuentas_qs.order_by('nombre')
        self.fields['tipo_gasto'].queryset = tipos_gasto_qs.order_by('nombre')
        self.fields['tipo_cuenta_filter'].queryset = tipos_cuenta_qs.order_by('tipo')

        # El input[type=date] necesita YYYY-MM-DD para mostrar correctamente el valor inicial.
        self.fields['fecha_pago'].widget.format = '%Y-%m-%d'
        self.fields['fecha_pago'].input_formats = ['%Y-%m-%d', '%d/%m/%Y']
    
    class Meta:
        model = Compra
        exclude = ['created_at', 'created_by']
        widgets = {
            'numero_pedido': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'cuenta': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'id': 'id_cuenta'}),
            'tipo_gasto': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'id': 'id_tipo_gasto'}),
            'fecha_pago': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'type': 'date'}),
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
