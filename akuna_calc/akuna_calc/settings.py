import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-change-this-in-production')

DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.lower() in {'1', 'true', 'yes', 'on'}


def env_int(name, default):
    value = os.environ.get(name)
    if value in (None, ''):
        return default
    try:
        return int(value)
    except ValueError:
        return default

_allowed_hosts_env = os.environ.get('ALLOWED_HOSTS', '')
if _allowed_hosts_env:
    ALLOWED_HOSTS = [h.strip() for h in _allowed_hosts_env.split(',') if h.strip()]
else:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1'] if not DEBUG else ['*']

_csrf_trusted_env = os.environ.get('CSRF_TRUSTED_ORIGINS', '')
CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_trusted_env.split(',') if o.strip()]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'security',
    'core',
    'productos',
    'usuarios',
    'comercial',
    'facturacion',
    'plantillas',
    'pricing',
    'pedidos',
    'presupuestos',
    'configuracion',
    'gastos_diarios',
    'agenda',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'core.middleware.PersistedNavigationMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'usuarios.middleware.RouteAccessMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'security.middleware.SecurityMiddleware',  # Seguridad personalizada
    'security.middleware.AuditMiddleware',  # Auditoría
    'security.middleware.LoginAttemptMiddleware',  # Control de intentos de login
]

ROOT_URLCONF = 'akuna_calc.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'usuarios.context_processors.sidebar_access',
            ],
        },
    },
]

WSGI_APPLICATION = 'akuna_calc.wsgi.application'

_database_url = os.environ.get("DATABASE_URL")
_default_conn_max_age = env_int('DB_CONN_MAX_AGE', 600)
if _database_url:
    DATABASES = {"default": dj_database_url.parse(_database_url, conn_max_age=_default_conn_max_age)}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.environ.get("DB_NAME", "akuna_calc"),
            "USER": os.environ.get("DB_USER", "root"),
            "PASSWORD": os.environ.get("DB_PASSWORD", ""),
            "HOST": os.environ.get("DB_HOST", "127.0.0.1"),
            "PORT": os.environ.get("DB_PORT", "3306"),
            "CONN_MAX_AGE": _default_conn_max_age,
        }
    }

if DATABASES["default"].get("ENGINE", "").endswith("mysql"):
    DATABASES["default"].setdefault("CONN_HEALTH_CHECKS", env_bool('DB_CONN_HEALTH_CHECKS', True))
    DATABASES["default"].setdefault("OPTIONS", {})
    DATABASES["default"]["OPTIONS"].update({
        "charset": "utf8mb4",
        "init_command": "SET sql_mode='STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION'",
    })
    DATABASES["default"]["OPTIONS"].setdefault("connect_timeout", env_int('DB_CONNECT_TIMEOUT', 5))

    _db_read_timeout = env_int('DB_READ_TIMEOUT', None)
    if _db_read_timeout is not None:
        DATABASES["default"]["OPTIONS"].setdefault("read_timeout", _db_read_timeout)

    _db_write_timeout = env_int('DB_WRITE_TIMEOUT', None)
    if _db_write_timeout is not None:
        DATABASES["default"]["OPTIONS"].setdefault("write_timeout", _db_write_timeout)

# Excluir migraciones de apps legacy en tests (pricing tiene managed=False)
import sys
if 'test' in sys.argv:
    MIGRATION_MODULES = {
        'pricing': None,
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'America/Argentina/Buenos_Aires'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = Path(os.environ.get('MEDIA_ROOT', BASE_DIR / 'media'))

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'login'

# ============================================
# CONFIGURACIÓN DE SEGURIDAD
# ============================================

# Seguridad de sesiones
SESSION_COOKIE_SECURE = not DEBUG  # Solo HTTPS en producción
SESSION_COOKIE_HTTPONLY = True  # No accesible desde JavaScript
SESSION_COOKIE_SAMESITE = 'Lax'  # Protección CSRF
SESSION_COOKIE_AGE = 3600  # 1 hora

# Seguridad de CSRF
CSRF_COOKIE_SECURE = not DEBUG  # Solo HTTPS en producción
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# Seguridad de headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'  # Prevenir clickjacking
SECURE_REDIRECT_EXEMPT = [r'^health/$']

# HTTPS (solo en producción)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # 1 año
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Validación de contraseñas mejorada
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django.security': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'security': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}