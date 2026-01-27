@echo off
echo ========================================
echo   FASE 1 - FACTURACION ELECTRONICA
echo   Instalacion y Configuracion
echo ========================================
echo.

cd akuna_calc

echo [1/5] Creando migraciones...
python manage.py makemigrations comercial
python manage.py makemigrations productos
python manage.py makemigrations facturacion

echo.
echo [2/5] Aplicando migraciones...
python manage.py migrate

echo.
echo [3/5] Configurando datos iniciales...
python manage.py setup_facturacion

echo.
echo [4/5] Creando superusuario (si no existe)...
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', 'admin123')"

echo.
echo [5/5] Recolectando archivos estaticos...
python manage.py collectstatic --noinput

echo.
echo ========================================
echo   INSTALACION COMPLETADA
echo ========================================
echo.
echo Accede a:
echo   - Facturas: http://localhost:8000/facturacion/
echo   - Admin: http://localhost:8000/admin/
echo   - Usuario: admin / admin123
echo.
echo Para iniciar el servidor:
echo   python manage.py runserver
echo.
pause
