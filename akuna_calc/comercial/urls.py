from django.urls import path
from . import views

app_name = 'comercial'

urlpatterns = [
    # Dashboard
    path('', views.dashboard_comercial, name='dashboard'),
    
    # Ventas
    path('ventas/', views.ventas_list, name='ventas_list'),
    path('ventas/nueva/', views.venta_create, name='venta_create'),
    path('ventas/<int:pk>/', views.venta_detail, name='venta_detail'),
    path('ventas/<int:pk>/editar/', views.venta_edit, name='venta_edit'),
    path('ventas/<int:pk>/eliminar/', views.venta_delete, name='venta_delete'),
    path('ventas/<int:pk>/pago/', views.registrar_pago, name='registrar_pago'),
    path('ventas/<int:pk>/pdf/', views.generar_pdf_venta, name='generar_pdf_venta'),
    
    # Clientes
    path('clientes/', views.clientes_list, name='clientes_list'),
    path('clientes/nuevo/', views.cliente_create, name='cliente_create'),
    path('clientes/<int:pk>/editar/', views.cliente_edit, name='cliente_edit'),
    path('clientes/<int:pk>/eliminar/', views.cliente_delete, name='cliente_delete'),
    
    # Compras
    path('compras/', views.compras_list, name='compras_list'),
    path('compras/nueva/', views.compra_create, name='compra_create'),
    path('compras/<int:pk>/editar/', views.compra_edit, name='compra_edit'),
    path('compras/<int:pk>/eliminar/', views.compra_delete, name='compra_delete'),
    
    # Cuentas
    path('cuentas/', views.cuentas_list, name='cuentas_list'),
    path('cuentas/nueva/', views.cuenta_create, name='cuenta_create'),
    path('cuentas/<int:pk>/editar/', views.cuenta_edit, name='cuenta_edit'),
    path('cuentas/<int:pk>/eliminar/', views.cuenta_delete, name='cuenta_delete'),
    
    # Tipos de Cuenta
    path('tipos-cuenta/', views.tipos_cuenta_list, name='tipos_cuenta_list'),
    path('tipos-cuenta/nuevo/', views.tipo_cuenta_create, name='tipo_cuenta_create'),
    path('tipos-cuenta/<int:pk>/editar/', views.tipo_cuenta_edit, name='tipo_cuenta_edit'),
    path('tipos-cuenta/<int:pk>/eliminar/', views.tipo_cuenta_delete, name='tipo_cuenta_delete'),
    
    # Tipos de Gasto
    path('tipos-gasto/', views.tipos_gasto_list, name='tipos_gasto_list'),
    path('tipos-gasto/nuevo/', views.tipo_gasto_create, name='tipo_gasto_create'),
    path('tipos-gasto/<int:pk>/editar/', views.tipo_gasto_edit, name='tipo_gasto_edit'),
    path('tipos-gasto/<int:pk>/eliminar/', views.tipo_gasto_delete, name='tipo_gasto_delete'),
    
    # Reportes
    path('reportes/', views.reportes, name='reportes'),
    path('reportes/exportar-excel/', views.exportar_reporte_excel, name='exportar_reporte_excel'),
    
    # API
    path('api/tipos-gasto-by-cuenta/', views.get_tipos_gasto_by_cuenta, name='tipos_gasto_by_cuenta'),
    path('api/cuentas-by-tipo/', views.get_cuentas_by_tipo, name='cuentas_by_tipo'),
    path('api/clientes-list/', views.get_clientes_list, name='clientes_list_api'),
    path('api/pago/<int:pk>/editar/', views.editar_pago, name='editar_pago'),
    path('api/venta/<int:pk>/editar-fecha-sena/', views.editar_fecha_sena, name='editar_fecha_sena'),
]