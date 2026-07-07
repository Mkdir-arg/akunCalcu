from django.urls import path
from . import views
from .views_opcionales import opcional_list, opcional_create, opcional_edit, opcional_delete, opcional_formulas_guardar, opcional_accesorios_guardar, opcional_relaciones_guardar

app_name = 'plantillas'

urlpatterns = [
    path('', views.index, name='index'),

    # Pedidos de Fábrica
    path('pedidos/', views.pedido_list, name='pedido_list'),
    path('pedidos/crear/', views.pedido_create, name='pedido_create'),
    path('pedidos/<int:pk>/', views.pedido_detail, name='pedido_detail'),

    # Órdenes de Fabricación
    path('pedidos/<int:pedido_pk>/ordenes/crear/', views.orden_create, name='orden_create'),
    path('ordenes/<int:pk>/editar/', views.orden_edit, name='orden_edit'),
    path('ordenes/<int:pk>/eliminar/', views.orden_delete, name='orden_delete'),
    path('ordenes/<int:pk>/pdf/', views.orden_pdf, name='orden_pdf'),

    # Opcionales de Fábrica
    path('opcionales/', opcional_list, name='opcional_list'),
    path('opcionales/crear/', opcional_create, name='opcional_create'),
    path('opcionales/<int:pk>/editar/', opcional_edit, name='opcional_edit'),
    path('opcionales/<int:pk>/eliminar/', opcional_delete, name='opcional_delete'),
    path('opcionales/<int:pk>/formulas/guardar/', opcional_formulas_guardar, name='opcional_formulas_guardar'),
    path('opcionales/<int:pk>/accesorios/guardar/', opcional_accesorios_guardar, name='opcional_accesorios_guardar'),
    path('opcionales/<int:pk>/relaciones/guardar/', opcional_relaciones_guardar, name='opcional_relaciones_guardar'),
]
