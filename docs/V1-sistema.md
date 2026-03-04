# AkunCalcu — Documento V1 del Sistema

> Versión: 1.0
> Fecha: 2026-03-04
> Estado: Activo

---

## 1. ¿Qué es AkunCalcu?

AkunCalcu es el sistema de gestión interna de **Akuna Aberturas**, una empresa fabricante y comercializadora de aberturas de aluminio (ventanas, puertas, paños fijos, persianas).

El sistema centraliza tres grandes necesidades del negocio:

1. **Calcular precios** — desde una calculadora rápida hasta un cotizador completo con despiece de materiales.
2. **Gestionar la operación comercial** — ventas, cobros, gastos, clientes, cuentas corrientes.
3. **Administrar la fábrica** — pedidos de fábrica con medidas y despiece de perfiles y accesorios.

**Problema que resuelve:**
Sin el sistema, la empresa dependía de hojas de cálculo separadas para presupuestos, ventas, cobros y materiales. AkunCalcu unifica todo en una sola plataforma web accesible desde cualquier dispositivo.

---

## 2. Usuarios del sistema

| Tipo de usuario | Acceso |
|----------------|--------|
| **Staff (administrador)** | Acceso total: productos, ABM usuarios, configuración de fábrica, plantillas, todos los módulos |
| **Usuario regular** | Acceso a módulo comercial, calculadoras, cotizador, despiece. Sin acceso a configuración de sistema |

Todos los usuarios requieren login. El sistema no tiene acceso público.

---

## 3. Módulos del sistema

### 3.1 Calculadora Rápida

**Propósito:** Calcular el precio de vidrios, paños fijos o persianas a partir de medidas en milímetros.

**Proceso:**
1. El usuario selecciona uno o más productos del catálogo
2. Ingresa las medidas en **milímetros** (alto y ancho)
3. El sistema convierte a metros y aplica la fórmula del producto
4. Muestra el precio al instante (cálculo en tiempo real vía JS)

**Cálculos:**

Cada producto tiene dos fórmulas posibles:

- **Área** (vidrios, paños fijos):
  ```
  m² = (alto_mm / 1000) × (ancho_mm / 1000)
  precio = m² × precio_por_m²
  ```

- **Perímetro** (persianas):
  ```
  metros = ((alto_mm / 1000) × 2) + ((ancho_mm / 1000) × 2)
  precio = metros × precio_por_m²
  ```

El catálogo de productos tiene tres categorías: `Vidrios`, `Paños Fijos` y `Persianas`. Cada producto puede activarse o desactivarse sin eliminarse.

---

### 3.2 Módulo Comercial

**Propósito:** Registrar y controlar ventas, cobros, gastos y cuentas corrientes de la empresa.

#### 3.2.1 Clientes

CRUD completo de clientes con datos fiscales (CUIT, condición de IVA: RI, Monotributista, Exento, Consumidor Final). La eliminación es **lógica** (soft delete): el cliente no se borra, se marca con `deleted_at`. Las ventas asociadas mantienen su referencia.

#### 3.2.2 Ventas

Una venta representa un pedido de abertura a un cliente.

**Datos principales:**
- `numero_pedido`: identificador del pedido (puede repetirse, ej: varias cuotas del mismo)
- `cliente`: FK a Cliente
- `valor_total`: monto de la venta
- `sena`: anticipo cobrado al momento de la venta
- `tiene_retenciones` / `monto_retenciones`: si el cliente retiene impuestos
- `estado`: Pendiente → Entregado → Colocado
- `con_factura`: indica si la venta es en blanco (con factura) o en negro

**Cálculo del saldo (automático, se recalcula en cada `save()`):**
```
saldo = (valor_total + total_percepciones) - monto_retenciones - seña - total_pagos_realizados
```

El saldo representa lo que falta cobrar al cliente.

#### 3.2.3 Percepciones

Las percepciones son **importes que se agregan al total** de una venta. El cliente las paga adicionalmente.

Tipos: Ganancias, Ingresos Brutos BA, Ingresos Brutos CABA, IVA.

```
total_con_percepciones = valor_total + suma(percepciones)
```

#### 3.2.4 Pagos

Los pagos van descontando el saldo pendiente de una venta.

Formas de pago: Transferencia, Efectivo, Cheque, Tarjeta.

Cada pago puede tener **retenciones** asociadas, que son descuentos que el cliente aplica sobre el pago (ej: retención de ganancias).

```
monto_neto_cobrado = monto_pago - suma(retenciones_del_pago)
```

#### 3.2.5 Gastos (Compras)

Registra los egresos de la empresa: colocadores, fletes, proveedores, colaboradores, etc.

