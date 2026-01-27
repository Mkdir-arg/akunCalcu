from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class Producto(models.Model):
    CATEGORIA_CHOICES = [
        ('vidrios', 'Vidrios'),
        ('panos_fijos', 'Paños Fijos'),
        ('persianas', 'Persianas'),
    ]
    
    FORMULA_CHOICES = [
        ('area', 'Área (Alto × Ancho)'),
        ('perimetro', 'Perímetro (Alto×2 + Ancho×2)'),
    ]
    
    ALICUOTA_IVA_CHOICES = [
        ('21.00', '21%'),
        ('10.50', '10.5%'),
        ('27.00', '27%'),
        ('0.00', 'Exento'),
    ]
    
    nombre = models.CharField(max_length=200)
    categoria = models.CharField(max_length=100, choices=CATEGORIA_CHOICES)
    precio_m2 = models.DecimalField(max_digits=10, decimal_places=2)
    alicuota_iva = models.DecimalField(max_digits=5, decimal_places=2, default=21.00)
    formula = models.CharField(max_length=20, choices=FORMULA_CHOICES, default='area')
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calcular_precio(self, alto_mm, ancho_mm):
        """Calcula el precio según la fórmula del producto"""
        alto_m = alto_mm / 1000
        ancho_m = ancho_mm / 1000
        
        if self.formula == 'perimetro':
            # Perímetro: (Alto×2 + Ancho×2)
            calculo = (alto_m * 2) + (ancho_m * 2)
        else:
            # Área: Alto × Ancho
            calculo = alto_m * ancho_m
            
        return calculo * float(self.precio_m2)

    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ['nombre']

class Cotizacion(models.Model):
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    total_general = models.DecimalField(max_digits=12, decimal_places=2)
    observaciones = models.TextField(blank=True)

    def __str__(self):
        return f"Cotización #{self.id} - {self.fecha.strftime('%d/%m/%Y')}"

    def calcular_total(self):
        return sum(item.subtotal for item in self.items.all())

    class Meta:
        ordering = ['-fecha']

class CotizacionItem(models.Model):
    cotizacion = models.ForeignKey(Cotizacion, related_name='items', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    alto_mm = models.IntegerField()
    ancho_mm = models.IntegerField()
    area_m2 = models.DecimalField(max_digits=10, decimal_places=3)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.producto.nombre} - {self.alto_mm}x{self.ancho_mm}mm"