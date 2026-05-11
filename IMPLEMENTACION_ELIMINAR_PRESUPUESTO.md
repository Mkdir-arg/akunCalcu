# Implementación de Eliminación Lógica de Presupuestos (Soft Delete)

## Resumen
Se implementó eliminación lógica (soft delete) para presupuestos en lugar de eliminación física. Los presupuestos eliminados se marcan con fecha y usuario, pero permanecen en la base de datos para auditoría y recuperación.

## Ventajas del Soft Delete

✅ **Auditoría completa**: Se registra quién y cuándo eliminó cada presupuesto
✅ **Recuperación**: Posibilidad de restaurar presupuestos eliminados
✅ **Integridad referencial**: No se rompen relaciones con ventas u otros registros
✅ **Historial**: Se mantiene el historial completo para reportes
✅ **Seguridad**: Previene pérdida accidental de datos importantes

## Cambios Realizados

### 1. Modelo (`presupuestos/models.py`)

#### Campos Nuevos:
- **deleted_at** (DateTimeField, nullable): Fecha y hora de eliminación
- **deleted_by** (ForeignKey a User, nullable): Usuario que eliminó el presupuesto

#### Método Nuevo:
- **esta_eliminado()**: Retorna True si el presupuesto está eliminado

### 2. Migración (`presupuestos/migrations/0003_presupuesto_soft_delete.py`)
- Agrega campos `deleted_at` y `deleted_by` a la tabla presupuestos

### 3. Vistas (`presupuestos/views.py`)

#### Vista `eliminar()`:
```python
def eliminar(request, pk):
    presupuesto = get_object_or_404(Presupuesto, pk=pk, deleted_at__isnull=True)
    presupuesto.deleted_at = timezone.now()
    presupuesto.deleted_by = request.user
    presupuesto.save()
```

#### Todas las vistas actualizadas:
Todas las vistas ahora filtran `deleted_at__isnull=True` para excluir presupuestos eliminados:
- `lista()` - Lista solo presupuestos activos
- `detalle()` - No permite ver presupuestos eliminados
- `editar()` - No permite editar presupuestos eliminados
- `agregar_item()` - No permite agregar ítems a presupuestos eliminados
- `actualizar_configuracion_obra()` - No permite modificar presupuestos eliminados
- `eliminar_item()` - No permite eliminar ítems de presupuestos eliminados
- `comentar()` - No permite comentar en presupuestos eliminados
- `cambiar_estado()` - No permite cambiar estado de presupuestos eliminados
- `recibo()` - No genera recibo de presupuestos eliminados
- `pdf()` - No genera PDF de presupuestos eliminados
- **Nueva función**: `eliminar(request, pk)`
  - Requiere POST
  - Requiere login
  - Elimina el presupuesto y todos sus registros relacionados (ítems, comentarios)
  - Muestra mensaje de éxito con el número del presupuesto eliminado
  - Redirige a la lista de presupuestos

### 2. URLs (`presupuestos/urls.py`)
- **Nueva ruta**: `path('<int:pk>/eliminar/', views.eliminar, name='presupuestos-eliminar')`

### 3. Template (`presupuestos/templates/presupuestos/detalle.html`)

#### Botón de Eliminar:
- Agregado en la sección de acciones del header
- Color rojo (bg-red-600) para indicar acción destructiva
- Icono de papelera (fa-trash)
- Visible siempre (no depende del estado del presupuesto)

#### Formulario Oculto:
- Formulario POST para enviar la solicitud de eliminación
- ID: `form-eliminar-presupuesto`
- Incluye CSRF token

#### Función JavaScript:
- `confirmarEliminarPresupuesto()`: Muestra diálogo de confirmación con SweetAlert
- Mensaje de advertencia claro indicando que la acción no se puede deshacer
- Menciona que se eliminarán ítems y comentarios asociados
- Botones: "Sí, eliminar" (rojo) y "Cancelar" (gris)

## Comportamiento

### Flujo de Eliminación:
1. Usuario hace clic en botón "Eliminar"
2. Aparece diálogo de confirmación con SweetAlert
3. Si confirma: Se envía formulario POST a `/presupuestos/<pk>/eliminar/`
4. Backend marca el presupuesto como eliminado:
   - `deleted_at` = fecha y hora actual
   - `deleted_by` = usuario actual
5. Muestra mensaje de éxito
6. Redirige a la lista de presupuestos

### Qué se Conserva:
✅ El presupuesto permanece en la base de datos
✅ Todos los ítems se conservan
✅ Todos los comentarios se conservan
✅ Todas las relaciones se mantienen intactas
✅ Se registra quién y cuándo lo eliminó

### Qué Cambia:
❌ El presupuesto NO aparece en la lista
❌ NO se puede acceder al detalle (404)
❌ NO se puede editar
❌ NO se puede generar PDF
❌ NO se cuenta en los KPIs

### Permisos:
- Requiere estar autenticado (`@login_required`)
- No hay restricción por estado (se puede eliminar incluso si está confirmado)
- No hay restricción por rol (cualquier usuario autenticado puede eliminar)

## Ubicación de los Botones

