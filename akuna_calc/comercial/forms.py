from decimal import Decimal

from django import forms
from django.db.models import Exists, OuterRef, Q
from .models import Cliente, Venta, Cuenta, Compra, TipoCuenta, TipoGasto


def _resolver_importe_formulario_usd(form, cleaned_data, *, enabled_field, ars_field, usd_field, rate_field, usd_required_message, rate_required_message):
    enabled = cleaned_data.get(enabled_field)
    ars_value = cleaned_data.get(ars_field)
    usd_value = cleaned_data.get(usd_field)
    rate_value = cleaned_data.get(rate_field)

    if enabled:
        if usd_value is None:
            form.add_error(usd_field, usd_required_message)
        elif usd_value <= 0:
            form.add_error(usd_field, 'Debe indicar un monto mayor a 0.')

        if rate_value is None:
            form.add_error(rate_field, rate_required_message)
        elif rate_value <= 0:
            form.add_error(rate_field, 'Debe indicar una cotización mayor a 0.')

        if usd_value is not None and usd_value > 0 and rate_value is not None and rate_value > 0:
            ars_value = (usd_value * rate_value).quantize(Decimal('0.01'))
            cleaned_data[ars_field] = ars_value
    else:
        cleaned_data[usd_field] = None
        cleaned_data[rate_field] = None
        cleaned_data[ars_field] = ars_value or Decimal('0')
        ars_value = cleaned_data[ars_field]

    return ars_value


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

    def clean_email(self):
        """Evita clientes duplicados por email (case-insensitive). En edición ignora
        al propio cliente. Los clientes sin email no se validan (puede haber varios)."""
        email = (self.cleaned_data.get('email') or '').strip()
        if not email:
            return email
        qs = Cliente.objects.filter(email__iexact=email, deleted_at__isnull=True)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        existente = qs.first()
        if existente:
            raise forms.ValidationError(
                f'Ya existe un cliente con ese email ({existente}). Elegilo del desplegable en vez de crear uno nuevo.'
            )
        return email


class VentaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['valor_total'].required = False
        self.fields['sena'].required = False
        # El input[type=date] necesita YYYY-MM-DD para renderizar el valor inicial.
        self.fields['fecha_pago'].widget.format = '%Y-%m-%d'
        self.fields['fecha_pago'].input_formats = ['%Y-%m-%d', '%d/%m/%Y']
        self.fields['fecha_factura'].widget.format = '%Y-%m-%d'
        self.fields['fecha_factura'].input_formats = ['%Y-%m-%d', '%d/%m/%Y']

    class Meta:
        model = Venta
        exclude = ['saldo', 'created_at', 'updated_at']
        widgets = {
            'numero_pedido': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'Ej: PVC, 001, etc.'}),
            'cliente': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'venta_en_dolares': forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50', 'id': 'id_venta_en_dolares'}),
            'valor_total': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'step': '0.01'}),
            'valor_total_usd': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'step': '0.01', 'id': 'id_valor_total_usd'}),
            'cotizacion_usd': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'step': '0.01', 'id': 'id_cotizacion_usd'}),
            'tiene_retenciones': forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50', 'id': 'id_tiene_retenciones'}),
            'monto_retenciones': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'step': '0.01', 'id': 'id_monto_retenciones'}),
            'sena': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'step': '0.01'}),
            'sena_en_dolares': forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50', 'id': 'id_sena_en_dolares'}),
            'sena_usd': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'step': '0.01', 'id': 'id_sena_usd'}),
            'cotizacion_sena_usd': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'step': '0.01', 'id': 'id_cotizacion_sena_usd'}),
            'fecha_pago': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'type': 'date'}),
            'forma_pago': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'con_factura': forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50'}),
            'tipo_factura': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'numero_factura': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'fecha_factura': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'type': 'date'}),
            'estado': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'observaciones': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'rows': 3}),
        }
        labels = {
            'con_factura': 'Venta en blanco (con factura)',
            'venta_en_dolares': 'Venta en dólares',
            'valor_total_usd': 'Valor total en USD',
            'cotizacion_usd': 'Cotización USD utilizada',
            'tiene_retenciones': 'Tiene retenciones',
            'monto_retenciones': 'Monto de retenciones',
            'sena': 'Seña',
            'sena_en_dolares': 'Seña en dólares',
            'sena_usd': 'Seña en USD',
            'cotizacion_sena_usd': 'Cotización USD de la seña',
        }

    def clean(self):
        cleaned_data = super().clean()
        valor_total = _resolver_importe_formulario_usd(
            self,
            cleaned_data,
            enabled_field='venta_en_dolares',
            ars_field='valor_total',
            usd_field='valor_total_usd',
            rate_field='cotizacion_usd',
            usd_required_message='Debe indicar el valor total en USD cuando la venta está en dólares.',
            rate_required_message='Debe indicar la cotización USD de la venta.',
        )

        if valor_total <= 0:
            self.add_error('valor_total', 'Debe indicar un valor total mayor a 0.')

        _resolver_importe_formulario_usd(
            self,
            cleaned_data,
            enabled_field='sena_en_dolares',
            ars_field='sena',
            usd_field='sena_usd',
            rate_field='cotizacion_sena_usd',
            usd_required_message='Debe indicar el monto de la seña en USD cuando selecciona esa moneda.',
            rate_required_message='Debe indicar la cotización USD de la seña.',
        )

        return cleaned_data


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
        self.fields['valor_total'].required = False
        self.fields['sena'].required = False
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
        exclude = ['created_at', 'created_by', 'saldo', 'deleted_at', 'updated_at', 'estado', 'notas_internas']
        widgets = {
            'numero_pedido': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'cuenta': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'id': 'id_cuenta'}),
            'tipo_gasto': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'id': 'id_tipo_gasto'}),
            'fecha_pago': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'type': 'date'}),
            'compra_en_dolares': forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50', 'id': 'id_compra_en_dolares'}),
            'valor_total': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'step': '0.01'}),
            'valor_total_usd': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'step': '0.01', 'id': 'id_valor_total_usd'}),
            'cotizacion_usd': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'step': '0.01', 'id': 'id_cotizacion_usd'}),
            'sena': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'step': '0.01'}),
            'sena_en_dolares': forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50', 'id': 'id_sena_en_dolares'}),
            'sena_usd': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'step': '0.01', 'id': 'id_sena_usd'}),
            'cotizacion_sena_usd': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'step': '0.01', 'id': 'id_cotizacion_sena_usd'}),
            'forma_pago_sena': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'id': 'id_forma_pago_sena'}),
            'con_factura': forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50'}),
            'numero_factura': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'descripcion': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'rows': 3}),
            'comprobante': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'}),
        }
        labels = {
            'con_factura': 'Compra en blanco (con factura)',
            'tipo_gasto': 'Tipo de Gasto',
            'valor_total': 'Valor Total',
            'compra_en_dolares': 'Compra en dólares',
            'valor_total_usd': 'Valor total en USD',
            'cotizacion_usd': 'Cotización USD utilizada',
            'sena': 'Seña',
            'sena_en_dolares': 'Seña en dólares',
            'sena_usd': 'Seña en USD',
            'cotizacion_sena_usd': 'Cotización USD de la seña',
            'forma_pago_sena': 'Forma de Pago de la Seña',
        }

    def clean(self):
        cleaned_data = super().clean()
        valor_total = _resolver_importe_formulario_usd(
            self,
            cleaned_data,
            enabled_field='compra_en_dolares',
            ars_field='valor_total',
            usd_field='valor_total_usd',
            rate_field='cotizacion_usd',
            usd_required_message='Debe indicar el valor total en USD cuando la compra está en dólares.',
            rate_required_message='Debe indicar la cotización USD de la compra.',
        )

        if not valor_total or valor_total <= 0:
            self.add_error('valor_total', 'Debe indicar un valor total mayor a 0.')

        sena = _resolver_importe_formulario_usd(
            self,
            cleaned_data,
            enabled_field='sena_en_dolares',
            ars_field='sena',
            usd_field='sena_usd',
            rate_field='cotizacion_sena_usd',
            usd_required_message='Debe indicar el monto de la seña en USD cuando selecciona esa moneda.',
            rate_required_message='Debe indicar la cotización USD de la seña.',
        )

        sena_en_dolares = cleaned_data.get('sena_en_dolares')
        forma_pago_sena = cleaned_data.get('forma_pago_sena')

        if sena > 0 and not forma_pago_sena:
            self.add_error('forma_pago_sena', 'Debe indicar la forma de pago cuando registra una seña.')

        if sena <= 0:
            cleaned_data['forma_pago_sena'] = ''
            if not sena_en_dolares:
                cleaned_data['sena'] = Decimal('0')

        return cleaned_data


