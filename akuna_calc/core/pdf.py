"""Base común de los PDF internos A4 (REQ-056): logo, datos de empresa y render con xhtml2pdf."""
import base64
import io
from pathlib import Path

from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa


def build_logo_data_url():
    logo_candidates = [
        Path(settings.BASE_DIR) / 'static' / 'imagenes' / 'AKUN-LOGO.png',
        Path(settings.BASE_DIR) / 'static' / 'AKUN-LOGO.png',
        Path(settings.STATIC_ROOT) / 'imagenes' / 'AKUN-LOGO.png',
        Path(settings.STATIC_ROOT) / 'AKUN-LOGO.png',
    ]
    logo_path = next((path for path in logo_candidates if path.exists()), None)
    if not logo_path:
        return ''
    logo_b64 = base64.b64encode(logo_path.read_bytes()).decode('ascii')
    return f'data:image/png;base64,{logo_b64}'


def contexto_base_pdf():
    from configuracion.models import ConfiguracionGeneral

    return {
        'logo_url': build_logo_data_url(),
        'empresa': ConfiguracionGeneral.get_datos_empresa(),
    }


def filas_cliente(cliente, incluir=('cliente', 'domicilio', 'localidad', 'provincia', 'telefono')):
    """Pares (etiqueta, valor) del cliente agrupados de a dos por renglón, para `_datos_cliente.html`."""
    datos = cliente.datos_documento()
    disponibles = {
        'cliente': ('CLIENTE', f"{datos['nombre_completo']} ({datos['codigo']})" if datos['codigo'] else datos['nombre_completo']),
        'domicilio': ('DOMICILIO', datos['direccion']),
        'localidad': ('LOCALIDAD', datos['localidad']),
        'provincia': ('PROVINCIA', datos['provincia']),
        'telefono': ('TELÉFONO', datos['telefono']),
        'email': ('MAIL', datos['email']),
        'cuit': ('CUIT', datos['cuit']),
    }
    pares = [disponibles[clave] for clave in incluir]
    if len(pares) % 2:
        pares.append(('', ''))
    return [pares[i:i + 2] for i in range(0, len(pares), 2)]


class PdfError(Exception):
    pass


def render_pdf_bytes(html):
    result = io.BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=result)
    if pisa_status.err:
        raise PdfError('xhtml2pdf no pudo generar el PDF')
    return result.getvalue()


def pdf_response(template, context, filename, inline=True, error_message='No se pudo generar el PDF.'):
    try:
        contenido = render_pdf_bytes(render_to_string(template, context))
    except PdfError:
        return HttpResponse(error_message, content_type='text/plain; charset=utf-8', status=500)

    response = HttpResponse(contenido, content_type='application/pdf')
    disposicion = 'inline' if inline else 'attachment'
    response['Content-Disposition'] = f'{disposicion}; filename="{filename}"'
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response
