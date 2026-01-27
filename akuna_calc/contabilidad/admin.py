from django.contrib import admin
from .models import Ejercicio, Cuenta, Asiento, AsientoLinea, ConfiguracionContable


class AsientoLineaInline(admin.TabularInline):
    model = AsientoLinea
    extra = 2
    fields = ['cuenta', 'debe', 'haber', 'detalle']


@admin.register(Ejercicio)
class EjercicioAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'fecha_inicio', 'fecha_cierre', 'cerrado']
    list_filter = ['cerrado']


@admin.register(Cuenta)
class CuentaAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'tipo', 'nivel', 'imputable', 'activa']
    list_filter = ['tipo', 'nivel', 'imputable', 'activa']
    search_fields = ['codigo', 'nombre']
    ordering = ['codigo']


@admin.register(Asiento)
class AsientoAdmin(admin.ModelAdmin):
    list_display = ['numero', 'fecha', 'tipo', 'descripcion', 'get_total_debe', 'get_total_haber', 'esta_balanceado']
    list_filter = ['tipo', 'fecha']
    search_fields = ['numero', 'descripcion']
    inlines = [AsientoLineaInline]
    readonly_fields = ['created_by', 'created_at']


@admin.register(ConfiguracionContable)
class ConfiguracionContableAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Cuentas Patrimoniales', {
            'fields': ('cuenta_clientes', 'cuenta_proveedores', 'cuenta_caja', 'cuenta_banco')
        }),
        ('Cuentas de Resultados', {
            'fields': ('cuenta_ventas', 'cuenta_costo_ventas')
        }),
        ('Cuentas Impositivas', {
            'fields': ('cuenta_iva_debito', 'cuenta_iva_credito')
        }),
    )
