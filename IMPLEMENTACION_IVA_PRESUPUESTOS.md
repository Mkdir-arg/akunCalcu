# Implementación de IVA 21% en Presupuestos

## Resumen
Se agregó la funcionalidad para aplicar IVA del 21% a los presupuestos de forma opcional mediante un checkbox en la configuración de obra.

## Cambios Realizados

### 1. Modelo (`presupuestos/models.py`)
- **Campo nuevo**: `aplicar_iva` (BooleanField, default=False)
- **Método nuevo**: `get_subtotal_sin_iva()` - Calcula subtotal sin IVA
- **Método nuevo**: `get_iva()` - Calcula el 21% de IVA si está activado
- **Método actualizado**: `recalcular_total()` - Ahora incluye IVA en el cálculo del total

### 2. Migración (`presupuestos/migrations/0002_presupuesto_aplicar_iva.py`)
- Agrega el campo `aplicar_iva` a la tabla de presupuestos

### 3. Formulario (`presupuestos/forms.py`)
- **PresupuestoConfiguracionObraForm**: Agregado campo `aplicar_iva` con widget CheckboxInput

### 4. Template (`presupuestos/templates/presupuestos/detalle.html`)

#### Panel de Configuración de Obra:
- Agregado checkbox "Aplicar IVA 21%" con descripción
- Ubicado después de los campos de recargo, separado con borde superior

#### Sección de Items (Resumen inferior):
- Muestra línea "IVA (21%): $X.XX" cuando `aplicar_iva` es True
- Se muestra entre los recargos y el total

#### Panel Lateral de Resumen:
- Muestra línea "IVA (21%): $X.XX" cuando `aplicar_iva` es True
- Se muestra antes del total final

## Cálculo del Total

### Sin IVA (aplicar_iva = False):
```
Total = Subtotal Items + Recargo Obra Nueva
```

### Con IVA (aplicar_iva = True):
```
Subtotal = Subtotal Items + Recargo Obra Nueva
IVA = Subtotal × 0.21
Total = Subtotal + IVA
```

## Visualización

### Ejemplo con IVA activado:
```
Subtotal ítems:           $100,000.00
Recargo obra nueva:        $10,000.00
IVA (21%):                 $23,100.00
─────────────────────────────────────
Total presupuesto:        $133,100.00
```

### Ejemplo sin IVA:
```
Subtotal ítems:           $100,000.00
Recargo obra nueva:        $10,000.00
─────────────────────────────────────
Total presupuesto:        $110,000.00
```

## Pasos para Aplicar en Servidor

1. **Subir archivos modificados**:
   - `presupuestos/models.py`
   - `presupuestos/forms.py`
   - `presupuestos/templates/presupuestos/detalle.html`
   - `presupuestos/migrations/0002_presupuesto_aplicar_iva.py`

2. **Ejecutar migración**:
   ```bash
   cd ~/akunCalcu/akuna_calc
   python3 manage.py migrate presupuestos
   ```

3. **Recargar aplicación**:
   - Ir al dashboard de PythonAnywhere
   - Hacer clic en "Reload" en la sección Web

## Uso

1. Abrir un presupuesto (ej: https://akun.pythonanywhere.com/presupuestos/1/)
2. En el panel "Configuración de obra" (lateral derecho)
3. Marcar el checkbox "Aplicar IVA 21%"
4. Hacer clic en "Guardar configuración"
5. El total se recalculará automáticamente incluyendo el IVA
6. El IVA se mostrará desglosado en el resumen de items y en el panel lateral

## Notas Importantes

- El IVA se aplica sobre el subtotal (items + recargos)
- El checkbox solo está disponible cuando el presupuesto NO está bloqueado
- El IVA se muestra solo cuando está activado (no se muestra línea si es $0)
- El recálculo del total es automático al guardar la configuración
- El IVA NO se incluye en el recargo de renovación (se aplica después)

## Compatibilidad

- Los presupuestos existentes tendrán `aplicar_iva = False` por defecto
- No afecta presupuestos ya confirmados o cancelados
- El campo es opcional y puede activarse/desactivarse en cualquier momento (mientras el presupuesto no esté bloqueado)
