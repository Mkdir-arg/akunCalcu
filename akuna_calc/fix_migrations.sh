#!/bin/bash

echo "Aplicando fix de migración..."

# Marcar migración como aplicada sin ejecutarla
python manage.py migrate comercial 0012_pagoventa_con_factura --fake

echo "Ejecutando migraciones restantes..."
python manage.py migrate

echo "Recalculando saldos..."
python manage.py recalcular_saldos

echo "¡Proceso completado!"
