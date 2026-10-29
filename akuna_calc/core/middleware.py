from django.contrib.sessions.middleware import SessionMiddleware
from django.utils.cache import patch_vary_headers
from django.utils.deprecation import MiddlewareMixin

from .navigation import remember_page_state


HEALTHCHECK_PATHS = {'/health', '/health/'}


class PersistedNavigationMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        if request.path in HEALTHCHECK_PATHS:
            return response

        if not getattr(request, 'user', None) or not request.user.is_authenticated:
            return response

        content_type = response.get('Content-Type', '')
        is_html_response = content_type.startswith('text/html')

        if request.method == 'GET' and 200 <= response.status_code < 400 and is_html_response:
            remember_page_state(request)

        return response


class PassiveSessionMiddleware(SessionMiddleware):
    """No renueva la sesión en las consultas automáticas de /core/api/.

    Con SESSION_SAVE_EVERY_REQUEST el poll de tiempo real (cada 20 s) alargaría la
    sesión indefinidamente mientras haya una pestaña abierta.
    """

    def process_response(self, request, response):
        if request.path.startswith('/core/api/') and not getattr(request.session, 'modified', False):
            patch_vary_headers(response, ('Cookie',))
            return response
        return super().process_response(request, response)
