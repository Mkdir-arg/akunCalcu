from django.db import models


class Resumen(models.Model):
    PERIODO_CHOICES = [
        ('dia', 'Día'),
        ('semana', 'Semana'),
    ]

    periodo = models.CharField(max_length=10, choices=PERIODO_CHOICES, verbose_name='Período')
    desde = models.DateField(verbose_name='Desde')
    hasta = models.DateField(verbose_name='Hasta')
    datos = models.JSONField(default=dict, verbose_name='Datos calculados')
    texto = models.TextField(verbose_name='Texto redactado')
    abierto_por = models.JSONField(default=list, blank=True, verbose_name='Abierto por (teléfonos)')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Generado')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Resumen'
        verbose_name_plural = 'Resúmenes'
        ordering = ['-hasta', '-created_at']
        constraints = [
            models.UniqueConstraint(fields=['periodo', 'hasta'], name='resumen_unico_por_periodo'),
        ]

    def __str__(self):
        if self.periodo == 'semana':
            return f'Resumen de la semana {self.desde:%d/%m} al {self.hasta:%d/%m/%Y}'
        return f'Resumen del día {self.hasta:%d/%m/%Y}'
