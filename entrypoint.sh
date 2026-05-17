#!/bin/sh
set -e

if [ -n "$DB_HOST" ] && [ -n "$DB_PORT" ]; then
  echo "Esperando MySQL en ${DB_HOST}:${DB_PORT}..."
  while ! nc -z "$DB_HOST" "$DB_PORT"; do
    echo "MySQL no disponible todavía, reintentando..."
    sleep 2
  done
fi

echo "Ejecutando migraciones..."
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

PORT="${PORT:-8000}"

if [ "$DEBUG" = "true" ] || [ "$DEBUG" = "True" ] || [ "$DEBUG" = "1" ]; then
  echo "Modo DEBUG: usando runserver para hot reload"
  exec python manage.py runserver 0.0.0.0:${PORT}
else
  echo "Modo producción: usando gunicorn en puerto ${PORT}"
  exec gunicorn akuna_calc.wsgi:application \
    --bind 0.0.0.0:${PORT} \
    --workers 3 \
    --access-logfile - \
    --error-logfile -
fi
