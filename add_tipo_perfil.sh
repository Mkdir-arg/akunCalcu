#!/bin/bash
# Script para agregar columna tipo_perfil a la tabla perfiles

mysql -u akun_admin -p'Akun2024!' akun_admin$akuna_calc << EOF
ALTER TABLE perfiles ADD COLUMN tipo_perfil TEXT NULL;
SELECT 'Columna tipo_perfil agregada exitosamente' AS resultado;
EOF
