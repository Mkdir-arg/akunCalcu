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

    # Claves de datos de contacto de la empresa (usadas en el pie del PDF de fábrica).
    EMPRESA_DEFAULTS = {
        'empresa_nombre': 'Akun Aberturas',
        'empresa_direccion': 'José Cubas 4388, CABA',
        'empresa_telefonos': '11 2345 6789 / 11 4567 8901',
        'empresa_web': 'www.akunaberturas.com.ar',
    }

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

    @classmethod
    def get_valor(cls, clave, default=''):
        try:
            return cls.objects.get(clave=clave).valor
        except cls.DoesNotExist:
            return default

    @classmethod
    def set_valor(cls, clave, valor, descripcion=''):
        config, _ = cls.objects.update_or_create(
            clave=clave,
            defaults={'valor': str(valor), 'descripcion': descripcion},
        )
        return config

    @classmethod
    def get_datos_empresa(cls):
        return {
            clave: cls.get_valor(clave, default)
            for clave, default in cls.EMPRESA_DEFAULTS.items()
        }
