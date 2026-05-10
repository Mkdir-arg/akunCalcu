# Despliegue en PythonAnywhere

## 1. Subir archivos
- Sube todo el proyecto a `/home/yourusername/akunCalcu/`

## 2. Instalar dependencias
```bash
cd /home/yourusername/akunCalcu
python3.10 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements_prod.txt
```

## 3. Configurar base de datos
- Crear base de datos MySQL: `yourusername$akunacalc`
- Actualizar credenciales en `settings_prod.py`

## 4. Ejecutar migraciones
```bash
cd /home/yourusername/akunCalcu/akuna_calc
python manage.py migrate --settings=akuna_calc.settings_prod
```

## 5. Recolectar archivos estáticos
```bash
python manage.py collectstatic --noinput --settings=akuna_calc.settings_prod
```

## 6. Crear superusuario
```bash
python manage.py createsuperuser --settings=akuna_calc.settings_prod
```

## 7. Cargar productos
```bash
python manage.py seed_productos --settings=akuna_calc.settings_prod
```

## 8. Configurar Web App
- Source code: `/home/yourusername/akunCalcu/akuna_calc`
- WSGI file: `/home/yourusername/akunCalcu/akuna_calc/wsgi_prod.py`
- Static files: URL `/static/` → Directory `/home/yourusername/akunCalcu/akuna_calc/staticfiles`
- Virtualenv: `/home/yourusername/akunCalcu/.venv`

## 9. Reemplazar en archivos:
- `yourusername` → tu usuario de PythonAnywhere
- `your_db_password` → tu contraseña de base de datos