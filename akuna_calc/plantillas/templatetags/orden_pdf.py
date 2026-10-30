from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def si_no(valor):
    """Celdas de valor de una pregunta SÍ/NO del PDF: la respuesta, o dos casillas para tildar a mano."""
    if valor is not None and str(valor).strip():
        return format_html('<td class="dv" style="width:42%;">{}</td>', valor)
    return mark_safe(
        '<td class="box" style="width:3%;">&nbsp;</td>'
        '<td class="opt" style="width:8%;">SÍ</td>'
        '<td class="box" style="width:3%;">&nbsp;</td>'
        '<td class="opt" style="width:28%;">NO</td>'
    )
