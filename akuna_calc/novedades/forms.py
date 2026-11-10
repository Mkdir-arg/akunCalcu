from django import forms

from .models import Noticia
from .services import modulo_choices


class NoticiaForm(forms.ModelForm):
    class Meta:
        model = Noticia
        fields = ['titulo', 'texto', 'tipo', 'modulo']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'input'}),
            'texto': forms.Textarea(attrs={'class': 'input', 'rows': 6}),
            'tipo': forms.Select(attrs={'class': 'input'}),
        }
        help_texts = {
            'texto': 'Escribilo como lo va a leer el equipo: qué cambió y dónde se usa, sin términos técnicos.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['modulo'] = forms.ChoiceField(
            label='Módulo', choices=modulo_choices(), required=False,
            widget=forms.Select(attrs={'class': 'input'}),
            help_text='Solo la ven quienes tienen acceso a ese módulo. «General» la ven todos.',
        )


class BorradorApiForm(forms.Form):
    """Valida lo que manda la GitHub Action."""
    sha = forms.RegexField(regex=r'^[0-9a-f]{7,40}$')
    titulo = forms.CharField(max_length=200)
    texto_usuario = forms.CharField(required=False)
    texto_tecnico = forms.CharField(required=False)
    pr_numero = forms.IntegerField(required=False, min_value=1)
    autor = forms.CharField(required=False, max_length=100)
