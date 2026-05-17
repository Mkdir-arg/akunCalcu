from django.contrib import admin

from .models import GastoDiario, NumeroAutorizado


@admin.register(NumeroAutorizado)
class NumeroAutorizadoAdmin(admin.ModelAdmin):
    list_display = ('numero', 'nombre', 'activo', 'created_at')
    list_filter = ('activo',)
    search_fields = ('numero', 'nombre')


@admin.register(GastoDiario)
class GastoDiarioAdmin(admin.ModelAdmin):
    list_display = ('id', 'descripcion', 'monto', 'estado', 'numero_origen', 'fecha')
    list_filter = ('estado', 'fecha')
    search_fields = ('descripcion', 'numero_origen', 'audio_id')
    readonly_fields = ('audio_id', 'numero_origen', 'transcripcion', 'created_at', 'updated_at')
