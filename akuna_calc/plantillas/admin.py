from django.contrib import admin
from .models import PedidoFabrica, OrdenFabricacion, MedidaOrdenFabricacion


@admin.register(PedidoFabrica)
class PedidoFabricaAdmin(admin.ModelAdmin):
    list_display = ['numero', 'cliente', 'fecha', 'estado', 'usuario']
    list_filter = ['estado', 'fecha']
    search_fields = ['numero', 'cliente']


class MedidaOrdenFabricacionInline(admin.TabularInline):
    model = MedidaOrdenFabricacion
    extra = 0


@admin.register(OrdenFabricacion)
class OrdenFabricacionAdmin(admin.ModelAdmin):
    list_display = ['numero', 'pedido', 'tipo_abertura', 'linea', 'color']
    search_fields = ['numero', 'cliente_nombre', 'pedido__numero']
    inlines = [MedidaOrdenFabricacionInline]
