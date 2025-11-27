from django.contrib import admin
from .models import Cliente, Venta, TipoCuenta, Cuenta, Compra


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'apellido', 'razon_social', 'localidad', 'telefono']
    search_fields = ['nombre', 'apellido', 'razon_social']
    list_filter = ['localidad', 'created_at']


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ['numero_pedido', 'cliente', 'valor_total', 'estado', 'fecha_pago']
    list_filter = ['estado', 'forma_pago', 'con_factura', 'created_at']
    search_fields = ['numero_pedido', 'cliente__nombre', 'cliente__apellido']
    readonly_fields = ['saldo']


@admin.register(TipoCuenta)
class TipoCuentaAdmin(admin.ModelAdmin):
    list_display = ['tipo', 'descripcion', 'activo']
    list_filter = ['activo']


@admin.register(Cuenta)
class CuentaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo_cuenta', 'razon_social', 'activo']
    list_filter = ['tipo_cuenta', 'activo']
    search_fields = ['nombre', 'razon_social']


@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = ['numero_pedido', 'cuenta', 'fecha_pago', 'importe_abonado', 'created_by']
    list_filter = ['cuenta__tipo_cuenta', 'fecha_pago', 'created_by']
    search_fields = ['numero_pedido', 'cuenta__nombre']