Organización:
- `TipoCuenta` → categoría principal (Colocadores, Fletes, Proveedores, etc.)
- `TipoGasto` → subcategoría dentro de un TipoCuenta
- `Cuenta` → proveedor/persona a quien se le paga
- `Compra` → el gasto en sí, con fecha, importe, número de factura

#### 3.2.6 Reportes

- **Reporte de Ingresos**: ventas agrupadas por período, totales cobrados y pendientes
- **Reporte de Gastos**: compras agrupadas por tipo de gasto y período

---

### 3.3 Facturación Electrónica

**Propósito:** Emitir facturas electrónicas homologadas ante AFIP.

**Proceso:**
1. Se crea una factura vinculada a una Venta existente (o sin venta)
2. Se agregan ítems con descripción, cantidad, precio unitario y alícuota de IVA
3. El sistema envía a AFIP y obtiene el **CAE** (Código de Autorización Electrónica)
4. La factura queda registrada con estado: Borrador → Autorizada / Rechazada

**Tipos de factura:** A (a RI), B (a consumidor final/mono), C

**Cálculo de IVA por ítem:**
```
iva = precio_unitario × cantidad × (alicuota_iva / 100)
subtotal = precio_unitario × cantidad
total_item = subtotal + iva
```

**Libro IVA Ventas:** Registro contable mensual con la discriminación de netos gravados e IVA por cada alícuota (21%, 10.5%, 27%, exento).

**Numeración:** Punto de venta (configurable) + número correlativo, ej: `0001-00000123`

---

### 3.4 Contabilidad

**Propósito:** Plan de cuentas y asientos contables para el seguimiento financiero de la empresa.

**Plan de cuentas:** Estructura jerárquica con 6 tipos:
- Activo (A), Pasivo (P), Patrimonio Neto (PN)
- Ingresos (I), Costos (C), Gastos (G)

**Asientos:** Partida doble (Debe / Haber). El sistema valida que cada asiento esté balanceado (`total_debe == total_haber`).

**Cálculo de saldo de cuenta:**
```
si cuenta es Activo/Gasto/Costo:  saldo = debe - haber
si cuenta es Pasivo/PN/Ingreso:   saldo = haber - debe
```

**Reportes:** Balance General y Estado de Resultados.

**Nota:** Este módulo está implementado a nivel de modelos y vistas básicas. La integración automática con ventas/compras está planificada para fases futuras.

---

### 3.5 Despiece / Pedidos de Fábrica

**Propósito:** Calcular las medidas exactas de corte de perfiles y accesorios para fabricar las aberturas de un pedido.

Este módulo tiene dos partes: la **configuración de plantillas** (solo staff) y la **operativa de pedidos** (todos los usuarios).

#### 3.5.1 Plantillas de Despiece

Una plantilla define cómo se calcula una abertura específica (ej: "Ventana corrediza 2 hojas").

Cada plantilla tiene **campos** que pueden ser:
- **MANUAL**: el operario ingresa el valor (ej: `ANCHO = 1200`)
- **CALCULADO**: el sistema lo calcula automáticamente a partir de una fórmula (ej: `LUZ_ANCHO = ANCHO - 42`)

**Fórmulas soportadas:**
```
Operadores: + - * / ( )
Funciones: MIN(a;b), MAX(a;b), ROUND(valor;decimales), IF(condicion;si_verdadero;si_falso)
Alias español: SI(condicion;si_verdadero;si_falso)
Comparadores: = > <
```

**Motor de cálculo (FormulaEngine):**
1. Parsea la fórmula usando el algoritmo **Shunting Yard** (convierte a notación polaca inversa)
2. Resuelve las dependencias entre campos calculados usando **ordenamiento topológico**
3. Detecta referencias circulares entre campos y reporta el error
4. Convierte unidades automáticamente: cm×10 → mm, m×1000 → mm (mm es la unidad base interna)

**Ejemplo de fórmula:**
```
ANCHO_VIDRIO = ANCHO - 42           → ancho del vidrio = ancho total - 42mm de marco
ALTO_HOJA = (ALTO - 30) / 2         → alto de cada hoja cuando son 2
LUZ = IF(TIPO = BALCON; ALTO; ANCHO) → usa condicional según tipo
```

#### 3.5.2 Pedidos de Fábrica

Un pedido de fábrica agrupa las aberturas de un cliente para fabricar.

**Estructura:**
```
PedidoFabrica (número, cliente, estado)
  └── PedidoFabricaItem (plantilla usada, ej: "Ventana V90")
        └── PedidoFabricaFila (una abertura específica con sus medidas)
              inputs_json: {"ANCHO": "1200", "ALTO": "1500", "TIPO": "BALCON"}
              outputs_json: {"LUZ_ANCHO": 1158, "ALTO_HOJA": 735, ...}
```

