# Soporte de Dólares en Items PVC - Presupuestos

## Resumen
Los items PVC ahora soportan ingreso de valores en dólares, igual que el módulo de ventas.

## Cambios Realizados

### 1. Vista `agregar_item` (`views.py`)
Se modificó para capturar y procesar datos de USD cuando es un item PVC:

**Nuevos campos capturados:**
- `valor_en_dolares`: Boolean que indica si el valor está en USD
- `valor_usd`: Monto en dólares
- `cotizacion_usd`: Cotización del dólar utilizada

**Procesamiento:**
```python
if valor_en_dolares:
    resultado_json['valor_en_dolares'] = True
    resultado_json['valor_usd'] = valor_usd
    resultado_json['cotizacion_usd'] = cotizacion_usd
```

### 2. Template `detalle.html`

#### Formulario HTML Oculto
Agregados 3 campos hidden para enviar datos USD:
- `f-pvc-valor-en-dolares`
- `f-pvc-valor-usd`
- `f-pvc-cotizacion-usd`

#### Componente React `FormularioPVC`

**Estado agregado:**
```javascript
const [valorEnDolares, setValorEnDolares] = useState(false);
const [valorUsd, setValorUsd] = useState(0);
const [cotizacionUsd, setCotizacionUsd] = useState(0);
```

**Cálculo automático:**
```javascript
const valorCalculado = valorEnDolares && valorUsd > 0 && cotizacionUsd > 0 
    ? valorUsd * cotizacionUsd 
    : valor;
```

**Validaciones:**
- Si marca USD: valida `valorUsd > 0` y `cotizacionUsd > 0`
- Si no marca USD: valida `valor > 0`

### 3. UI del Formulario

**Checkbox "Valor en dólares":**
- Si está desmarcado: muestra campo "Valor base ($)"
- Si está marcado: muestra dos campos:
  - "Valor en USD"
  - "Cotización USD"
  - Banner informativo con valor calculado en pesos

**Preview del cálculo:**
- Card con gradiente mostrando:
  - Precio unitario con margen
  - Total (si cantidad > 1)
- Se actualiza en tiempo real

## Estructura de Datos

### resultado_json para items PVC con USD
```json
{
  "precio_unitario_base": 150000.00,
  "valor_base": 115384.62,
  "margen": 30,
  "recargo_renovacion_unitario_aplicado": 0,
  "tipo": "pvc_simple",
  "valor_en_dolares": true,
  "valor_usd": 100.00,
  "cotizacion_usd": 1153.85
}
```

### resultado_json para items PVC sin USD
```json
{
  "precio_unitario_base": 150000.00,
  "valor_base": 115384.62,
  "margen": 30,
  "recargo_renovacion_unitario_aplicado": 0,
  "tipo": "pvc_simple"
}
```

## Flujo de Uso

### Caso 1: Ingresar en Pesos
1. Abrir modal de agregar item (presupuesto PVC)
2. Completar descripción, cantidad
3. Dejar desmarcado "Valor en dólares"
4. Ingresar "Valor base ($)"
5. Ajustar "Margen (%)" si es necesario
6. Ver preview del precio
7. Guardar

### Caso 2: Ingresar en Dólares
1. Abrir modal de agregar item (presupuesto PVC)
2. Completar descripción, cantidad
3. **Marcar checkbox "Valor en dólares"**
4. Ingresar "Valor en USD"
5. Ingresar "Cotización USD" (ej: 1150)
6. Ver banner con "Valor calculado en pesos: $XXX.XX"
7. Ajustar "Margen (%)" si es necesario
8. Ver preview del precio final
9. Guardar

## Ejemplo de Cálculo

**Input:**
- Valor en USD: $100
- Cotización: $1,150
- Margen: 30%
- Cantidad: 2

**Cálculo:**
1. Valor en pesos: $100 × 1,150 = $115,000
2. Precio con margen: $115,000 × 1.30 = $149,500
3. Total: $149,500 × 2 = $299,000

**Guardado en DB:**
- `precio_unitario`: $149,500
- `precio_total`: $299,000
- `resultado_json`: incluye `valor_usd: 100` y `cotizacion_usd: 1150`

## Compatibilidad

### Items Existentes
- Items PVC creados antes de esta actualización no tendrán campos USD en `resultado_json`
- Seguirán funcionando correctamente
- Solo mostrarán valor en pesos

### Items Aluminio
- No se ven afectados por estos cambios
- Mantienen su flujo de cotizador completo

### Reportes y PDFs
- Los PDFs usan `precio_unitario` y `precio_total` (ya en pesos)
- No requieren cambios
- La información de USD queda registrada en `resultado_json` para auditoría

## Consideraciones

1. **Trazabilidad:** La información de USD se guarda en `resultado_json` para futuras consultas o auditorías

2. **Cálculos:** Todos los cálculos (recargos, IVA, totales) se hacen sobre valores en pesos

3. **Consistencia:** El comportamiento es idéntico al módulo de ventas

4. **Flexibilidad:** El usuario puede elegir ingresar en pesos o dólares según su conveniencia

## Testing Recomendado

1. ✅ Crear item PVC en pesos → verificar guardado correcto
2. ✅ Crear item PVC en USD → verificar conversión y guardado
3. ✅ Verificar que resultado_json incluye campos USD
4. ✅ Verificar preview en tiempo real del cálculo
5. ✅ Verificar validaciones de campos USD
6. ✅ Verificar que PDF muestra precios correctos
7. ✅ Crear presupuesto con mix de items (pesos y USD)
8. ✅ Verificar totales con recargos e IVA
