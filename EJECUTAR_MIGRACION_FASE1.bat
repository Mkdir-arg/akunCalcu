@echo off
echo ========================================
echo   FASE 1 - CORRECCIONES CRITICAS
echo   Migraciones y Actualizaciones
echo ========================================
echo.

cd akuna_calc

echo [1/3] Creando migraciones...
python manage.py makemigrations comercial

echo.
echo [2/3] Aplicando migraciones...
python manage.py migrate

echo.
echo [3/3] Actualizando datos existentes...
python manage.py shell -c "from comercial.models import Venta, Compra; Venta.objects.filter(con_factura=False).update(con_factura=True); Compra.objects.update(con_factura=True); print('Datos actualizados correctamente')"

echo.
echo ========================================
echo   MIGRACION COMPLETADA
echo ========================================
echo.
echo CAMBIOS APLICADOS:
echo   - numero_pedido ahora permite duplicados (PVC, PVC, etc.)
echo   - Campo monto_cobrado eliminado
echo   - Saldo = Total - Seña (automatico)
echo   - Agregado con_factura en Ventas y Compras
echo   - Agregado numero_factura en Compras
echo   - Decimales se muestran correctamente (.00)
echo.
pause
