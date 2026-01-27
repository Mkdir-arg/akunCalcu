from django.urls import path
from . import views

app_name = 'facturacion'

urlpatterns = [
    path('', views.lista_facturas, name='lista_facturas'),
    path('nueva/', views.crear_factura, name='crear_factura'),
    path('<int:factura_id>/', views.detalle_factura, name='detalle_factura'),
    path('desde-venta/<int:venta_id>/', views.crear_factura_desde_venta, name='crear_factura_desde_venta'),
    path('libro-iva-ventas/', views.libro_iva_ventas, name='libro_iva_ventas'),
]
