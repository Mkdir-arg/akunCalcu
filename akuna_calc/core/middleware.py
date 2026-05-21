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
