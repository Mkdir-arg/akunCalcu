#!/bin/sh
set -e

echo "Esperando MySQL en ${DB_HOST}:${DB_PORT}..."
while ! nc -z "$DB_HOST" "$DB_PORT"; do
  echo "MySQL no disponible todavía, reintentando..."
  sleep 2
done

echo "Base de datos disponible, ejecutando migraciones..."
python manage.py migrate --noinput

echo "Creando superusuario (si no existe)..."
python manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
import os

User = get_user_model()
username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@example.com")
password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "admin123")

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f"Superusuario {username} creado")
else:
    print(f"Superusuario {username} ya existe")
EOF

echo "Cargando datos iniciales de productos..."
python manage.py seed_productos || echo "seed_productos falló o no existe, continuando..."

echo "Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

echo "Iniciando servidor Django en 0.0.0.0:8000..."
exec python manage.py runserver 0.0.0.0:8000

