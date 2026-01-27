from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal


class Cliente(models.Model):
    CONDICION_IVA_CHOICES = [
        ('RI', 'Responsable Inscripto'),
        ('MONO', 'Monotributista'),
        ('EX', 'Exento'),
        ('CF', 'Consumidor Final'),
    ]
    
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    razon_social = models.CharField(max_length=200, blank=True)
    cuit = models.CharField(max_length=11, blank=True, null=True, unique=True)
    dni = models.CharField(max_length=8, blank=True)
    condicion_iva = models.CharField(max_length=4, choices=CONDICION_IVA_CHOICES, default='CF')
    direccion = models.TextField()
    localidad = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.nombre} {self.apellido}"
    
    def get_nombre_completo(self):
        if self.razon_social:
            return self.razon_social
        return f"{self.nombre} {self.apellido}"
    
    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"


class Venta(models.Model):
    FORMA_PAGO_CHOICES = [
        ('transferencia', 'Transferencia'),
        ('efectivo', 'Efectivo'),
    ]
    
    TIPO_FACTURA_CHOICES = [
        ('A', 'Factura A'),
        ('B', 'Factura B'),
        ('NC', 'Nota de Crédito'),
    ]
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('entregado', 'Entregado'),
        ('colocado', 'Colocado'),
    ]
    
    numero_pedido = models.CharField(max_length=50)  # Permite duplicados (PVC, PVC, etc.)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    valor_total = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    sena = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    saldo = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fecha_pago = models.DateField(null=True, blank=True)
    forma_pago = models.CharField(max_length=20, choices=FORMA_PAGO_CHOICES, blank=True)
    con_factura = models.BooleanField(default=True, verbose_name="Venta en blanco (con factura)")
    tipo_factura = models.CharField(max_length=2, choices=TIPO_FACTURA_CHOICES, blank=True)
    numero_factura = models.CharField(max_length=50, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    observaciones = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Saldo = Total - Seña (sin monto_cobrado confuso)
        self.saldo = self.valor_total - self.sena
        super().save(*args, **kwargs)
    
    def get_numero_factura_display(self):
        """Obtiene número de factura (electrónica o manual)"""
        if hasattr(self, 'factura_electronica'):
            return self.factura_electronica.get_numero_completo()
        return self.numero_factura or '-'
    
    def __str__(self):
        return f"Pedido {self.numero_pedido} - {self.cliente}"
    
    class Meta:
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"
        ordering = ['-created_at']


class TipoCuenta(models.Model):
    TIPOS_CUENTA = [
        ('colocadores', 'Colocadores'),
        ('colaboradores', 'Colaboradores'),
        ('fletes', 'Fletes'),
        ('retiros_propios', 'Retiros Propios'),
        ('varios', 'Varios'),
        ('proveedores', 'Proveedores'),
    ]
    
    tipo = models.CharField(max_length=20, choices=TIPOS_CUENTA, unique=True)
    descripcion = models.CharField(max_length=100)
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return self.get_tipo_display()
    
    class Meta:
        verbose_name = "Tipo de Cuenta"
        verbose_name_plural = "Tipos de Cuenta"


class Cuenta(models.Model):
    CONDICION_IVA_CHOICES = [
        ('RI', 'Responsable Inscripto'),
        ('MONO', 'Monotributista'),
        ('EX', 'Exento'),
        ('CF', 'Consumidor Final'),
    ]
    
    tipo_cuenta = models.ForeignKey(TipoCuenta, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    razon_social = models.CharField(max_length=200, blank=True)
    cuit = models.CharField(max_length=11, blank=True)
    condicion_iva = models.CharField(max_length=4, choices=CONDICION_IVA_CHOICES, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.nombre} ({self.tipo_cuenta})"
    
    class Meta:
        verbose_name = "Cuenta"
        verbose_name_plural = "Cuentas"


class Compra(models.Model):
    numero_pedido = models.CharField(max_length=50)
    cuenta = models.ForeignKey(Cuenta, on_delete=models.CASCADE)
    fecha_pago = models.DateField()
    importe_abonado = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    con_factura = models.BooleanField(default=True, verbose_name="Compra en blanco (con factura)")
    numero_factura = models.CharField(max_length=50, blank=True)
    descripcion = models.TextField(blank=True)
    comprobante = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"Compra {self.numero_pedido} - {self.cuenta}"
    
    class Meta:
        verbose_name = "Compra"
        verbose_name_plural = "Compras"
        ordering = ['-fecha_pago']