**Proceso de cálculo de un pedido:**
1. Se crea el pedido con número y cliente
2. Se agregan ítems eligiendo la plantilla (tipo de abertura)
3. Por cada abertura, se agrega una fila con las medidas manuales
4. Al calcular: el motor de fórmulas procesa cada fila y guarda los resultados en JSON
5. El estado de cada fila: `SIN_CALCULAR` → `OK` / `ERROR`

Los resultados (outputs) representan las longitudes de corte de cada perfil para esa abertura.

---

### 3.6 Cotizador

**Propósito:** Calcular el precio de costo de una abertura a partir de la base de datos de materiales heredada del sistema anterior.

Este módulo trabaja con tablas de base de datos **legacy** (read-only, `managed = False`), que contienen la estructura de productos definida por la extrusora fabricante de perfiles.

**Estructura de datos:**
```
Extrusora → Línea → Producto → Marco → Hoja → Interior → [opcionales: Contravidrio, Mosquitero, Vidrio Repartido, Cruces]
```

**Proceso de cálculo:**

El usuario selecciona:
- Marco, Hoja, Interior (jerarquía obligatoria)
- Color del perfil
- Vidrio (por código)
- Opcionales: Contravidrio, Mosquitero, Vidrio repartido, Cruces
- Tratamiento de superficie (pintura/anodizado)
- Ancho y alto en mm
- Margen de ganancia %

**Cálculo de perfiles:**
```
Para cada perfil del despiece:
  longitud_mm = evaluar_formula(formula_perfil, {Ancho, Alto, Cantidad})
  peso_kg = (longitud_mm / 1000) × cantidad × perfil.peso_por_metro
  precio = peso_kg × perfil.precio_por_kg

  Si corte a 45°: precio -= descuento_corte45 × cantidad
```

**Cálculo de accesorios:**
```
Para cada accesorio del despiece:
  cantidad = evaluar_formula(formula_cantidad, {Ancho, Alto, Cantidad})
  precio = cantidad × accesorio.precio_unitario
```

**Cálculo de vidrio:**
```
area_m2 = (ancho_mm - rebaje) × (alto_mm - rebaje) / 1.000.000
precio_vidrio = area_m2 × vidrio.precio_m2
```

**Cálculo de tratamiento de superficie:**
```
precio_tratamiento = peso_total_perfiles × tratamiento.precio_por_kg
```

**Total final:**
```
subtotal = perfiles + accesorios + vidrio + tratamiento
margen = subtotal × (margen_% / 100)
precio_total = subtotal + margen
```

La API devuelve el desglose completo de cada componente.

**Interfaz:** El cotizador es una SPA (Single Page Application) con selects en cascada que se actualizan según la selección anterior. El cálculo se realiza vía POST a la API REST.

---

### 3.7 Gestión de Usuarios

**Propósito:** ABM de usuarios del sistema (solo accesible para staff).

Permite crear, editar, activar y desactivar usuarios. Asignación de permisos `is_staff`. No se pueden eliminar usuarios, solo desactivar.

---

### 3.8 Seguridad / Backups

**Propósito:** Gestión de backups de la base de datos.

Módulo con acceso por login separado (distinto al login principal). Permite listar, descargar y gestionar backups del sistema.

---

## 4. Arquitectura técnica

### Stack

| Capa | Tecnología |
|------|-----------|
| Backend | Python 3.12, Django 4.2.7 |
| Base de datos | MySQL 8.0 |
| Frontend | Tailwind CSS (CDN), FontAwesome 6.4.0, jQuery 3.6.0, Select2, SweetAlert2 |
| API interna | Django REST Framework (solo para el cotizador) |
| Contenedores | Docker + Docker Compose |
| Servidor web | Gunicorn (producción) |

### Estructura de apps Django

```
akuna_calc/
├── core/           → Autenticación, home, base template
├── productos/      → Catálogo de productos + Calculadora rápida
├── comercial/      → Ventas, gastos, clientes, cuentas
├── facturacion/    → Facturación electrónica AFIP
├── contabilidad/   → Plan de cuentas y asientos contables
├── plantillas/     → Plantillas de despiece + Pedidos de fábrica
├── pricing/        → Cotizador legacy (BOM con DRF)
├── usuarios/       → ABM usuarios (staff)
├── security/       → Backups
└── configuracion/  → Configuración general del sistema
```

### Base de datos

Se utilizan **dos grupos de tablas**:

1. **Tablas gestionadas por Django** (`managed = True`, predeterminado): Todas las tablas de `comercial`, `facturacion`, `productos`, `plantillas`, `contabilidad`, `usuarios`.

2. **Tablas legacy** (`managed = False`): Las tablas del cotizador (`extrusoras`, `lineas`, `productos`, `marco`, `hoja`, `interior`, `perfiles`, `accesorios`, `vidrios`, `tratamientos`, etc.). Estas tablas provienen de un sistema anterior y Django las lee pero no las gestiona.

