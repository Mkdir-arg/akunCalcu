from django import forms

from .services import vendedores_pool

SELECT_CLASS = (
    'w-full px-3 py-2 border border-gray-300 rounded-lg '
    'focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
)


class ReasignarSolicitudForm(forms.Form):
    vendedor = forms.ModelChoiceField(
        queryset=None,
        label='Reasignar a',
        empty_label=None,
        widget=forms.Select(attrs={'class': SELECT_CLASS}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['vendedor'].queryset = vendedores_pool()
