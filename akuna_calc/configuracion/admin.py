from django.contrib import admin
from .models import ConfiguracionGeneral


@admin.register(ConfiguracionGeneral)
class ConfiguracionGeneralAdmin(admin.ModelAdmin):
    list_display = ('clave', 'valor', 'descripcion', 'actualizado')
    search_fields = ('clave', 'descripcion')
    readonly_fields = ('actualizado',)
