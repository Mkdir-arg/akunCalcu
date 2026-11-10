from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class PlanCorte(models.Model):
    """Plan de corte de perfiles de marco: parámetros, foto del cálculo y órdenes que incluyó (REQ-070)."""

    numero = models.PositiveIntegerField(unique=True, verbose_name='N° de plan')
    usuario = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='planes_corte', verbose_name='Creado por',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado el')
    disco_mm = models.DecimalField(max_digits=5, decimal_places=1, default=4, verbose_name='Espesor del disco (mm)')
    despunte_mm = models.DecimalField(max_digits=6, decimal_places=1, default=10, verbose_name='Despunte (mm)')
    largo_barra_mm = models.PositiveIntegerField(
        null=True, blank=True, verbose_name='Largo de barra forzado (mm)',
        help_text='Vacío: el de cada perfil en el catálogo.',
    )
    recorte_min_mm = models.PositiveIntegerField(
        null=True, blank=True, verbose_name='Guardar recortes desde (mm)',
        help_text='Vacío: el mínimo reutilizable de cada perfil.',
    )
    resultado = models.JSONField(default=dict, verbose_name='Resultado del cálculo')
    firma = models.CharField(max_length=40, blank=True, verbose_name='Firma de las órdenes')
    pedidos = models.ManyToManyField('plantillas.PedidoFabrica', related_name='planes_corte', blank=True, verbose_name='Pedidos')
    ordenes = models.ManyToManyField('plantillas.OrdenFabricacion', related_name='planes_corte', blank=True, verbose_name='Órdenes incluidas')

    class Meta:
        verbose_name = 'Plan de corte'
        verbose_name_plural = 'Planes de corte'
        ordering = ['-numero']

    def __str__(self):
        return f'Plan de corte {self.numero_formateado}'

    @property
    def numero_formateado(self):
        return f'{self.numero:04d}'

    @classmethod
    def generar_numero(cls):
        return (cls.objects.aggregate(mayor=models.Max('numero'))['mayor'] or 0) + 1

    def esta_vigente(self):
        """False si cambió la medida, el marco o el color de alguna orden incluida, o si se borró una."""
        from .services.plan import firma_de_ordenes

        return firma_de_ordenes(self.ordenes.all()) == self.firma
