from django.contrib import admin

from .models import EventoAgenda


@admin.register(EventoAgenda)
class EventoAgendaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo', 'fecha_evento', 'hora_envio', 'recurrencia', 'estado', 'activo')
    list_filter = ('tipo', 'recurrencia', 'estado', 'activo')
    search_fields = ('titulo', 'descripcion')
    filter_horizontal = ('destinatarios',)
