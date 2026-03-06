@echo off
echo Recalculando saldos de todas las ventas...
docker-compose exec web python manage.py recalcular_saldos
echo.
echo Proceso completado.
pause
