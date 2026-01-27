from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
from decimal import Decimal


class Ejercicio(models.Model):
    """Período contable (ejercicio fiscal)"""
    nombre = models.CharField(max_length=100)
    fecha_inicio = models.DateField()
    fecha_cierre = models.DateField()
    cerrado = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.nombre} ({self.fecha_inicio.year})"
    
    class Meta:
        verbose_name = "Ejercicio Contable"
        verbose_name_plural = "Ejercicios Contables"
        ordering = ['-fecha_inicio']


class Cuenta(models.Model):
    """Plan de cuentas contable"""
    TIPO_CHOICES = [
        ('A', 'Activo'),
        ('P', 'Pasivo'),
        ('PN', 'Patrimonio Neto'),
        ('I', 'Ingresos'),
        ('C', 'Costos'),
        ('G', 'Gastos'),
    ]
    
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=200)
    tipo = models.CharField(max_length=2, choices=TIPO_CHOICES)
    padre = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='subcuentas')
    nivel = models.IntegerField(default=1)
    imputable = models.BooleanField(default=True, help_text="¿Acepta movimientos?")
    activa = models.BooleanField(default=True)
    
    # Para ajuste inflación (Fase futura)
    monetaria = models.BooleanField(default=True, help_text="False = se ajusta por inflación")
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    
    def get_saldo(self, fecha_desde=None, fecha_hasta=None):
        """Calcula saldo de la cuenta"""
        lineas = self.lineas.all()
        
        if fecha_desde:
            lineas = lineas.filter(asiento__fecha__gte=fecha_desde)
        if fecha_hasta:
            lineas = lineas.filter(asiento__fecha__lte=fecha_hasta)
        
        debe = sum(l.debe for l in lineas)
        haber = sum(l.haber for l in lineas)
        
        # Saldo según naturaleza de la cuenta
        if self.tipo in ['A', 'G', 'C']:  # Activo, Gastos, Costos
            return debe - haber
        else:  # Pasivo, PN, Ingresos
            return haber - debe
    
    class Meta:
        verbose_name = "Cuenta Contable"
        verbose_name_plural = "Plan de Cuentas"
        ordering = ['codigo']


class Asiento(models.Model):
    """Asiento contable (cabecera)"""
    TIPO_CHOICES = [
        ('MAN', 'Manual'),
        ('VEN', 'Venta'),
        ('COM', 'Compra'),
        ('COB', 'Cobranza'),
        ('PAG', 'Pago'),
        ('AJU', 'Ajuste'),
    ]
    
    numero = models.IntegerField()
    fecha = models.DateField()
    tipo = models.CharField(max_length=3, choices=TIPO_CHOICES, default='MAN')
    descripcion = models.TextField()
    
    # Referencia a documento origen
    factura = models.ForeignKey('facturacion.Factura', null=True, blank=True, on_delete=models.SET_NULL)
    
    # Auditoría
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Asiento {self.numero} - {self.fecha}"
    
    def get_total_debe(self):
        return sum(l.debe for l in self.lineas.all())
    
    def get_total_haber(self):
        return sum(l.haber for l in self.lineas.all())
    
    def esta_balanceado(self):
        return self.get_total_debe() == self.get_total_haber()
    
    class Meta:
        verbose_name = "Asiento Contable"
        verbose_name_plural = "Asientos Contables"
        ordering = ['-fecha', '-numero']
        unique_together = ['numero', 'fecha']


class AsientoLinea(models.Model):
    """Línea de asiento (debe/haber)"""
    asiento = models.ForeignKey(Asiento, related_name='lineas', on_delete=models.CASCADE)
    cuenta = models.ForeignKey(Cuenta, related_name='lineas', on_delete=models.PROTECT)
    debe = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(Decimal('0'))])
    haber = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(Decimal('0'))])
    detalle = models.CharField(max_length=200, blank=True)
    
    def __str__(self):
        return f"{self.cuenta.codigo} - D:{self.debe} H:{self.haber}"
    
    class Meta:
        verbose_name = "Línea de Asiento"
        verbose_name_plural = "Líneas de Asiento"


class ConfiguracionContable(models.Model):
    """Mapeo de cuentas para asientos automáticos"""
    # Cuentas patrimoniales
    cuenta_clientes = models.ForeignKey(Cuenta, related_name='+', on_delete=models.PROTECT, null=True, blank=True)
    cuenta_proveedores = models.ForeignKey(Cuenta, related_name='+', on_delete=models.PROTECT, null=True, blank=True)
    cuenta_caja = models.ForeignKey(Cuenta, related_name='+', on_delete=models.PROTECT, null=True, blank=True)
    cuenta_banco = models.ForeignKey(Cuenta, related_name='+', on_delete=models.PROTECT, null=True, blank=True)
    
    # Cuentas de resultados
    cuenta_ventas = models.ForeignKey(Cuenta, related_name='+', on_delete=models.PROTECT, null=True, blank=True)
    cuenta_costo_ventas = models.ForeignKey(Cuenta, related_name='+', on_delete=models.PROTECT, null=True, blank=True)
    
    # Cuentas impositivas
    cuenta_iva_debito = models.ForeignKey(Cuenta, related_name='+', on_delete=models.PROTECT, null=True, blank=True)
    cuenta_iva_credito = models.ForeignKey(Cuenta, related_name='+', on_delete=models.PROTECT, null=True, blank=True)
    
    class Meta:
        verbose_name = "Configuración Contable"
        verbose_name_plural = "Configuración Contable"
    
    def __str__(self):
        return "Configuración Contable"
