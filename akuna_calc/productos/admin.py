from django.contrib import admin
from .models import Producto, Cotizacion, CotizacionItem

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'categoria', 'precio_m2', 'formula', 'activo', 'created_at']
    list_filter = ['categoria', 'formula', 'activo']
    search_fields = ['nombre', 'categoria']

class CotizacionItemInline(admin.TabularInline):
    model = CotizacionItem
    extra = 0

@admin.register(Cotizacion)
class CotizacionAdmin(admin.ModelAdmin):
    list_display = ['id', 'fecha', 'usuario', 'total_general']
    list_filter = ['fecha', 'usuario']
    inlines = [CotizacionItemInline]