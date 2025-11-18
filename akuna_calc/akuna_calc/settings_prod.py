from .settings import *
import pymysql

# Use PyMySQL instead of mysqlclient
pymysql.install_as_MySQLdb()

# Production settings
DEBUG = False
ALLOWED_HOSTS = ['YOURUSERNAME.pythonanywhere.com', 'localhost', '127.0.0.1']

# Database for PythonAnywhere
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'YOURUSERNAME$default',
        'USER': 'YOURUSERNAME',
        'PASSWORD': 'YOUR_DB_PASSWORD',
        'HOST': 'YOURUSERNAME.mysql.pythonanywhere-services.com',
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}

# Static files for production
STATIC_ROOT = '/home/YOURUSERNAME/akunCalcu/akuna_calc/staticfiles'
STATICFILES_DIRS = ['/home/YOURUSERNAME/akunCalcu/akuna_calc/static']

# Security settings
SECURE_SSL_REDIRECT = False  # PythonAnywhere handles SSL
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True