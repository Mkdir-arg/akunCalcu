from django.db import models


class ConfiguracionGeneral(models.Model):
    clave = models.CharField(max_length=100, unique=True, primary_key=True)
    valor = models.TextField()
    descripcion = models.TextField(blank=True, null=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'configuracion_general'
        verbose_name = 'Configuración'
        verbose_name_plural = 'Configuraciones'

    def __str__(self):
        return f"{self.clave}: {self.valor}"

    @classmethod
    def get_valor_hora_hombre(cls):
        try:
            config = cls.objects.get(clave='valor_hora_hombre')
            return float(config.valor)
        except (cls.DoesNotExist, ValueError):
            return 0.0

    @classmethod
    def set_valor_hora_hombre(cls, valor):
        config, _ = cls.objects.update_or_create(
            clave='valor_hora_hombre',
            defaults={
                'valor': str(valor),
                'descripcion': 'Valor por hora de mano de obra'
            }
        )
        return config
