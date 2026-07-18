from django.contrib import admin

from .models import ConfiguracionSolicitudes, SolicitudPresupuesto


@admin.register(SolicitudPresupuesto)
class SolicitudPresupuestoAdmin(admin.ModelAdmin):
    list_display = ('nombre_cliente', 'email', 'vendedor', 'estado', 'fecha_recepcion')
    list_filter = ('estado', 'vendedor')
    search_fields = ('nombre_cliente', 'email', 'telefono', 'asunto')
    date_hierarchy = 'fecha_recepcion'


@admin.register(ConfiguracionSolicitudes)
class ConfiguracionSolicitudesAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'ultimo_vendedor', 'updated_at')
