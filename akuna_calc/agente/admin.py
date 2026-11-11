from django.contrib import admin

from .models import (
    ConfiguracionAgente,
    Conversacion,
    DiaCerrado,
    EntradaConocimiento,
    FranjaAtencion,
    FranjaTecnico,
    Mensaje,
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


class MensajeInline(admin.TabularInline):
    model = Mensaje
    extra = 0
    readonly_fields = ('rol', 'texto', 'detalle', 'created_at')


@admin.register(Conversacion)
class ConversacionAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'canal', 'es_simulacion', 'iniciada_por', 'updated_at')
    list_filter = ('canal', 'es_simulacion')
    inlines = [MensajeInline]
