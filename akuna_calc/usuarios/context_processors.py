from .access_control import build_sidebar_modules, get_route_key, get_user_access_summary, get_user_role_label


def sidebar_access(request):
    if not getattr(request, 'user', None) or not request.user.is_authenticated:
        return {
            'sidebar_modules': [],
            'current_route_key': None,
            'user_role_label': '',
            'user_access_summary': '',
        }

    current_route_key = get_route_key(getattr(request, 'resolver_match', None))
    return {
        'sidebar_modules': build_sidebar_modules(request.user, current_route_key),
        'current_route_key': current_route_key,
        'user_role_label': get_user_role_label(request.user),
        'user_access_summary': get_user_access_summary(request.user),
    }