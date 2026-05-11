# Resumen de Cambios en Presupuestos

## 1. IVA 21% ✅

### Archivos:
- `presupuestos/models.py`
- `presupuestos/forms.py`
- `presupuestos/templates/presupuestos/detalle.html`
- `presupuestos/migrations/0002_presupuesto_aplicar_iva.py`

### Funcionalidad:
- Checkbox "Aplicar IVA 21%" en configuración de obra
- Cálculo automático: `Total = Subtotal + (Subtotal × 0.21)`
- Desglose visible en resumen de ítems y panel lateral

### Migración:
```bash
python3 manage.py migrate presupuestos
```

---

## 2. Eliminación Lógica (Soft Delete) ✅

### Archivos:
- `presupuestos/models.py` - Campos `deleted_at` y `deleted_by`
- `presupuestos/views.py` - Todas las vistas filtran eliminados
- `presupuestos/templates/presupuestos/lista.html` - Botón eliminar
- `presupuestos/templates/presupuestos/detalle.html` - Botón eliminar
- `presupuestos/urls.py` - Ruta de eliminación
- `presupuestos/migrations/0003_presupuesto_soft_delete.py`

### Funcionalidad:
- Botón "Eliminar" en lista y detalle
- Confirmación con SweetAlert
- Marca presupuesto como eliminado (no lo borra)
- Registra quién y cuándo eliminó
- Posibilidad de restaurar

### Migración:
```bash
python3 manage.py migrate presupuestos
```

---

## Pasos para Aplicar en Servidor

### 1. Subir archivos modificados:
```bash
# Modelos y migraciones
presupuestos/models.py
presupuestos/migrations/0002_presupuesto_aplicar_iva.py
presupuestos/migrations/0003_presupuesto_soft_delete.py

# Vistas y URLs
presupuestos/views.py
presupuestos/urls.py
presupuestos/forms.py

# Templates
presupuestos/templates/presupuestos/detalle.html
presupuestos/templates/presupuestos/lista.html
```

### 2. Ejecutar migraciones:
```bash
cd ~/akunCalcu/akuna_calc
python3 manage.py migrate presupuestos
```

### 3. Verificar migraciones:
```bash
python3 manage.py showmigrations presupuestos
```

Debería mostrar:
```
presupuestos
 [X] 0001_initial
 [X] 0002_presupuesto_aplicar_iva
 [X] 0003_presupuesto_soft_delete
```

### 4. Recargar aplicación:
- Ir al dashboard de PythonAnywhere
- Hacer clic en "Reload" en la sección Web

---

## Testing Recomendado

### IVA:
1. ✅ Crear presupuesto nuevo
2. ✅ Marcar checkbox "Aplicar IVA 21%"
3. ✅ Agregar ítems
4. ✅ Verificar que el IVA se calcula correctamente
5. ✅ Verificar que aparece en el resumen
6. ✅ Desmarcar checkbox y verificar que se recalcula

### Eliminación:
1. ✅ Eliminar presupuesto desde lista
2. ✅ Verificar que no aparece en lista
3. ✅ Verificar que no se puede acceder al detalle (404)
4. ✅ Verificar en base de datos que tiene deleted_at
5. ✅ Restaurar desde SQL y verificar que vuelve a aparecer
6. ✅ Eliminar presupuesto desde detalle
7. ✅ Verificar mensaje de confirmación

---

## Consultas SQL Útiles

### Ver presupuestos eliminados:
```sql
SELECT 
    p.id,
    p.numero,
    p.total,
    p.deleted_at,
    u.username as deleted_by
FROM presupuestos_presupuesto p
LEFT JOIN auth_user u ON p.deleted_by_id = u.id
WHERE p.deleted_at IS NOT NULL
ORDER BY p.deleted_at DESC;
```

### Restaurar presupuesto:
```sql
UPDATE presupuestos_presupuesto 
SET deleted_at = NULL, deleted_by_id = NULL 
WHERE id = 1;
```

### Ver presupuestos con IVA:
```sql
SELECT 
    numero,
    total,
    aplicar_iva
FROM presupuestos_presupuesto
WHERE aplicar_iva = 1 AND deleted_at IS NULL;
```

---

## Documentación Completa

- `IMPLEMENTACION_IVA_PRESUPUESTOS.md` - Detalles de IVA
- `IMPLEMENTACION_ELIMINAR_PRESUPUESTO.md` - Detalles de eliminación lógica

---

## Notas Importantes

⚠️ **IVA**:
- El IVA se aplica sobre el subtotal (ítems + recargos)
- Solo se muestra cuando está activado
- Se puede activar/desactivar mientras el presupuesto no esté bloqueado

⚠️ **Eliminación**:
- Es eliminación LÓGICA, no física
- Los datos permanecen en la base de datos
- Se puede restaurar manualmente
- Se registra auditoría completa
- Considerar agregar restricción de permisos en producción

⚠️ **Migraciones**:
- Ejecutar en orden: 0002 primero, luego 0003
- Hacer backup antes de migrar en producción
- Verificar que las migraciones se aplicaron correctamente
