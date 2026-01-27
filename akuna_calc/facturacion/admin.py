from django.contrib import admin
from .models import PuntoVenta, Factura, FacturaItem, LibroIVAVentas


class FacturaItemInline(admin.TabularInline):
    model = FacturaItem
    extra = 1
    fields = ['descripcion', 'cantidad', 'precio_unitario', 'alicuota_iva', 'subtotal', 'iva', 'total']
    readonly_fields = ['subtotal', 'iva', 'total']


@admin.register(PuntoVenta)
class PuntoVentaAdmin(admin.ModelAdmin):
    list_display = ['numero', 'nombre', 'activo']
    list_filter = ['activo']
    search_fields = ['nombre']


@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display = ['get_numero_completo', 'tipo', 'cliente', 'fecha', 'total', 'estado', 'cae']
    list_filter = ['tipo', 'estado', 'fecha', 'punto_venta']
    search_fields = ['numero', 'cliente__nombre', 'cliente__apellido', 'cae']
    readonly_fields = ['cae', 'cae_vencimiento', 'created_at', 'updated_at']
    inlines = [FacturaItemInline]
    
    fieldsets = (
        ('Datos del Comprobante', {
            'fields': ('tipo', 'punto_venta', 'numero', 'fecha', 'cliente', 'venta')
        }),
        ('Importes', {
            'fields': ('subtotal_neto', 'iva_21', 'iva_105', 'iva_27', 'exento', 'total')
        }),
        ('AFIP', {
            'fields': ('estado', 'cae', 'cae_vencimiento', 'observaciones_afip')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(LibroIVAVentas)
class LibroIVAVentasAdmin(admin.ModelAdmin):
    list_display = ['periodo', 'factura', 'neto_gravado_21', 'iva_21', 'total']
    list_filter = ['periodo']
    date_hierarchy = 'periodo'
