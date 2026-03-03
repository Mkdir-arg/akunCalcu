from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Obtiene un item de un diccionario"""
    if dictionary is None:
        return ''
    return dictionary.get(key, '')

@register.filter
def split(value, arg):
    """Divide un string por un separador"""
    if not value:
        return []
    return value.split(arg)
