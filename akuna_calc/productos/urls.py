from django.urls import path
from . import views

app_name = 'productos'

urlpatterns = [
    path('calculadora/', views.calculadora_rapida, name='calculadora'),
    path('productos/', views.productos_list, name='productos_list'),
    path('productos/nuevo/', views.producto_create, name='producto_create'),
    path('productos/<int:pk>/editar/', views.producto_update, name='producto_update'),
    path('productos/<int:pk>/toggle/', views.producto_toggle_active, name='producto_toggle_active'),
    path('cotizaciones/', views.cotizacion_list, name='cotizacion_list'),
    path('cotizaciones/nueva/', views.crear_cotizacion, name='cotizacion_create'),
    path('cotizaciones/<int:pk>/', views.cotizacion_detail, name='cotizacion_detail'),
    path('cotizaciones/<int:pk>/cambiar-estado/', views.cambiar_estado_cotizacion, name='cambiar_estado_cotizacion'),
    path('cotizaciones/<int:pk>/eliminar/', views.cotizacion_delete, name='cotizacion_delete'),
]