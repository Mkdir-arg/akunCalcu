@echo off
echo Iniciando Akuna Calc...
echo.

echo 1. Construyendo contenedores...
docker-compose up --build -d

echo.
echo 2. Esperando a que los servicios estén listos...
timeout /t 10 /nobreak > nul

echo.
echo 3. Ejecutando migraciones...
docker-compose exec web python manage.py migrate

echo.
echo 4. Creando superusuario (opcional)...
echo Para crear un superusuario, ejecuta:
echo docker-compose exec web python manage.py createsuperuser

echo.
echo ========================================
echo Aplicación disponible en:
echo http://localhost:8000
echo.
echo Admin disponible en:
echo http://localhost:8000/admin
echo.
echo Para detener: docker-compose down
echo ========================================