### Patrón de eliminación

Todos los modelos críticos utilizan **soft delete** (eliminación lógica):
```python
def delete(self):
    self.deleted_at = timezone.now()
    self.activo = False  # donde aplica
    self.save()
```
Esto significa que ningún dato se elimina físicamente de la base. Los registros marcados con `deleted_at` se filtran en las consultas normales.

### Entorno de desarrollo

```bash
docker-compose up --build   # levanta todo (MySQL + Django)
http://localhost:8000        # aplicación
http://localhost:8000/admin  # admin Django
```
Credenciales por defecto: `admin / admin123`

---

## 5. Flujo de trabajo típico

### Flujo de venta

```
1. Cliente solicita presupuesto
        ↓
2. Comercial usa el Cotizador o la Calculadora para estimar el precio
        ↓
3. Se registra la Venta con el cliente, número de pedido, total y seña
        ↓
4. Fábrica usa el módulo de Despiece para calcular los cortes del pedido
        ↓
5. Se fabrica y entrega. Venta pasa a estado "Entregado"
        ↓
6. Se cobran los pagos pendientes. El saldo se recalcula automáticamente.
        ↓
7. Si es venta en blanco: se emite la Factura Electrónica vía AFIP
        ↓
8. Venta pasa a estado "Colocado"
```

### Flujo de gasto

```
1. Se recibe un gasto (flete, colocación, proveedor)
        ↓
2. Se registra en Compras con cuenta, tipo de gasto, importe y fecha
        ↓
3. El reporte de gastos lo incluye en el período correspondiente
```

---

## 6. Integraciones externas

| Integración | Descripción | Estado |
|-------------|-------------|--------|
| **AFIP** | Facturación electrónica (CAE) vía webservices | Implementado |
| **Base legacy** | Tablas del sistema anterior de cotización | Implementado (read-only) |

---

## 7. Estado actual del sistema

### Implementado y en uso

- [x] Calculadora rápida (vidrios, paños, persianas)
- [x] Módulo comercial completo (ventas, cobros, gastos, clientes, cuentas)
- [x] Percepciones y retenciones en ventas
- [x] Reportes de ingresos y gastos
- [x] Facturación electrónica AFIP
- [x] Libro IVA Ventas
- [x] Despiece / Plantillas de fábrica
- [x] Pedidos de fábrica con motor de fórmulas
- [x] Cotizador con BOM legacy
- [x] ABM usuarios
- [x] Sistema de backups

### Implementado parcialmente

- [~] Contabilidad: modelos y vistas básicas (plan de cuentas, asientos), sin integración automática con ventas/compras

### No implementado (identificado para fases futuras)

- [ ] Ajuste por inflación (campo `monetaria` en cuentas contables existe pero no está activo)
- [ ] Integración contable automática: que una venta genere su asiento automáticamente
- [ ] Módulo de stock de materiales
- [ ] Notificaciones / alertas de vencimientos
- [ ] App mobile nativa (actualmente el web es responsive)

---

## 8. Glosario del negocio

| Término | Significado |
|---------|-------------|
| **Abertura** | Ventana, puerta, paño fijo o persiana de aluminio |
| **Despiece** | Lista de perfiles y accesorios cortados a medida para fabricar una abertura |
| **Perfil** | Barra de aluminio con forma específica que se corta y ensambla |
| **Marco** | Parte fija de la abertura que va en la pared |
| **Hoja** | Parte móvil de la abertura (la que se desliza o abre) |
| **Interior** | Parte interior de la hoja (contramarco) |
| **Contravidrio** | Perfil que retiene el vidrio en el marco o la hoja |
| **Mosquitero** | Marco con malla que se coloca en la abertura |
| **Vidrio repartido** | División interna de una abertura en múltiples paños |
| **Cruce** | Perfil central que separa hojas en aberturas de 4 hojas |
| **Extrusora** | Fabricante del perfil de aluminio (ej: Modena, A30) |
| **Línea** | Familia de perfiles de una extrusora (ej: Serie 25, Serie 40) |
| **Tratamiento** | Acabado superficial del aluminio: pintura electrostática o anodizado |
| **Seña** | Anticipo que paga el cliente al confirmar el pedido |
| **Saldo** | Lo que falta cobrar: Total + Percepciones - Retenciones - Seña - Pagos |
| **Percepción** | Impuesto que se agrega al total de una venta (paga el cliente) |
| **Retención** | Impuesto que el cliente descuenta del pago |
| **CAE** | Código de Autorización Electrónica emitido por AFIP |
| **IIBB** | Ingresos Brutos (impuesto provincial) |
| **PV** | Punto de Venta (para facturación AFIP) |
| **BOM** | Bill of Materials — lista de materiales necesarios para fabricar un producto |
