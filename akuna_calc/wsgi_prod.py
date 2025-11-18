import os
import sys
import pymysql

# Use PyMySQL instead of mysqlclient
pymysql.install_as_MySQLdb()

# Add your project directory to sys.path
path = '/home/YOURUSERNAME/akunCalcu/akuna_calc'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'akuna_calc.settings_prod')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()