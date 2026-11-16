from django.contrib import admin

from .models import ComentarioPedido, LecturaNovedades, Noticia, PedidoDesarrollo


@admin.register(Noticia)
class NoticiaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'estado', 'tipo', 'modulo', 'origen', 'creada_en', 'publicada_en')
    list_filter = ('estado', 'tipo', 'origen')
    search_fields = ('titulo', 'texto', 'sha')


admin.site.register(LecturaNovedades)


class ComentarioPedidoInline(admin.TabularInline):
    model = ComentarioPedido
    extra = 0


@admin.register(PedidoDesarrollo)
class PedidoDesarrolloAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'etiqueta', 'estado', 'creado_por', 'creado_en')
    list_filter = ('estado', 'etiqueta')
    search_fields = ('titulo', 'comentario')
    inlines = [ComentarioPedidoInline]
