from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.forms import inlineformset_factory

from .models import (
    ConfiguracionAgente,
    Conversacion,
    DiaCerrado,
    EntradaConocimiento,
    FranjaAtencion,
    FranjaTecnico,
    TecnicoVisita,
    ZonaTecnico,
    normalizar_numeros,
)

User = get_user_model()

_INPUT = 'input'
_CHECK = 'h-5 w-5 rounded border-line'


def _usuarios_activos(incluir_pk=None):
    """Usuarios activos; incluye además al ya elegido aunque se haya dado de baja,
    para que el formulario se pueda volver a guardar sin cambiarlo."""
    filtro = Q(is_active=True)
    if incluir_pk:
        filtro |= Q(pk=incluir_pk)
    return User.objects.filter(filtro).order_by('first_name', 'username')


class ConfiguracionAgenteForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionAgente
        fields = [
            'nombre_firma', 'instrucciones_tono', 'modelo_ia',
            'whatsapp_activo', 'email_activo', 'instagram_activo',
            'modo_prueba', 'numeros_prueba', 'derivar_a',
        ]
        widgets = {
            'nombre_firma': forms.TextInput(attrs={'class': _INPUT}),
            'instrucciones_tono': forms.Textarea(attrs={'class': _INPUT, 'rows': 5}),
            'modelo_ia': forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'gpt-5-mini'}),
            'whatsapp_activo': forms.CheckboxInput(attrs={'class': _CHECK}),
            'email_activo': forms.CheckboxInput(attrs={'class': _CHECK}),
            'instagram_activo': forms.CheckboxInput(attrs={'class': _CHECK}),
            'modo_prueba': forms.CheckboxInput(attrs={'class': _CHECK}),
            'numeros_prueba': forms.Textarea(attrs={'class': _INPUT, 'rows': 4, 'placeholder': '5491155555555'}),
            'derivar_a': forms.Select(attrs={'class': _INPUT}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['derivar_a'].queryset = _usuarios_activos(self.instance.derivar_a_id)

    def clean_numeros_prueba(self):
        return normalizar_numeros(self.cleaned_data.get('numeros_prueba'))

    def clean_modelo_ia(self):
        return (self.cleaned_data.get('modelo_ia') or '').strip()


class FranjaAtencionForm(forms.ModelForm):
    class Meta:
        model = FranjaAtencion
        fields = ['dia_semana', 'hora_desde', 'hora_hasta']
        widgets = {
            'dia_semana': forms.Select(attrs={'class': _INPUT}),
            'hora_desde': forms.TimeInput(attrs={'class': _INPUT, 'type': 'time'}, format='%H:%M'),
            'hora_hasta': forms.TimeInput(attrs={'class': _INPUT, 'type': 'time'}, format='%H:%M'),
        }


class DiaCerradoForm(forms.ModelForm):
    class Meta:
        model = DiaCerrado
        fields = ['fecha', 'motivo']
        widgets = {
            'fecha': forms.DateInput(attrs={'class': _INPUT, 'type': 'date'}, format='%Y-%m-%d'),
            'motivo': forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Feriado, vacaciones…'}),
        }


class TecnicoVisitaForm(forms.ModelForm):
    class Meta:
        model = TecnicoVisita
        fields = ['usuario', 'duracion_minutos', 'cupo_por_franja', 'costo_visita', 'activo', 'notas']
        widgets = {
            'usuario': forms.Select(attrs={'class': _INPUT}),
            'duracion_minutos': forms.NumberInput(attrs={'class': _INPUT, 'min': 1}),
            'cupo_por_franja': forms.NumberInput(attrs={'class': _INPUT, 'min': 1}),
            'costo_visita': forms.NumberInput(attrs={'class': _INPUT, 'min': 0, 'step': '0.01'}),
            'activo': forms.CheckboxInput(attrs={'class': _CHECK}),
            'notas': forms.Textarea(attrs={'class': _INPUT, 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['usuario'].queryset = _usuarios_activos(self.instance.usuario_id if self.instance.pk else None)


class FranjaTecnicoForm(forms.ModelForm):
    class Meta:
        model = FranjaTecnico
        fields = ['dia_semana', 'hora_desde', 'hora_hasta']
        widgets = FranjaAtencionForm.Meta.widgets

    def _post_clean(self):
        # El formset compara todas las franjas juntas (incluidas las que se borran o cambian
        # en el mismo envío), así que el modelo no las compara contra la base.
        self.instance._superposicion_validada_afuera = True
        super()._post_clean()


class BaseFranjaTecnicoFormSet(forms.BaseInlineFormSet):
    """Valida superposiciones entre las franjas del mismo formulario (aún sin guardar)."""

    def clean(self):
        super().clean()
        vigentes = []
        for form in self.forms:
            if not hasattr(form, 'cleaned_data') or not form.cleaned_data:
                continue
            if form.cleaned_data.get('DELETE'):
                continue
            dia = form.cleaned_data.get('dia_semana')
            desde = form.cleaned_data.get('hora_desde')
            hasta = form.cleaned_data.get('hora_hasta')
            if dia is None or desde is None or hasta is None:
                continue
            for otro_dia, otro_desde, otro_hasta in vigentes:
                if dia == otro_dia and desde < otro_hasta and hasta > otro_desde:
                    raise forms.ValidationError('Hay franjas del técnico que se superponen el mismo día.')
            vigentes.append((dia, desde, hasta))


class ZonaTecnicoForm(forms.ModelForm):
    class Meta:
        model = ZonaTecnico
        fields = ['localidad', 'provincia']
        widgets = {
            'localidad': forms.TextInput(attrs={'class': _INPUT}),
            'provincia': forms.Select(attrs={'class': _INPUT}),
        }

    def clean_localidad(self):
        return ' '.join((self.cleaned_data.get('localidad') or '').split())


class BaseZonaTecnicoFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        vistas = set()
        for form in self.forms:
            if not hasattr(form, 'cleaned_data') or not form.cleaned_data:
                continue
            if form.cleaned_data.get('DELETE'):
                continue
            localidad = (form.cleaned_data.get('localidad') or '').casefold()
            if not localidad:
                continue
            if localidad in vistas:
                raise forms.ValidationError('Hay localidades repetidas en las zonas del técnico.')
            vistas.add(localidad)


FranjaTecnicoFormSet = inlineformset_factory(
    TecnicoVisita, FranjaTecnico, form=FranjaTecnicoForm, formset=BaseFranjaTecnicoFormSet,
    extra=1, can_delete=True,
)

ZonaTecnicoFormSet = inlineformset_factory(
    TecnicoVisita, ZonaTecnico, form=ZonaTecnicoForm, formset=BaseZonaTecnicoFormSet,
    extra=1, can_delete=True,
)


class EntradaConocimientoForm(forms.ModelForm):
    class Meta:
        model = EntradaConocimiento
        fields = ['tema', 'contenido', 'orden', 'activo']
        widgets = {
            'tema': forms.TextInput(attrs={'class': _INPUT}),
            'contenido': forms.Textarea(attrs={'class': _INPUT, 'rows': 8}),
            'orden': forms.NumberInput(attrs={'class': _INPUT, 'min': 0}),
            'activo': forms.CheckboxInput(attrs={'class': _CHECK}),
        }


class SimulacionForm(forms.ModelForm):
    fecha_hora_simulada = forms.DateTimeField(
        required=False,
        label='Fecha y hora simulada',
        help_text='Opcional. Sirve para probar fuera de horario o en un día cerrado.',
        input_formats=['%Y-%m-%dT%H:%M'],
        widget=forms.DateTimeInput(attrs={'class': _INPUT, 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
    )

    class Meta:
        model = Conversacion
        fields = ['canal', 'nombre_contacto', 'fecha_hora_simulada']
        widgets = {
            'canal': forms.Select(attrs={'class': _INPUT}),
            'nombre_contacto': forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Ej. Laura (opcional)'}),
        }
        labels = {'nombre_contacto': 'Nombre del cliente de prueba'}


class MensajeSimuladoForm(forms.Form):
    texto = forms.CharField(max_length=2000, strip=True)
