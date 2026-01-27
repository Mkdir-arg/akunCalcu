from django.urls import path
from . import views

app_name = 'facturacion'

urlpatterns = [
    path('', views.lista_facturas, name='lista_facturas'),
    path('nueva/', views.crear_factura, name='crear_factura'),
    path('<int:factura_id>/', views.detalle_factura, name='detalle_factura'),
    path('desde-venta/<int:venta_id>/', views.crear_factura_desde_venta, name='crear_factura_desde_venta'),
    path('libro-iva-ventas/', views.libro_iva_ventas, name='libro_iva_ventas'),
    
    # Puntos de Venta
    path('puntos-venta/', views.puntos_venta_list, name='puntos_venta_list'),
    path('puntos-venta/nuevo/', views.punto_venta_create, name='punto_venta_create'),
    path('puntos-venta/<int:pk>/editar/', views.punto_venta_edit, name='punto_venta_edit'),
]
