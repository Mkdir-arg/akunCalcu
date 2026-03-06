-- Marcar migración 0012 como aplicada (la columna ya existe en la BD)
INSERT INTO django_migrations (app, name, applied) 
VALUES ('comercial', '0012_pagoventa_con_factura', NOW())
ON DUPLICATE KEY UPDATE applied = NOW();

-- Verificar
SELECT * FROM django_migrations WHERE app = 'comercial' ORDER BY id;
