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
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.nombre} {self.apellido}"
    
    def get_nombre_completo(self):
        if self.razon_social:
            return self.razon_social
        return f"{self.nombre} {self.apellido}"
    
    def delete(self, *args, **kwargs):
        """Eliminado lógico"""
        from django.utils import timezone
        self.deleted_at = timezone.now()
        self.save()
    
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
    tiene_retenciones = models.BooleanField(default=False, verbose_name="Tiene retenciones")
    monto_retenciones = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Monto de retenciones")
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
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        # Calcular saldo: Total - Retenciones - Seña - Pagos realizados
        valor_neto = self.valor_total - self.monto_retenciones
        if self.pk:  # Solo calcular pagos si la venta ya existe
            total_pagos = sum(pago.monto for pago in self.pagos.all())
            self.saldo = valor_neto - self.sena - total_pagos
        else:
            # Nueva venta: saldo = total neto - seña
            self.saldo = valor_neto - self.sena
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Eliminado lógico"""
        from django.utils import timezone
        self.deleted_at = timezone.now()
        self.save()
    
    def get_numero_factura_display(self):
        """Obtiene número de factura (electrónica o manual)"""
        if hasattr(self, 'factura_electronica'):
            return self.factura_electronica.get_numero_completo()
        return self.numero_factura or '-'
    
    def get_total_percepciones(self):
        """Calcula el total de percepciones"""
        return sum(p.importe for p in self.percepciones.all())
    
    def get_total_con_percepciones(self):
        """Calcula el total de la venta incluyendo percepciones"""
        return self.valor_total + self.get_total_percepciones()
    
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
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return self.get_tipo_display()
    
    def delete(self, *args, **kwargs):
        """Eliminado lógico"""
        from django.utils import timezone
        self.deleted_at = timezone.now()
        self.activo = False
        self.save()
    
    class Meta:
        verbose_name = "Tipo de Cuenta"
        verbose_name_plural = "Tipos de Cuenta"


class TipoGasto(models.Model):
    tipo_cuenta = models.ForeignKey(TipoCuenta, on_delete=models.CASCADE, related_name='tipos_gasto')
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=200, blank=True)
    activo = models.BooleanField(default=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.nombre} ({self.tipo_cuenta})"
    
    def delete(self, *args, **kwargs):
        """Eliminado lógico"""
        from django.utils import timezone
        self.deleted_at = timezone.now()
        self.activo = False
        self.save()
    
    class Meta:
        verbose_name = "Tipo de Gasto"
        verbose_name_plural = "Tipos de Gasto"
        ordering = ['nombre']
        db_table = 'comercial_subtipocuenta'


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
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.nombre} ({self.tipo_cuenta})"
    
    def delete(self, *args, **kwargs):
        """Eliminado lógico"""
        from django.utils import timezone
        self.deleted_at = timezone.now()
        self.activo = False
        self.save()
    
    class Meta:
        verbose_name = "Cuenta"
        verbose_name_plural = "Cuentas"


class Compra(models.Model):
    numero_pedido = models.CharField(max_length=50)
    cuenta = models.ForeignKey(Cuenta, on_delete=models.CASCADE)
    tipo_gasto = models.ForeignKey(TipoGasto, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_pago = models.DateField()
    importe_abonado = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    con_factura = models.BooleanField(default=True, verbose_name="Compra en blanco (con factura)")
    numero_factura = models.CharField(max_length=50, blank=True)
    descripcion = models.TextField(blank=True)
    comprobante = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Compra {self.numero_pedido} - {self.cuenta}"
    
    def delete(self, *args, **kwargs):
        """Eliminado lógico"""
        from django.utils import timezone
        self.deleted_at = timezone.now()
        self.save()
    
    class Meta:
        verbose_name = "Compra"
        verbose_name_plural = "Compras"
        ordering = ['-fecha_pago']


class PagoVenta(models.Model):
    FORMA_PAGO_CHOICES = [
        ('transferencia', 'Transferencia'),
        ('efectivo', 'Efectivo'),
        ('cheque', 'Cheque'),
        ('tarjeta', 'Tarjeta'),
    ]
    
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='pagos')
    monto = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    fecha_pago = models.DateField()
    forma_pago = models.CharField(max_length=20, choices=FORMA_PAGO_CHOICES)
    numero_factura = models.CharField(max_length=50, blank=True, verbose_name='Número de Factura')
    observaciones = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def get_total_retenciones(self):
        """Calcula el total de retenciones aplicadas a este pago"""
        return sum(r.importe_retenido for r in self.retenciones.all())
    
    def get_monto_neto(self):
        """Calcula el monto neto cobrado (monto - retenciones)"""
        return self.monto - self.get_total_retenciones()
    
    def __str__(self):
        return f"Pago ${self.monto} - Venta {self.venta.numero_pedido}"
    
    class Meta:
        verbose_name = "Pago de Venta"
        verbose_name_plural = "Pagos de Ventas"
        ordering = ['-fecha_pago']


class Percepcion(models.Model):
    """Percepciones aplicadas a las ventas (se suman al total)"""
    
    TIPO_CHOICES = [
        ('ganancias', 'Ganancias'),
        ('iibb_ba', 'Ingresos Brutos Buenos Aires'),
        ('iibb_caba', 'Ingresos Brutos CABA'),
        ('iva', 'IVA'),
    ]
    
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='percepciones')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    observaciones = models.TextField(blank=True)
    importe = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_tipo_display()} - ${self.importe}"
    
    class Meta:
        verbose_name = "Percepción"
        verbose_name_plural = "Percepciones"


class Retencion(models.Model):
    """Retenciones aplicadas a los pagos (se descuentan del cobro)"""
    
    TIPO_CHOICES = [
        ('ganancias', 'Ganancias'),
        ('iibb', 'Ingresos Brutos'),
        ('iva', 'IVA'),
        ('seguridad_social', 'Seguridad Social'),
        ('otros', 'Otros'),
    ]
    
    pago = models.ForeignKey(PagoVenta, on_delete=models.CASCADE, related_name='retenciones')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    concepto = models.CharField(max_length=200, blank=True)
    descripcion = models.TextField(blank=True)
    numero_comprobante = models.CharField(max_length=100, blank=True)
    importe_isar = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Importe ISAR (Base)')
    importe_retenido = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], verbose_name='Importe Retenido')
    fecha_comprobante = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_tipo_display()} - ${self.importe_retenido}"
    
    class Meta:
        verbose_name = "Retención"
        verbose_name_plural = "Retenciones"