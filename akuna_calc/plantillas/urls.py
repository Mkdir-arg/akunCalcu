from django.urls import path
from . import views

app_name = 'plantillas'

urlpatterns = [
    # ABM Plantillas
    path('', views.plantilla_list, name='plantilla_list'),
    path('crear/', views.plantilla_create, name='plantilla_create'),
    path('<int:pk>/editar/', views.plantilla_edit, name='plantilla_edit'),
    path('<int:pk>/toggle/', views.plantilla_toggle, name='plantilla_toggle'),
    
    # Configurador de Campos
    path('<int:pk>/campos/', views.plantilla_campos, name='plantilla_campos'),
    path('<int:plantilla_pk>/campos/crear/', views.campo_create, name='campo_create'),
    path('campos/<int:pk>/editar/', views.campo_edit, name='campo_edit'),
    path('campos/<int:pk>/eliminar/', views.campo_delete, name='campo_delete'),
    
    # Probar Plantilla
    path('<int:pk>/probar/', views.plantilla_probar, name='plantilla_probar'),
    
    # Pantalla Operativa
    path('calcular/', views.calcular_index, name='calcular_index'),
    path('calcular/<int:pk>/', views.calcular_ejecutar, name='calcular_ejecutar'),
    path('calcular/<int:pk>/ajax/', views.calcular_ajax, name='calcular_ajax'),
    
    # Historial
    path('historial/', views.historial_calculos, name='historial_calculos'),
    
    # Pedidos de Fábrica
    path('pedidos/', views.pedido_list, name='pedido_list'),
    path('pedidos/crear/', views.pedido_create, name='pedido_create'),
    path('pedidos/<int:pk>/', views.pedido_detail, name='pedido_detail'),
    path('pedidos/<int:pedido_pk>/agregar-item/', views.pedido_add_item, name='pedido_add_item'),
    path('pedidos/items/<int:item_pk>/calcular/', views.pedido_item_calcular, name='pedido_item_calcular'),
    path('pedidos/items/<int:item_pk>/agregar-fila/', views.pedido_item_add_fila, name='pedido_item_add_fila'),
    path('pedidos/items/<int:item_pk>/duplicar/', views.pedido_item_duplicate, name='pedido_item_duplicate'),
    path('pedidos/items/<int:item_pk>/eliminar/', views.pedido_item_delete, name='pedido_item_delete'),
    path('pedidos/filas/<int:fila_pk>/eliminar/', views.pedido_fila_delete, name='pedido_fila_delete'),
]
