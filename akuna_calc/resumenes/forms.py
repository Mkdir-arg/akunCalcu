from django import forms

from .services import PERIODOS

LIMITE_TEXTO = 4000  # WhatsApp corta en 4096


class GuardarResumenForm(forms.Form):
    periodo = forms.ChoiceField(choices=[(p, p) for p in PERIODOS])
    hasta = forms.DateField(input_formats=['%Y-%m-%d'])
    texto = forms.CharField(strip=True)
    datos = forms.JSONField(required=False)

    def clean_texto(self):
        texto = self.cleaned_data['texto']
        if len(texto) > LIMITE_TEXTO:
            texto = texto[:LIMITE_TEXTO - 1].rstrip() + '…'
        return texto
