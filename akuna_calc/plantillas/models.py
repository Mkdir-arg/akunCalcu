from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
import json


class ProductoPlantilla(models.Model):
    nombre = models.CharField(max_length=200, unique=True)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Producto Plantilla'
        verbose_name_plural = 'Productos Plantilla'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class CampoPlantilla(models.Model):
    TIPO_CHOICES = [
        ('number', 'Número'),
        ('text', 'Texto'),
        ('bool', 'Sí/No'),
        ('select', 'Selección'),
    ]
    
    MODO_CHOICES = [
        ('MANUAL', 'Manual'),
        ('CALCULADO', 'Calculado'),
    ]
    
    UNIDAD_CHOICES = [
        ('', 'Sin unidad'),
        ('mm', 'Milímetros'),
        ('cm', 'Centímetros'),
        ('m', 'Metros'),
        ('m2', 'Metros cuadrados'),
        ('unidad', 'Unidad'),
    ]
    
    # Factores de conversión a mm (unidad base)
    CONVERSION_TO_MM = {
        'mm': 1,
        'cm': 10,
        'm': 1000,
        'm2': 1,  # No se convierte automáticamente
        'unidad': 1,
        '': 1,
    }

    plantilla = models.ForeignKey(ProductoPlantilla, on_delete=models.CASCADE, related_name='campos')
    nombre_visible = models.CharField(max_length=100)
    clave = models.CharField(max_length=50)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='number')
    unidad = models.CharField(max_length=10, choices=UNIDAD_CHOICES, blank=True)
    modo = models.CharField(max_length=10, choices=MODO_CHOICES, default='MANUAL')
    editable = models.BooleanField(default=True)
    requerido = models.BooleanField(default=False)
    orden = models.IntegerField(default=0)
    formula = models.TextField(blank=True, help_text='Fórmula para campos calculados (ej: ANCHO - 42)')
    ayuda = models.CharField(max_length=200, blank=True)
    opciones = models.TextField(blank=True, help_text='Opciones para tipo select, separadas por | (ej: BALCON|VENTANA|PUERTA)')

    class Meta:
        verbose_name = 'Campo de Plantilla'
        verbose_name_plural = 'Campos de Plantilla'
        ordering = ['plantilla', 'orden', 'id']
        unique_together = [['plantilla', 'clave']]

    def __str__(self):
        return f"{self.plantilla.nombre} - {self.nombre_visible}"

    def clean(self):
        if self.modo == 'CALCULADO':
            self.editable = False
            if not self.formula:
                raise ValidationError({'formula': 'Los campos calculados requieren una fórmula'})
        
        # Validar que la clave sea alfanumérica y guiones bajos
        if not self.clave.replace('_', '').isalnum():
            raise ValidationError({'clave': 'La clave solo puede contener letras, números y guiones bajos'})


class CalculoEjecucion(models.Model):
    plantilla = models.ForeignKey(ProductoPlantilla, on_delete=models.CASCADE, related_name='ejecuciones')
    inputs_json = models.TextField()
    outputs_json = models.TextField()
    errores_json = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = 'Ejecución de Cálculo'
        verbose_name_plural = 'Ejecuciones de Cálculo'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.plantilla.nombre} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    @property
    def inputs(self):
        return json.loads(self.inputs_json) if self.inputs_json else {}

    @property
    def outputs(self):
        return json.loads(self.outputs_json) if self.outputs_json else {}

    @property
    def errores(self):
        return json.loads(self.errores_json) if self.errores_json else {}


class PedidoFabrica(models.Model):
    ESTADO_CHOICES = [
        ('BORRADOR', 'Borrador'),
        ('EN_PROCESO', 'En Proceso'),
        ('COMPLETADO', 'Completado'),
        ('CANCELADO', 'Cancelado'),
    ]
    
    numero = models.CharField(max_length=50, unique=True)
    cliente = models.CharField(max_length=200)
    fecha = models.DateField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='BORRADOR')
    observaciones = models.TextField(blank=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='pedidos_fabrica')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Pedido de Fábrica'
        verbose_name_plural = 'Pedidos de Fábrica'
        ordering = ['-created_at']

    def __str__(self):
        return f"Pedido {self.numero} - {self.cliente}"


class PedidoFabricaItem(models.Model):
    ESTADO_CHOICES = [
        ('SIN_CALCULAR', 'Sin Calcular'),
        ('OK', 'OK'),
        ('ERROR', 'Con Errores'),
    ]
    
    pedido = models.ForeignKey(PedidoFabrica, on_delete=models.CASCADE, related_name='items')
    plantilla = models.ForeignKey(ProductoPlantilla, on_delete=models.PROTECT)
    orden = models.IntegerField(default=0)
    inputs_json = models.TextField(default='{}')
    outputs_json = models.TextField(default='{}')
    errores_json = models.TextField(default='{}')
    obs = models.TextField(blank=True, verbose_name='Observaciones')
    cantidad = models.IntegerField(default=1, verbose_name='Cantidad')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='SIN_CALCULAR')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Ítem de Pedido'
        verbose_name_plural = 'Ítems de Pedido'
        ordering = ['pedido', 'orden', 'id']

    def __str__(self):
        return f"{self.pedido.numero} - Item #{self.orden} - {self.plantilla.nombre}"

    @property
    def inputs(self):
        return json.loads(self.inputs_json) if self.inputs_json else {}

    @property
    def outputs(self):
        return json.loads(self.outputs_json) if self.outputs_json else {}

    @property
    def errores(self):
        return json.loads(self.errores_json) if self.errores_json else {}
