from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django.utils.http import url_has_allowed_host_and_scheme


RETURN_TO_PARAM = '_return_to'
PAGE_STATE_SESSION_KEY = 'persisted_page_state'


def _is_safe_local_url(request, url):
    if not url:
        return False

    return url_has_allowed_host_and_scheme(
        url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    )


def _normalize_path(url):
    return urlsplit(url).path


def get_explicit_return_url(request):
    return request.POST.get(RETURN_TO_PARAM) or request.GET.get(RETURN_TO_PARAM) or ''


def resolve_return_url(request, default_url):
    explicit_return_url = get_explicit_return_url(request)
    if _is_safe_local_url(request, explicit_return_url):
        return explicit_return_url

    remembered_pages = request.session.get(PAGE_STATE_SESSION_KEY, {})
    remembered_url = remembered_pages.get(_normalize_path(default_url), '')
    if _is_safe_local_url(request, remembered_url):
        return remembered_url

    return default_url


def append_return_to(url, return_to):
    if not return_to:
        return url

    parsed_url = urlsplit(url)
    query_items = [
        (key, value)
        for key, value in parse_qsl(parsed_url.query, keep_blank_values=True)
        if key != RETURN_TO_PARAM
    ]
    query_items.append((RETURN_TO_PARAM, return_to))

    return urlunsplit(
        (
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            urlencode(query_items),
            parsed_url.fragment,
        )
    )


def remember_page_state(request):
    if request.method != 'GET' or not hasattr(request, 'session'):
        return

    current_full_path = request.get_full_path()
    remembered_pages = request.session.get(PAGE_STATE_SESSION_KEY, {})
    if remembered_pages.get(request.path) == current_full_path:
        return

    remembered_pages[request.path] = current_full_path
    request.session[PAGE_STATE_SESSION_KEY] = remembered_pages
