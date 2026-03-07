-- Agregar columna tipo_perfil a la tabla perfiles
ALTER TABLE perfiles ADD COLUMN tipo_perfil TEXT NULL;

-- Opcional: Actualizar perfiles existentes según su uso
-- UPDATE perfiles SET tipo_perfil = 'Marco' WHERE NRO_PERFIL IN (SELECT DISTINCT Perfil FROM despiece_perfiles_marcos);
-- UPDATE perfiles SET tipo_perfil = 'Hojas' WHERE NRO_PERFIL IN (SELECT DISTINCT Perfil FROM despiece_perfiles_hojas);
