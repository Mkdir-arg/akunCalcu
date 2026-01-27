# 🚀 FASE 1 - FACTURACIÓN ELECTRÓNICA - IMPLEMENTADA

## ✅ LO QUE SE IMPLEMENTÓ

### 1. **Modelos Extendidos**
- ✅ `Cliente`: Agregados campos CUIT, DNI, condición_iva
- ✅ `Cuenta` (Proveedores): Agregados campos CUIT, condición_iva
- ✅ `Producto`: Agregado campo alicuota_iva

### 2. **Nueva App: facturacion/**
- ✅ `PuntoVenta`: Gestión de puntos de venta AFIP
- ✅ `Factura`: Facturas electrónicas A/B/C con CAE
- ✅ `FacturaItem`: Items de factura con IVA discriminado
- ✅ `LibroIVAVentas`: Registro automático para AFIP

### 3. **Servicios AFIP**
- ✅ `AFIPService`: Integración WSFEv1 (MOCK para desarrollo)
- ✅ Solicitud de CAE automática
- ✅ Validación de CUIT
- ✅ Determinación automática tipo factura según cliente

### 4. **Funcionalidades**
- ✅ Crear facturas manualmente
- ✅ Crear facturas desde Ventas existentes
- ✅ Cálculo automático de IVA por alícuota
- ✅ Libro IVA Ventas con totales
- ✅ Templates responsive con Tailwind

---

## 📋 PASOS PARA ACTIVAR

### 1. **Crear migraciones**
```bash
cd akuna_calc
python manage.py makemigrations comercial
python manage.py makemigrations productos
python manage.py makemigrations facturacion
```

### 2. **Aplicar migraciones**
```bash
python manage.py migrate
```

### 3. **Crear Punto de Venta inicial**
```bash
python manage.py shell
```
```python
from facturacion.models import PuntoVenta
PuntoVenta.objects.create(numero=1, nombre="Principal", activo=True)
exit()
```

### 4. **Actualizar datos existentes (opcional)**
```bash
python manage.py shell
```
```python
# Agregar alícuota IVA a productos existentes
from productos.models import Producto
Producto.objects.all().update(alicuota_iva=21.00)

# Agregar condición IVA a clientes existentes
from comercial.models import Cliente
Cliente.objects.all().update(condicion_iva='CF')  # Consumidor Final por defecto

exit()
```

---

## 🎯 CÓMO USAR

### **Opción 1: Crear Factura desde Venta**
1. Ir a una Venta existente
2. Agregar botón "Generar Factura Electrónica" (ver integración abajo)
3. Se crea automáticamente con CAE

### **Opción 2: Crear Factura Manual**
1. Ir a: http://localhost:8000/facturacion/
2. Click en "Nueva Factura"
3. Seleccionar cliente, punto de venta
4. Agregar items
5. Confirmar → Se solicita CAE automáticamente

### **Ver Libro IVA**
- http://localhost:8000/facturacion/libro-iva-ventas/
- Filtrar por período
- Ver totales por alícuota

---

## 🔗 INTEGRACIÓN CON VENTAS

### Agregar botón en template de Venta:

**Archivo:** `comercial/templates/comercial/detalle_venta.html`

```html
<!-- Agregar después de los datos de la venta -->
{% if venta.con_factura %}
    {% if venta.factura_electronica %}
        <div class="mt-4 p-4 bg-green-50 rounded-lg">
            <h3 class="font-semibold text-green-800 mb-2">
                <i class="fas fa-check-circle mr-2"></i>Factura Electrónica Generada
            </h3>
            <p class="text-sm text-gray-700">
                Factura: {{ venta.factura_electronica.get_numero_completo }}<br>
                CAE: {{ venta.factura_electronica.cae }}<br>
                Total: ${{ venta.factura_electronica.total|floatformat:2 }}
            </p>
            <a href="{% url 'facturacion:detalle_factura' venta.factura_electronica.id %}" 
               class="mt-2 inline-block bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded">
                <i class="fas fa-file-invoice mr-2"></i>Ver Factura
            </a>
        </div>
    {% else %}
        <div class="mt-4">
            <a href="{% url 'facturacion:crear_factura_desde_venta' venta.id %}" 
               class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg inline-block">
                <i class="fas fa-file-invoice-dollar mr-2"></i>Generar Factura Electrónica
            </a>
        </div>
    {% endif %}
{% endif %}
```

---

## ⚙️ CONFIGURACIÓN AFIP (PRODUCCIÓN)

### Para usar AFIP real (no MOCK):

1. **Obtener certificado digital AFIP**
   - Ingresar a AFIP con clave fiscal
   - Generar certificado para WSFEv1
   - Descargar .crt y .key

2. **Instalar dependencias**
```bash
pip install zeep
pip install cryptography
```

3. **Configurar en `facturacion/afip_service.py`**
```python
# Descomentar y configurar:
from zeep import Client
from zeep.wsse.signature import Signature

class AFIPService:
    def __init__(self):
        self.cert_path = '/path/to/certificado.crt'
        self.key_path = '/path/to/private.key'
        self.wsdl = 'https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL'
        # ... implementar autenticación real
```

---

## 📊 DATOS DE PRUEBA

### Crear clientes de prueba:
```python
from comercial.models import Cliente

# Cliente Responsable Inscripto
Cliente.objects.create(
    nombre="Juan",
    apellido="Pérez",
    razon_social="Pérez SA",
    cuit="20123456789",
    condicion_iva="RI",
    direccion="Av. Corrientes 1234",
    localidad="CABA",
    email="juan@perez.com"
)

# Cliente Consumidor Final
Cliente.objects.create(
    nombre="María",
    apellido="González",
    dni="12345678",
    condicion_iva="CF",
    direccion="Calle Falsa 123",
    localidad="Buenos Aires",
    email="maria@gmail.com"
)
```

---

## 🐛 TROUBLESHOOTING

### Error: "No module named 'facturacion'"
```bash
# Verificar que esté en INSTALLED_APPS
python manage.py check
```

### Error: "PuntoVenta matching query does not exist"
```bash
# Crear punto de venta
python manage.py shell
from facturacion.models import PuntoVenta
PuntoVenta.objects.create(numero=1, nombre="Principal", activo=True)
```

### Error en migraciones
```bash
# Resetear migraciones (solo desarrollo)
python manage.py migrate facturacion zero
rm facturacion/migrations/0*.py
python manage.py makemigrations facturacion
python manage.py migrate
```

---

## 📈 PRÓXIMOS PASOS (FASE 2)

- [ ] Módulo de Contabilidad
- [ ] Asientos automáticos desde facturas
- [ ] Plan de cuentas
- [ ] Balance y Estado de Resultados
- [ ] Ajuste por inflación

---

## 📞 SOPORTE

**Implementación MOCK**: Sistema funcional para desarrollo
**Producción**: Requiere certificados AFIP reales

**Estado**: ✅ FASE 1 COMPLETA - LISTA PARA TESTING
