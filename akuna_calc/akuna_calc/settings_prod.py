from .settings import *
import pymysql

# Use PyMySQL instead of mysqlclient
pymysql.install_as_MySQLdb()

# Production settings
DEBUG = False
ALLOWED_HOSTS = ['akun.pythonanywhere.com', 'AKUN.pythonanywhere.com', 'localhost', '127.0.0.1']

# Database for PythonAnywhere
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'AKUN$default',
        'USER': 'AKUN',
        'PASSWORD': 'AKUN1234!',
        'HOST': 'AKUN.mysql.pythonanywhere-services.com',
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION'",
        },
    }
}

# Static files for production
STATIC_ROOT = '/home/AKUN/akunCalcu/akuna_calc/staticfiles'
STATICFILES_DIRS = ['/home/AKUN/akunCalcu/akuna_calc/static']

# Security settings
SECURE_SSL_REDIRECT = False  # PythonAnywhere handles SSL
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True