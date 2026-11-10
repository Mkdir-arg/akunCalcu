from django import forms
from django.core.exceptions import ValidationError

from pricing.models import Linea

from .models import OpcionalFabrica, OrdenFabricacion, PedidoFabrica
from .services import abertura_catalogo
from .utils import cortar_a_max_length

CAMPOS_ABERTURA_CATALOGO = ('tipo_abertura', 'linea', 'tipo_marco', 'modelo_hoja', 'tipo_vidrio', 'color')


_INPUT = 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500'


class OrdenFabricacionForm(forms.ModelForm):
    class Meta:
        model = OrdenFabricacion
        fields = [
            'fecha_comprometida', 'atendido_por', 'medicion_por',
            'cliente_nombre', 'cliente_domicilio', 'cliente_piso', 'cliente_depto',
            'cliente_localidad', 'cliente_mail', 'cliente_telefono',
            'tipo_abertura', 'linea', 'color',
            'mosquitero', 'mosquitero_modelo', 'travesano', 'tipo_marco', 'marco_desarmado',
            'umbral_transitable', 'premarco', 'guia_persiana', 'tipo_guia', 'tapacinta',
            'lado', 'modelo_hoja', 'travesano_divisor', 'altura_travesano', 'cantidad_hojas',
            'tipo_vidrio', 'contramarco', 'modelo_contramarco', 'tipo_trabajo', 'altura_trabajo',
            'estructura', 'nota',
        ]
        widgets = {
            'fecha_comprometida': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': _INPUT}),
            'estructura': forms.Textarea(attrs={'rows': 2, 'class': _INPUT}),
            'nota': forms.Textarea(attrs={'rows': 6, 'class': _INPUT}),
        }

    def __init__(self, *args, requiere_motivo=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fecha_comprometida'].input_formats = ['%Y-%m-%d', '%d/%m/%Y']
        for name, field in self.fields.items():
            field.required = False
            if name not in self.Meta.widgets:
                field.widget.attrs.setdefault('class', _INPUT)
        # REQ-063: modificar una orden ya liberada sube su revisión y exige el motivo.
        if requiere_motivo:
            self.fields['motivo_revision'] = forms.CharField(
                label='Motivo del cambio', max_length=500,
                widget=forms.TextInput(attrs={'class': _INPUT}),
                help_text='La orden pasa a una revisión nueva y el taller tiene que reimprimirla.',
            )
        # REQ-067: la abertura se elige del catálogo. Los textos viajan ocultos y solo se
        # reemplazan si el usuario tocó los desplegables (`cat_cambios`).
        for campo in CAMPOS_ABERTURA_CATALOGO:
            self.fields[campo].widget = forms.HiddenInput()
        for clave in abertura_catalogo.CLAVES:
            # 255 = largo del código de vidrio en el catálogo.
            self.fields[f'cat_{clave}'] = forms.CharField(required=False, max_length=255, widget=forms.HiddenInput())
        self.fields['cat_cambios'] = forms.CharField(required=False, max_length=50, widget=forms.HiddenInput())

    def clean(self):
        cleaned = super().clean()
        cambios = set((cleaned.get('cat_cambios') or '').split(','))
        if not cambios & {'cadena', 'color'}:
            return cleaned
        seleccion = dict(self.instance.seleccion_catalogo or {})
        try:
            if 'cadena' in cambios:
                textos, elegidos = abertura_catalogo.resolver_cadena(
                    {clave: cleaned.get(f'cat_{clave}') for clave in abertura_catalogo.CADENA}
                )
                cleaned.update(textos)
                for clave in abertura_catalogo.CADENA:
                    seleccion.pop(clave, None)
                seleccion.update(elegidos)
            if 'color' in cambios:
                cleaned['color'], tratamiento = abertura_catalogo.resolver_color(cleaned.get('cat_tratamiento'))
                seleccion.pop('tratamiento', None)
                if tratamiento is not None:
                    seleccion['tratamiento'] = tratamiento
        except ValidationError as error:
            raise forms.ValidationError(error.messages)
        for campo in (*CAMPOS_ABERTURA_CATALOGO, 'cantidad_hojas'):
            cleaned[campo] = cortar_a_max_length(OrdenFabricacion, campo, cleaned.get(campo))
        self.instance.seleccion_catalogo = seleccion
        return cleaned


class PedidoFabricaForm(forms.ModelForm):
    class Meta:
        model = PedidoFabrica
        fields = ['numero', 'cliente', 'observaciones']


class LiberarPedidoForm(forms.Form):
    motivo_sin_sena = forms.CharField(required=False, max_length=500, label='Motivo para liberar sin seña')


class CancelarPedidoForm(forms.Form):
    motivo = forms.CharField(max_length=500, label='Motivo de la cancelación')


class EntregarPedidoForm(forms.Form):
    tipo = forms.ChoiceField(choices=[('entregado', 'Entregado'), ('colocado', 'Colocado en obra')])


class CambiarEtapaForm(forms.Form):
    etapa = forms.ChoiceField(choices=OrdenFabricacion.ETAPA_CHOICES)
    nota = forms.CharField(required=False, max_length=500)


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
        fields = ['codigo', 'nombre', 'tipo', 'linea_id', 'precio_m2', 'precio_unidad', 'descripcion', 'activo']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg', 'placeholder': 'OPC-001'}),
            'nombre': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg'}),
            'tipo': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg'}),
            'precio_m2': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg', 'step': '0.01', 'min': '0'}),
            'precio_unidad': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg', 'step': '0.01', 'min': '0'}),
            'descripcion': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border rounded-lg', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # El precio por unidad solo aplica al tipo 'unidad'; no debe ser
        # obligatorio para los demás tipos (se normaliza a 0 en clean()).
        self.fields['precio_unidad'].required = False

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

        if tipo == 'unidad':
            cleaned_data['precio_unidad'] = cleaned_data.get('precio_unidad') or 0
        else:
            cleaned_data['precio_unidad'] = 0

        return cleaned_data
