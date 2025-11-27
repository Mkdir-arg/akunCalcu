from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal


class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    razon_social = models.CharField(max_length=200, blank=True)
    direccion = models.TextField()
    localidad = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
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
    
    numero_pedido = models.CharField(max_length=50, unique=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    valor_total = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    sena = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    saldo = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    monto_cobrado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fecha_pago = models.DateField(null=True, blank=True)
    forma_pago = models.CharField(max_length=20, choices=FORMA_PAGO_CHOICES, blank=True)
    con_factura = models.BooleanField(default=False)
    tipo_factura = models.CharField(max_length=2, choices=TIPO_FACTURA_CHOICES, blank=True)
    numero_factura = models.CharField(max_length=50, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    observaciones = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        self.saldo = self.valor_total - self.sena - self.monto_cobrado
        super().save(*args, **kwargs)
    
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
    tipo_cuenta = models.ForeignKey(TipoCuenta, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    razon_social = models.CharField(max_length=200, blank=True)
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