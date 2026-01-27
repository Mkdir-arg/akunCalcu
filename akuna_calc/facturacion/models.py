from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from comercial.models import Cliente, Venta
from productos.models import Producto


class PuntoVenta(models.Model):
    numero = models.IntegerField(unique=True)
    nombre = models.CharField(max_length=100)
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return f"PV {self.numero:04d} - {self.nombre}"
    
    class Meta:
        verbose_name = "Punto de Venta"
        verbose_name_plural = "Puntos de Venta"
        ordering = ['numero']


class Factura(models.Model):
    TIPO_CHOICES = [
        ('A', 'Factura A'),
        ('B', 'Factura B'),
        ('C', 'Factura C'),
    ]
    
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('autorizada', 'Autorizada'),
        ('rechazada', 'Rechazada'),
        ('anulada', 'Anulada'),
    ]
    
    # Relaciones
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    venta = models.OneToOneField(Venta, null=True, blank=True, on_delete=models.SET_NULL, related_name='factura_electronica')
    
    # Datos comprobante
    tipo = models.CharField(max_length=1, choices=TIPO_CHOICES)
    punto_venta = models.ForeignKey(PuntoVenta, on_delete=models.PROTECT)
    numero = models.IntegerField()
    fecha = models.DateField(auto_now_add=True)
    
    # Importes
    subtotal_neto = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    iva_21 = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    iva_105 = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    iva_27 = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    exento = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    
    # AFIP
    cae = models.CharField(max_length=14, blank=True)
    cae_vencimiento = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='borrador')
    observaciones_afip = models.TextField(blank=True)
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Factura {self.tipo} {self.punto_venta.numero:04d}-{self.numero:08d}"
    
    def get_numero_completo(self):
        return f"{self.punto_venta.numero:04d}-{self.numero:08d}"
    
    class Meta:
        verbose_name = "Factura"
        verbose_name_plural = "Facturas"
        unique_together = ['tipo', 'punto_venta', 'numero']
        ordering = ['-fecha', '-numero']


class FacturaItem(models.Model):
    factura = models.ForeignKey(Factura, related_name='items', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, null=True, blank=True)
    descripcion = models.CharField(max_length=200)
    cantidad = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(Decimal('0.001'))])
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    alicuota_iva = models.DecimalField(max_digits=5, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    iva = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    
    def __str__(self):
        return f"{self.descripcion} - {self.cantidad}"
    
    class Meta:
        verbose_name = "Item de Factura"
        verbose_name_plural = "Items de Factura"


class LibroIVAVentas(models.Model):
    periodo = models.DateField()  # Primer día del mes
    factura = models.ForeignKey(Factura, on_delete=models.CASCADE)
    
    # Discriminación por alícuota
    neto_gravado_21 = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    iva_21 = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    neto_gravado_105 = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    iva_105 = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    neto_gravado_27 = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    iva_27 = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    exento = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"IVA Ventas {self.periodo.strftime('%m/%Y')} - {self.factura}"
    
    class Meta:
        verbose_name = "Libro IVA Ventas"
        verbose_name_plural = "Libro IVA Ventas"
        ordering = ['-periodo', '-created_at']
