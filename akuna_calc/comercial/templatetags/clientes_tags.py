from django import template
from django.urls import reverse

from comercial.forms import ClienteForm

register = template.Library()


@register.inclusion_tag('comercial/clientes/_modal_nuevo_cliente.html', takes_context=True)
def modal_nuevo_cliente(context, target='#id_cliente'):
    return {
        'form': ClienteForm(auto_id='nc_%s'),
        'url': reverse('comercial:cliente_create_rapido'),
        'target': target,
        'csrf_token': context.get('csrf_token'),
    }
