from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.views import redirect_to_login
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import resolve, Resolver404
from django.utils.deprecation import MiddlewareMixin

from .access_control import PUBLIC_ROUTE_KEYS, get_default_url_for_user, get_route_key, is_api_request, user_has_route_access


class RouteAccessMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        try:
            resolver_match = request.resolver_match or resolve(request.path_info)
        except Resolver404:
            return None

        route_key = get_route_key(resolver_match)
        if not route_key:
            return None

        if resolver_match.namespace == 'admin' or route_key in PUBLIC_ROUTE_KEYS:
            return None

        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(), login_url='login')

        if user_has_route_access(request.user, route_key):
            return None

        if is_api_request(request):
            return JsonResponse({'detail': 'No tiene permisos para acceder a este recurso.'}, status=403)

        fallback_url = get_default_url_for_user(request.user)
        if fallback_url and fallback_url != request.path:
            messages.error(request, 'No tiene permisos para acceder a esa sección.')
            return redirect(fallback_url)

        logout(request)
        messages.error(request, 'Tu usuario no tiene módulos asignados. Contacta a un administrador.')
        return redirect('login')