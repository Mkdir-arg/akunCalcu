from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class Producto(models.Model):
    CATEGORIA_CHOICES = [
        ('vidrios', 'Vidrios'),
        ('panos_fijos', 'Paños Fijos'),
        ('persianas', 'Persianas'),
    ]
    
    nombre = models.CharField(max_length=200)
    categoria = models.CharField(max_length=100, choices=CATEGORIA_CHOICES)
    precio_m2 = models.DecimalField(max_digits=10, decimal_places=2)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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