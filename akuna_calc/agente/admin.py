from django.contrib import admin

from .models import (
    ConfiguracionAgente,
    DiaCerrado,
    EntradaConocimiento,
    FranjaAtencion,
    FranjaTecnico,
    TecnicoVisita,
    ZonaTecnico,
)


class FranjaTecnicoInline(admin.TabularInline):
    model = FranjaTecnico
    extra = 0


class ZonaTecnicoInline(admin.TabularInline):
    model = ZonaTecnico
    extra = 0


@admin.register(TecnicoVisita)
class TecnicoVisitaAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'duracion_minutos', 'cupo_por_franja', 'costo_visita', 'activo')
    inlines = [FranjaTecnicoInline, ZonaTecnicoInline]


@admin.register(EntradaConocimiento)
class EntradaConocimientoAdmin(admin.ModelAdmin):
    list_display = ('tema', 'orden', 'activo', 'updated_at')
    search_fields = ('tema', 'contenido')


admin.site.register(ConfiguracionAgente)
admin.site.register(FranjaAtencion)
admin.site.register(DiaCerrado)
