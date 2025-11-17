#!/bin/bash
set -e

echo "Esperando MySQL..."
while ! nc -z db 3306; do sleep 1; done

echo "Ejecutando migraciones..."
python manage.py migrate --noinput

echo "Iniciando Django..."
exec python manage.py runserver 0.0.0.0:8000