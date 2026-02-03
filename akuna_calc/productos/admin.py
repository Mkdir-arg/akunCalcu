from django.contrib import admin
from .models import Producto

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'categoria', 'precio_m2', 'formula', 'activo', 'created_at']
    list_filter = ['categoria', 'formula', 'activo']
    search_fields = ['nombre', 'categoria']