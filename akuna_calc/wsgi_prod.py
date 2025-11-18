import os
import sys

# Add your project directory to sys.path
path = '/home/yourusername/akunCalcu/akuna_calc'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'akuna_calc.settings_prod')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()