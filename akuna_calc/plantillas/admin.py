from django.contrib import admin
from .models import ProductoPlantilla, CampoPlantilla, CalculoEjecucion, PedidoFabrica, PedidoFabricaItem, PedidoFabricaFila


class CampoPlantillaInline(admin.TabularInline):
    model = CampoPlantilla
    extra = 0
    fields = ['orden', 'nombre_visible', 'clave', 'tipo', 'modo', 'formula', 'requerido']


@admin.register(ProductoPlantilla)
class ProductoPlantillaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'activo', 'created_at', 'updated_at']
    list_filter = ['activo', 'created_at']
    search_fields = ['nombre', 'descripcion']
    inlines = [CampoPlantillaInline]


@admin.register(CampoPlantilla)
class CampoPlantillaAdmin(admin.ModelAdmin):
    list_display = ['plantilla', 'nombre_visible', 'clave', 'tipo', 'modo', 'orden']
    list_filter = ['plantilla', 'tipo', 'modo']
    search_fields = ['nombre_visible', 'clave']
    ordering = ['plantilla', 'orden']


@admin.register(CalculoEjecucion)
class CalculoEjecucionAdmin(admin.ModelAdmin):
    list_display = ['plantilla', 'usuario', 'created_at']
    list_filter = ['plantilla', 'created_at']
    readonly_fields = ['inputs_json', 'outputs_json', 'errores_json', 'created_at']
    date_hierarchy = 'created_at'


class PedidoFabricaItemInline(admin.TabularInline):
    model = PedidoFabricaItem
    extra = 0
    fields = ['plantilla', 'orden']


@admin.register(PedidoFabrica)
class PedidoFabricaAdmin(admin.ModelAdmin):
    list_display = ['numero', 'cliente', 'fecha', 'estado', 'usuario']
    list_filter = ['estado', 'fecha']
    search_fields = ['numero', 'cliente']
    inlines = [PedidoFabricaItemInline]


@admin.register(PedidoFabricaItem)
class PedidoFabricaItemAdmin(admin.ModelAdmin):
    list_display = ['pedido', 'plantilla', 'orden']
    list_filter = ['plantilla']


@admin.register(PedidoFabricaFila)
class PedidoFabricaFilaAdmin(admin.ModelAdmin):
    list_display = ['item', 'orden', 'cantidad', 'estado']
    list_filter = ['estado']
    readonly_fields = ['inputs_json', 'outputs_json', 'errores_json']
