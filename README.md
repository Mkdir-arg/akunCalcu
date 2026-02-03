# Akuna Calc - Sistema de Gestión Comercial

Aplicación Django completa para gestionar productos, usuarios, ventas y gastos de aberturas.

## 🚀 Características

- **Gestión de Productos**: CRUD completo con categorías y precios por m²
- **Calculadora Rápida**: Cálculo en tiempo real de precios
- **Módulo Comercial**: Gestión de ventas, gastos, clientes y cuentas
- **Facturación**: Sistema de facturación electrónica integrado
- **ABM de Usuarios**: Gestión completa de usuarios (solo para staff)
- **Autenticación**: Sistema de login integrado
- **Interfaz Moderna**: UI 100% responsive con Tailwind CSS
- **Docker Ready**: Configuración completa con Docker Compose

## 🛠️ Tecnologías

- **Backend**: Python 3.12, Django 4.2.7
- **Base de Datos**: MySQL 8.0
- **Frontend**: Tailwind CSS, FontAwesome
- **Contenedores**: Docker & Docker Compose

## 📦 Instalación y Ejecución

### Con Docker (Recomendado)

1. **Clona el repositorio:**
```bash
git clone <repository-url>
cd akunCalcu
```

2. **Levanta el sistema completo:**
```bash
docker-compose up --build
```

El sistema automáticamente:
- ✅ Ejecuta migraciones
- ✅ Crea superusuario (admin/admin123)
- ✅ Carga productos iniciales
- ✅ Inicia el servidor

3. **Accede a la aplicación:**
- **App**: http://localhost:8000
- **Admin**: http://localhost:8000/admin

### Credenciales por Defecto
- **Usuario**: admin
- **Contraseña**: admin123

## 📊 Productos Precargados

El sistema incluye estos productos iniciales:

**Vidrios:**
- Laminado 3+3 (m²) - $81,000
- DVH 4+9+4 (m²) - $86,000
- DVH 3+3+9+4 (m²) - $143,000
- DVH 3+3+9+3+3 (m²) - $201,800

**Paños Fijos:**
- Módena blanco (m²) - $24,750
- Módena negro (m²) - $29,700
- A30 blanco (m²) - $35,000
- A30 negro (m²) - $42,000

**Persianas:**
- PVC blanco (m²) - $65,000

## 🎯 Funcionalidades

### 👤 Gestión de Usuarios (Solo Staff)
- Crear, editar y activar/desactivar usuarios
- Asignar permisos de staff
- Gestión completa de credenciales

### 📦 Gestión de Productos
- CRUD completo de productos
- Categorización por tipo
- Precios por metro cuadrado
- Activación/desactivación

### 🧮 Calculadora
- Cálculo rápido de precios
- Conversión automática mm → m²
- Cálculos en tiempo real
- Soporte para múltiples productos

### 💼 Módulo Comercial
- Gestión de ventas y gastos
- Control de clientes
- Administración de cuentas
- Reportes y estadísticas
- Dashboard con indicadores clave

## 🏗️ Estructura del Proyecto

```
akuna_calc/
├── akuna_calc/          # Configuración Django
├── core/                # App principal (auth, home)
├── productos/           # App productos y calculadora
├── comercial/           # App ventas, gastos, clientes
├── facturacion/         # App facturación electrónica
├── usuarios/            # App gestión de usuarios
├── static/              # Archivos estáticos
├── docker-compose.yml   # Orquestación Docker
├── Dockerfile          # Imagen Django
├── entrypoint.sh       # Script de inicio
└── requirements.txt    # Dependencias Python
```

## ⚙️ Variables de Entorno

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `DB_NAME` | Nombre de la base de datos | `akuna_calc` |
| `DB_USER` | Usuario de MySQL | `akuna` |
| `DB_PASSWORD` | Contraseña de MySQL | `akuna123` |
| `DB_HOST` | Host de MySQL | `db` |
| `DB_PORT` | Puerto de MySQL | `3306` |
| `DJANGO_SUPERUSER_USERNAME` | Usuario admin | `admin` |
| `DJANGO_SUPERUSER_EMAIL` | Email admin | `admin@example.com` |
| `DJANGO_SUPERUSER_PASSWORD` | Contraseña admin | `admin123` |

## 🔧 Comandos Útiles

```bash
# Ver logs
docker-compose logs -f

# Acceder al contenedor web
docker-compose exec web bash

# Crear migraciones
docker-compose exec web python manage.py makemigrations

# Aplicar migraciones
docker-compose exec web python manage.py migrate

# Cargar productos (manual)
docker-compose exec web python manage.py seed_productos

# Crear superusuario adicional
docker-compose exec web python manage.py createsuperuser

# Detener servicios
docker-compose down
```

## 🎨 Diseño Responsive

- **Mobile First**: Optimizado para dispositivos móviles
- **Breakpoints**: sm (640px), md (768px), lg (1024px), xl (1280px)
- **Componentes**: Cards adaptables, tablas responsive, sidebar móvil
- **Animaciones**: Transiciones suaves y efectos visuales

## 🔐 Seguridad

- Autenticación requerida para todas las funciones
- Permisos de staff para gestión de usuarios
- Validación de formularios
- Protección CSRF
- Variables de entorno para credenciales

## 📱 Compatibilidad

- ✅ Chrome, Firefox, Safari, Edge
- ✅ iOS Safari, Chrome Mobile
- ✅ Tablets y dispositivos móviles
- ✅ Pantallas desde 320px hasta 4K

## 🚀 Producción

Para producción, modifica las variables de entorno:
- Cambia credenciales por defecto
- Configura `DEBUG=False`
- Usa base de datos externa
- Configura dominio y SSL

---

**Desarrollado con ❤️ para Akuna Aberturas**