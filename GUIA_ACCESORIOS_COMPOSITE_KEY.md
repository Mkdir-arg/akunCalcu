# Guía: Permitir Códigos Duplicados en Accesorios con Diferentes Tipos

## Resumen
Cambiar la PRIMARY KEY de la tabla `accesorios` de solo `codigo` a una clave compuesta `(codigo, tipo)` para permitir el mismo código en diferentes tipos (ej: E69 tipo "hoja" y E69 tipo "marco").

## Pasos a Seguir

### 1. Ejecutar Script SQL en MySQL

Conectarse a la base de datos MySQL y ejecutar:

```sql
USE akuna_calc;

-- Eliminar PRIMARY KEY actual
ALTER TABLE accesorios DROP PRIMARY KEY;

-- Agregar nueva PRIMARY KEY compuesta
ALTER TABLE accesorios ADD PRIMARY KEY (COD_PARTE, Tipo);
```

**IMPORTANTE**: Este cambio afectará la estructura de la base de datos. Asegúrate de hacer un backup antes.

### 2. Archivos Modificados

Los siguientes archivos ya fueron actualizados en tu repositorio local:

#### `akuna_calc/pricing/models.py`
- Eliminado `primary_key=True` del campo `codigo`
- Agregado `unique_together = [['codigo', 'tipo']]` en Meta
- Actualizado `__str__` para mostrar el tipo: `"E69 (hoja) - Descripción"`

#### `akuna_calc/pricing/config_views.py`
- Función `_save_accesorio_edit()` ahora recibe `old_codigo` y `old_tipo`
- Vista `accesorio_edit()` ahora recibe parámetros `codigo` y `tipo`
- Vista `accesorio_delete()` ahora recibe parámetros `codigo` y `tipo`
- Actualizada lógica para comparar ambos campos al decidir si eliminar/recrear

#### `akuna_calc/pricing/urls.py`
- URL de editar: `config/accesorios/<str:codigo>/<str:tipo>/editar/`
- URL de eliminar: `config/accesorios/<str:codigo>/<str:tipo>/eliminar/`

#### `akuna_calc/pricing/templates/pricing/config/accesorios.html`
- Enlaces de editar y eliminar ahora pasan ambos parámetros
- Mensaje de confirmación muestra "E69 (hoja)" en lugar de solo "E69"

### 3. Subir Archivos al Servidor

Subir estos archivos actualizados a PythonAnywhere:
- `akuna_calc/pricing/models.py`
- `akuna_calc/pricing/config_views.py`
- `akuna_calc/pricing/urls.py`
- `akuna_calc/pricing/templates/pricing/config/accesorios.html`

### 4. Recargar Aplicación

En PythonAnywhere:
1. Ir al dashboard de Web
2. Hacer clic en "Reload" para aplicar los cambios

### 5. Verificar Funcionamiento

Después de aplicar los cambios:

1. **Crear accesorios con mismo código pero diferente tipo**:
   - Crear: E69 tipo "hoja"
   - Crear: E69 tipo "marco"
   - Ambos deberían coexistir sin error

2. **Editar accesorios**:
   - Cambiar código de E-69 a E69 (mismo tipo) → debería funcionar
   - Cambiar tipo de "hoja" a "marco" → debería funcionar
   - Cambiar ambos → debería funcionar

3. **Verificar listado**:
   - Ambos E69 deberían aparecer en la lista
   - Cada uno con su tipo visible

## Consideraciones Importantes

### Datos Existentes
- Si ya existen accesorios con códigos duplicados en diferentes tipos, el cambio de PRIMARY KEY funcionará sin problemas
- Si existen duplicados con el MISMO tipo, el ALTER TABLE fallará. En ese caso, primero debes limpiar los duplicados

### Referencias en Otras Tablas
Las tablas de despiece (DespieceAccesoriosMarco, DespieceAccesoriosHoja, etc.) solo guardan el `codigo` del accesorio, no el `tipo`. Esto significa que:
- Las referencias seguirán funcionando
- Al actualizar referencias con `_rename_accesorio_codigo_references()`, se actualizarán todos los registros que usen ese código, independientemente del tipo

### Validación en Formularios
Los formularios ya están configurados para manejar ambos campos (codigo y tipo), por lo que no requieren cambios adicionales.

## Rollback (Si es necesario)

Si necesitas revertir los cambios:

```sql
USE akuna_calc;

-- Eliminar PRIMARY KEY compuesta
ALTER TABLE accesorios DROP PRIMARY KEY;

-- Restaurar PRIMARY KEY simple
ALTER TABLE accesorios ADD PRIMARY KEY (COD_PARTE);
```

Y revertir los archivos Python a la versión anterior.

## Testing Recomendado

1. Crear accesorio: E69 tipo "hoja"
2. Crear accesorio: E69 tipo "marco"
3. Editar E69 (hoja) → cambiar a E70 (hoja)
4. Editar E69 (marco) → cambiar tipo a "hoja" (ahora sería E69 hoja)
5. Verificar que no hay conflictos
6. Desactivar un accesorio
7. Verificar que el otro con mismo código sigue activo

## Notas Finales

- La clave compuesta permite códigos duplicados SOLO si tienen diferente tipo
- E69 (hoja) y E69 (marco) pueden coexistir
- E69 (hoja) y E69 (hoja) NO pueden coexistir (error de PRIMARY KEY)
- El campo `tipo` puede ser NULL, pero si dos registros tienen el mismo código y ambos tienen tipo NULL, habrá conflicto
