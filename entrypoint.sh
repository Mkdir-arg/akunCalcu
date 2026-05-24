#!/bin/sh
set -e

is_truthy() {
  case "$1" in
    true|True|TRUE|1|yes|Yes|YES|on|On|ON)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

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
  db_wait_timeout="${DB_WAIT_TIMEOUT:-}"
  if [ -z "$db_wait_timeout" ]; then
    if is_truthy "$DEBUG"; then
      db_wait_timeout="0"
    else
      db_wait_timeout="60"
    fi
  fi

  echo "Esperando MySQL en ${DB_HOST}:${DB_PORT} (timeout ${db_wait_timeout}s)..."
  wait_started_at=$(date +%s)
  while ! nc -z -w 1 "$DB_HOST" "$DB_PORT"; do
    current_time=$(date +%s)
    elapsed_seconds=$((current_time - wait_started_at))

    if [ "$db_wait_timeout" -gt 0 ] && [ "$elapsed_seconds" -ge "$db_wait_timeout" ]; then
      echo "MySQL sigue inaccesible tras ${elapsed_seconds}s; continúo arranque de web sin bloquear healthcheck."
      break
    fi

    echo "MySQL no disponible todavía, reintentando..."
    sleep 2
  done
fi

run_migrations_on_startup="${RUN_MIGRATIONS_ON_STARTUP:-}"
if [ -z "$run_migrations_on_startup" ]; then
  if is_truthy "$DEBUG"; then
    run_migrations_on_startup="true"
  else
    run_migrations_on_startup="false"
  fi
fi

if is_truthy "$run_migrations_on_startup"; then
  echo "Ejecutando migraciones..."
  python manage.py migrate --noinput --fake-initial
else
  echo "Saltando migraciones al arranque (RUN_MIGRATIONS_ON_STARTUP=${run_migrations_on_startup})"
fi

create_superuser_on_startup="${CREATE_SUPERUSER_ON_STARTUP:-}"
if [ -z "$create_superuser_on_startup" ]; then
  if is_truthy "$DEBUG"; then
    create_superuser_on_startup="true"
  else
    create_superuser_on_startup="false"
  fi
fi

if is_truthy "$create_superuser_on_startup"; then
  echo "Creando superusuario (si no existe)..."
  python manage.py shell -c "from django.contrib.auth import get_user_model; import os; User = get_user_model(); username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin'); email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com'); password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123'); exists = User.objects.filter(username=username).exists(); print(f'Superusuario {username} ya existe' if exists else f'Superusuario {username} creado'); None if exists else User.objects.create_superuser(username=username, email=email, password=password)"
else
  echo "Saltando creación de superusuario al arranque (CREATE_SUPERUSER_ON_STARTUP=${create_superuser_on_startup})"
fi

PORT="${PORT:-8000}"
GUNICORN_WORKERS="${GUNICORN_WORKERS:-3}"
GUNICORN_TIMEOUT="${GUNICORN_TIMEOUT:-30}"

if [ "$DEBUG" = "true" ] || [ "$DEBUG" = "True" ] || [ "$DEBUG" = "1" ]; then
  echo "Modo DEBUG: usando runserver para hot reload"
  exec python manage.py runserver 0.0.0.0:${PORT}
else
  echo "Modo producción: usando gunicorn en puerto ${PORT} con ${GUNICORN_WORKERS} workers y timeout ${GUNICORN_TIMEOUT}s"
  exec gunicorn akuna_calc.wsgi:application \
    --bind 0.0.0.0:${PORT} \
    --workers "${GUNICORN_WORKERS}" \
    --timeout "${GUNICORN_TIMEOUT}" \
    --access-logfile - \
    --error-logfile -
fi
