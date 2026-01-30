from django import template
from decimal import Decimal

register = template.Library()

@register.filter(name='formato_numero')
def formato_numero(value):
    """
    Formatea números al estilo argentino: 1.081.293,00
    """
    if value is None or value == '':
        return '0,00'
    
    try:
        # Convertir a Decimal para manejar correctamente
        if isinstance(value, str):
            value = value.replace('.', '').replace(',', '.')
        
        num = Decimal(str(value))
        
        # Separar parte entera y decimal
        partes = f"{num:.2f}".split('.')
        parte_entera = partes[0]
        parte_decimal = partes[1]
        
        # Formatear parte entera con puntos de miles
        if parte_entera.startswith('-'):
            signo = '-'
            parte_entera = parte_entera[1:]
        else:
            signo = ''
        
        # Agregar puntos cada 3 dígitos desde la derecha
        parte_entera_formateada = ''
        for i, digito in enumerate(reversed(parte_entera)):
            if i > 0 and i % 3 == 0:
                parte_entera_formateada = '.' + parte_entera_formateada
            parte_entera_formateada = digito + parte_entera_formateada
        
        return f"{signo}{parte_entera_formateada},{parte_decimal}"
    
    except (ValueError, TypeError, ArithmeticError):
        return '0,00'
