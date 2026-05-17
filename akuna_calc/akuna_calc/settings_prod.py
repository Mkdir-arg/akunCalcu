from .settings import *  # noqa: F401,F403
import os

DEBUG = False

railway_public_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', '').strip()
_allowed_hosts_env = os.environ.get('ALLOWED_HOSTS', '')
ALLOWED_HOSTS = [h.strip() for h in _allowed_hosts_env.split(',') if h.strip()]
if railway_public_domain:
	ALLOWED_HOSTS.append(railway_public_domain)
ALLOWED_HOSTS.append('healthcheck.railway.app')
ALLOWED_HOSTS = list(dict.fromkeys(ALLOWED_HOSTS))

_csrf_trusted_env = os.environ.get('CSRF_TRUSTED_ORIGINS', '')
CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_trusted_env.split(',') if o.strip()]
if railway_public_domain:
	CSRF_TRUSTED_ORIGINS.append(f'https://{railway_public_domain}')
CSRF_TRUSTED_ORIGINS = list(dict.fromkeys(CSRF_TRUSTED_ORIGINS))

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