class ReporteForm(forms.Form):
    TIPO_FACTURA_CHOICES = [
        ('blanco', 'Blanco'),
        ('negro', 'Negro'),
    ]
    ORDEN_CHOICES = [
        ('fecha_desc', 'Fecha: más recientes'),
        ('fecha_asc', 'Fecha: más antiguas'),
        ('monto_desc', 'Monto: mayor a menor'),
        ('monto_asc', 'Monto: menor a mayor'),
        ('cliente_asc', 'Cliente: A a Z'),
    ]
    
    fecha_desde = forms.DateField(
        required=False,
        input_formats=['%Y-%m-%d', '%d/%m/%Y'],
        widget=forms.DateInput(format='%Y-%m-%d', attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'type': 'date'})
    )
    fecha_hasta = forms.DateField(
        required=False,
        input_formats=['%Y-%m-%d', '%d/%m/%Y'],
        widget=forms.DateInput(format='%Y-%m-%d', attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'type': 'date'})
    )
    cliente = forms.ModelMultipleChoiceField(
        queryset=Cliente.objects.filter(deleted_at__isnull=True),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'id': 'id_cliente'})
    )
    numero_factura = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Ej: 0001-00001234'
        })
    )
    orden = forms.ChoiceField(
        required=False,
        initial='fecha_desc',
        choices=ORDEN_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'id': 'id_orden'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fecha_desde'].widget.format = '%Y-%m-%d'
        self.fields['fecha_hasta'].widget.format = '%Y-%m-%d'
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


class ReporteCobranzasForm(ReporteForm):
    MONEDA_COBRANZA_CHOICES = [
        ('todas', 'Todas'),
        ('usd', 'Solo USD'),
        ('ars', 'Solo pesos'),
    ]

    moneda_cobranza = forms.ChoiceField(
        required=False,
        initial='todas',
        choices=MONEDA_COBRANZA_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'id': 'id_moneda_cobranza',
        })
    )


class ReporteGastosForm(forms.Form):
    TIPO_FACTURA_CHOICES = [
        ('blanco', 'Blanco'),
        ('negro', 'Negro'),
    ]
    
    fecha_desde = forms.DateField(
        required=False,
        input_formats=['%Y-%m-%d', '%d/%m/%Y'],
        widget=forms.DateInput(format='%Y-%m-%d', attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'type': 'date'})
    )
    fecha_hasta = forms.DateField(
        required=False,
        input_formats=['%Y-%m-%d', '%d/%m/%Y'],
        widget=forms.DateInput(format='%Y-%m-%d', attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'type': 'date'})
    )
    cuenta = forms.ModelMultipleChoiceField(
        queryset=Cuenta.objects.filter(deleted_at__isnull=True, activo=True),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'})
    )
    tipo_cuenta = forms.ModelMultipleChoiceField(
        queryset=TipoCuenta.objects.filter(deleted_at__isnull=True, activo=True),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'})
    )
    tipo_gasto = forms.ModelMultipleChoiceField(
        queryset=TipoGasto.objects.filter(deleted_at__isnull=True, activo=True),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'})
    )
    tipo_factura = forms.MultipleChoiceField(
        choices=TIPO_FACTURA_CHOICES,
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fecha_desde'].widget.format = '%Y-%m-%d'
        self.fields['fecha_hasta'].widget.format = '%Y-%m-%d'


class ReporteProveedorForm(forms.Form):
    proveedor = forms.ModelChoiceField(
        queryset=Cuenta.objects.filter(
            deleted_at__isnull=True,
            tipo_cuenta__tipo='proveedores',
        ).annotate(
            tiene_movimientos=Exists(
                Compra.objects.filter(cuenta=OuterRef('pk'), deleted_at__isnull=True)
            )
        ).filter(
            Q(activo=True) | Q(tiene_movimientos=True)
        ).select_related('tipo_cuenta').order_by('nombre'),
        required=False,
        empty_label='Todos los proveedores',
        widget=forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'})
    )
