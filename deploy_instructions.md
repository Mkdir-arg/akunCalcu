# Instrucciones de Despliegue - PythonAnywhere

## Configuración que FUNCIONA

### 1. Archivos a personalizar:
- Reemplazar `YOURUSERNAME` por tu usuario de PythonAnywhere
- Reemplazar `YOUR_DB_PASSWORD` por tu contraseña de base de datos

### 2. WSGI File (`/var/www/username_pythonanywhere_com_wsgi.py`):
```python
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
```

### 3. Base de datos:
- Nombre: `YOURUSERNAME$default` (usar la base por defecto)
- Usuario: `YOURUSERNAME`
- Host: `YOURUSERNAME.mysql.pythonanywhere-services.com`

### 4. Web App Configuration:
- **Source code:** `/home/YOURUSERNAME/akunCalcu/akuna_calc`
- **Static files:** `/static/` → `/home/YOURUSERNAME/akunCalcu/akuna_calc/staticfiles`
- **Virtualenv:** (dejar vacío)

### 5. Comandos de despliegue:
```bash
cd akunCalcu/akuna_calc
python3.10 manage.py migrate --settings=akuna_calc.settings_prod
python3.10 manage.py collectstatic --noinput --settings=akuna_calc.settings_prod
python3.10 manage.py createsuperuser --settings=akuna_calc.settings_prod
python3.10 manage.py seed_productos --settings=akuna_calc.settings_prod
```

### 6. Después de cada cambio:
- Hacer **Reload** en el Web App
- Visitar: `yourusername.pythonanywhere.com`