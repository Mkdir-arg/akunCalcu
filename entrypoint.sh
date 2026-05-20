#!/bin/sh
set -e

if [ -z "$DB_HOST" ] || [ -z "$DB_PORT" ]; then
  if [ -n "$DATABASE_URL" ]; then
    db_host_from_url=$(python -c "import os; from urllib.parse import urlparse; parsed = urlparse(os.environ.get('DATABASE_URL', '')); print(parsed.hostname or '')")

    db_port_from_url=$(python -c "import os; from urllib.parse import urlparse; parsed = urlparse(os.environ.get('DATABASE_URL', '')); default_port = 3306 if parsed.scheme.startswith('mysql') else ''; print(parsed.port or default_port)")

    if [ -z "$DB_HOST" ] && [ -n "$db_host_from_url" ]; then
      DB_HOST="$db_host_from_url"
    fi

    if [ -z "$DB_PORT" ] && [ -n "$db_port_from_url" ]; then
      DB_PORT="$db_port_from_url"
    fi

    if [ -n "$DB_HOST" ] && [ -n "$DB_PORT" ]; then
      echo "MySQL detectado desde DATABASE_URL en ${DB_HOST}:${DB_PORT}"
    fi
  fi
fi

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
python manage.py shell -c "from django.contrib.auth import get_user_model; import os; User = get_user_model(); username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin'); email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com'); password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123'); exists = User.objects.filter(username=username).exists(); print(f'Superusuario {username} ya existe' if exists else f'Superusuario {username} creado'); None if exists else User.objects.create_superuser(username=username, email=email, password=password)"

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
