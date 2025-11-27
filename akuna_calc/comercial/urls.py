from django.urls import path
from . import views

app_name = 'comercial'

urlpatterns = [
    # Dashboard
    path('', views.dashboard_comercial, name='dashboard'),
    
    # Ventas
    path('ventas/', views.ventas_list, name='ventas_list'),
    path('ventas/nueva/', views.venta_create, name='venta_create'),
    path('ventas/<int:pk>/editar/', views.venta_edit, name='venta_edit'),
    
    # Clientes
    path('clientes/', views.clientes_list, name='clientes_list'),
    path('clientes/nuevo/', views.cliente_create, name='cliente_create'),
    path('clientes/<int:pk>/editar/', views.cliente_edit, name='cliente_edit'),
    
    # Compras
    path('compras/', views.compras_list, name='compras_list'),
    path('compras/nueva/', views.compra_create, name='compra_create'),
    path('compras/<int:pk>/editar/', views.compra_edit, name='compra_edit'),
    
    # Cuentas
    path('cuentas/', views.cuentas_list, name='cuentas_list'),
    path('cuentas/nueva/', views.cuenta_create, name='cuenta_create'),
    path('cuentas/<int:pk>/editar/', views.cuenta_edit, name='cuenta_edit'),
    
    # Reportes
    path('reportes/', views.reportes, name='reportes'),
    
    # API
    path('api/cuentas-by-tipo/', views.get_cuentas_by_tipo, name='cuentas_by_tipo'),
]