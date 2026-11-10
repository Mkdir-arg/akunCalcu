from django.contrib import admin

from .models import LecturaNovedades, Noticia


@admin.register(Noticia)
class NoticiaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'estado', 'tipo', 'modulo', 'origen', 'creada_en', 'publicada_en')
    list_filter = ('estado', 'tipo', 'origen')
    search_fields = ('titulo', 'texto', 'sha')


admin.site.register(LecturaNovedades)
