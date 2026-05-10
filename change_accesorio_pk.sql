-- Script para cambiar PRIMARY KEY de accesorios
-- De: codigo (solo)
-- A: codigo + tipo (compuesta)

USE akuna_calc;

-- 1. Eliminar PRIMARY KEY actual
ALTER TABLE accesorios DROP PRIMARY KEY;

-- 2. Agregar nueva PRIMARY KEY compuesta
ALTER TABLE accesorios ADD PRIMARY KEY (COD_PARTE, Tipo);
