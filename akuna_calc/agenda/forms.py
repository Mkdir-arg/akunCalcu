from django import forms

from comercial.models import Cliente, Cuenta
from gastos_diarios.models import NumeroAutorizado

from .models import EventoAgenda


_INPUT = 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'


class EventoAgendaForm(forms.ModelForm):
    class Meta:
        model = EventoAgenda
        fields = [
            'titulo', 'descripcion', 'tipo', 'fecha_evento', 'hora_envio',
            'anticipacion_dias', 'destinatarios', 'activo',
            'colocador', 'cliente', 'direccion', 'lat', 'lng',
        ]
        widgets = {
            'titulo': forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Ej: Colocación de ventana en obra Pérez'}),
            'descripcion': forms.Textarea(attrs={'class': _INPUT, 'rows': 3, 'placeholder': 'Detalle del evento (opcional)'}),
            'tipo': forms.Select(attrs={'class': _INPUT, 'id': 'id_tipo'}),
            'fecha_evento': forms.DateInput(attrs={'class': _INPUT, 'type': 'date'}, format='%Y-%m-%d'),
            'hora_envio': forms.TimeInput(attrs={'class': _INPUT, 'type': 'time'}, format='%H:%M'),
            'anticipacion_dias': forms.NumberInput(attrs={'class': _INPUT, 'min': 0}),
            'destinatarios': forms.SelectMultiple(attrs={'class': _INPUT}),
            'activo': forms.CheckboxInput(attrs={'class': 'h-5 w-5 text-blue-600 rounded border-gray-300 focus:ring-blue-500'}),
            'colocador': forms.Select(attrs={'class': _INPUT, 'id': 'id_colocador'}),
            'cliente': forms.Select(attrs={'class': _INPUT, 'id': 'id_cliente'}),
            'direccion': forms.TextInput(attrs={'class': _INPUT, 'id': 'id_direccion', 'placeholder': 'Calle 123, Localidad'}),
            'lat': forms.HiddenInput(attrs={'id': 'id_lat'}),
            'lng': forms.HiddenInput(attrs={'id': 'id_lng'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['destinatarios'].queryset = NumeroAutorizado.objects.filter(activo=True)
        self.fields['destinatarios'].help_text = 'Números autorizados a los que se enviará el recordatorio.'
        self.fields['cliente'].queryset = Cliente.objects.filter(deleted_at__isnull=True)
        self.fields['cliente'].required = False
        self.fields['direccion'].required = False
        self.fields['colocador'].queryset = Cuenta.objects.filter(
            tipo_cuenta__tipo='colocadores', activo=True, deleted_at__isnull=True,
        ).select_related('tipo_cuenta')
        self.fields['colocador'].required = False
        self.fields['hora_envio'].input_formats = ['%H:%M', '%H:%M:%S']
        self.fields['fecha_evento'].input_formats = ['%Y-%m-%d']

    def clean_destinatarios(self):
        destinatarios = self.cleaned_data.get('destinatarios')
        if not destinatarios:
            raise forms.ValidationError("Elegí al menos un destinatario.")
        return destinatarios