### En la Lista de Presupuestos:
El botón "Eliminar" (icono de papelera rojo) está en la columna "Acciones" de cada fila:
- **Ver** (azul) - Abre el detalle
- **PDF** (verde) - Descarga el PDF
- **Eliminar** (rojo) - Elimina el presupuesto

### En el Detalle del Presupuesto:
El botón "Eliminar" está en el header, junto a:
- Editar (solo si no está bloqueado)
- Agregar item (solo si no está bloqueado y tiene tipo de obra)
- Presupuesto (PDF)
- Recibo
- **Eliminar** (siempre visible)

## Mensajes de Confirmación

### En la Lista:
```
¿Eliminar presupuesto?

¿Estás seguro de eliminar el presupuesto PRES-2024-001?

Este presupuesto tiene 5 ítems.

Esta acción no se puede deshacer.

[Cancelar]  [Sí, eliminar]
```

### En el Detalle:
```
¿Eliminar presupuesto?

¿Estás seguro de eliminar el presupuesto PRES-2024-001?

Esta acción no se puede deshacer. Se eliminarán todos los 
ítems y comentarios asociados.

[Cancelar]  [Sí, eliminar]
```

## Cómo Restaurar un Presupuesto Eliminado

Para restaurar un presupuesto eliminado, se puede hacer desde el admin de Django o con SQL:

### Opción 1: Desde Django Admin
```python
# En el admin, filtrar por deleted_at__isnull=False
# Editar el presupuesto y poner deleted_at = None
```

### Opción 2: Desde SQL
```sql
-- Ver presupuestos eliminados
SELECT id, numero, deleted_at, deleted_by_id 
FROM presupuestos_presupuesto 
WHERE deleted_at IS NOT NULL;

-- Restaurar un presupuesto específico
UPDATE presupuestos_presupuesto 
SET deleted_at = NULL, deleted_by_id = NULL 
WHERE id = 1;
```

### Opción 3: Vista de Restauración (Futura Mejora)
Se puede crear una vista para que usuarios staff puedan restaurar presupuestos:
```python
@login_required
@user_passes_test(lambda u: u.is_staff)
@require_POST
def restaurar(request, pk):
    presupuesto = get_object_or_404(Presupuesto, pk=pk, deleted_at__isnull=False)
    presupuesto.deleted_at = None
    presupuesto.deleted_by = None
    presupuesto.save(update_fields=['deleted_at', 'deleted_by'])
    messages.success(request, f'Presupuesto {presupuesto.numero} restaurado.')
    return redirect('presupuestos:presupuestos-detalle', pk=pk)
```

## Testing Recomendado

1. Eliminar presupuesto sin ítems
2. Eliminar presupuesto con múltiples ítems
3. Eliminar presupuesto con comentarios
4. Verificar que los ítems se eliminan en cascada
5. Verificar que los comentarios se eliminan en cascada
6. Verificar redirección a lista después de eliminar
7. Verificar mensaje de éxito
8. Cancelar eliminación y verificar que no se elimina

## Archivos Modificados

- `presupuestos/models.py` - Campos `deleted_at` y `deleted_by`, método `esta_eliminado()`
- `presupuestos/migrations/0003_presupuesto_soft_delete.py` - Migración para soft delete
- `presupuestos/views.py` - Vista `eliminar()` con soft delete, todas las vistas filtran eliminados
- `presupuestos/urls.py` - Ruta para eliminación
- `presupuestos/templates/presupuestos/lista.html` - Botón y JavaScript en tabla
- `presupuestos/templates/presupuestos/detalle.html` - Botón, formulario y JavaScript en header

## Consultas Útiles

### Ver presupuestos eliminados:
```sql
SELECT 
    p.id,
    p.numero,
    c.nombre,
    c.apellido,
    p.total,
    p.deleted_at,
    u.username as deleted_by
FROM presupuestos_presupuesto p
JOIN comercial_cliente c ON p.cliente_id = c.id
LEFT JOIN auth_user u ON p.deleted_by_id = u.id
WHERE p.deleted_at IS NOT NULL
ORDER BY p.deleted_at DESC;
```

### Contar presupuestos eliminados:
```sql
SELECT COUNT(*) as eliminados
FROM presupuestos_presupuesto
WHERE deleted_at IS NOT NULL;
```

### Ver quién ha eliminado más presupuestos:
```sql
SELECT 
    u.username,
    COUNT(*) as cantidad_eliminados
FROM presupuestos_presupuesto p
JOIN auth_user u ON p.deleted_by_id = u.id
WHERE p.deleted_at IS NOT NULL
GROUP BY u.username
ORDER BY cantidad_eliminados DESC;
```

## Notas

- La eliminación es **lógica** (soft delete), no física
- Los datos permanecen en la base de datos para auditoría
- Se puede restaurar un presupuesto eliminado
- Los presupuestos eliminados NO aparecen en ninguna vista
- Los presupuestos eliminados NO se cuentan en KPIs
- Se registra quién y cuándo eliminó cada presupuesto
- Los ítems y comentarios se conservan intactos
- La eliminación no requiere permisos especiales (solo login)
- Se recomienda implementar restricciones adicionales en producción (ej: solo staff puede eliminar)
