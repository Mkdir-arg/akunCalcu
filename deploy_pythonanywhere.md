# Despliegue en PythonAnywhere

## 1. Subir archivos
- Sube todo el proyecto a `/home/yourusername/akunCalcu/`

## 2. Instalar dependencias
```bash
pip3.10 install --user -r requirements_prod.txt
```

## 3. Configurar base de datos
- Crear base de datos MySQL: `yourusername$akunacalc`
- Actualizar credenciales en `settings_prod.py`

## 4. Ejecutar migraciones
```bash
cd /home/yourusername/akunCalcu/akuna_calc
python3.10 manage.py migrate --settings=akuna_calc.settings_prod
```

## 5. Recolectar archivos estáticos
```bash
python3.10 manage.py collectstatic --noinput --settings=akuna_calc.settings_prod
```

## 6. Crear superusuario
```bash
python3.10 manage.py createsuperuser --settings=akuna_calc.settings_prod
```

## 7. Cargar productos
```bash
python3.10 manage.py seed_productos --settings=akuna_calc.settings_prod
```

## 8. Configurar Web App
- Source code: `/home/yourusername/akunCalcu/akuna_calc`
- WSGI file: `/home/yourusername/akunCalcu/akuna_calc/wsgi_prod.py`
- Static files: URL `/static/` → Directory `/home/yourusername/akunCalcu/akuna_calc/staticfiles`

## 9. Reemplazar en archivos:
- `yourusername` → tu usuario de PythonAnywhere
- `your_db_password` → tu contraseña de base de datos