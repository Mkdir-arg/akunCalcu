from django.urls import path

from . import views

app_name = 'novedades'

urlpatterns = [
    path('', views.lista, name='lista'),
    path('leidas/', views.marcar_leidas_view, name='marcar_leidas'),
    path('bandeja/', views.bandeja, name='bandeja'),
    path('bandeja/nueva/', views.crear, name='crear'),
    path('bandeja/<int:pk>/', views.editar, name='editar'),
    path('pedidos/', views.pedidos, name='pedidos'),
    path('pedidos/nuevo/', views.pedido_crear, name='pedido_crear'),
    path('pedidos/<int:pk>/', views.pedido_detalle, name='pedido_detalle'),
    path('pedidos/<int:pk>/estado/', views.pedido_estado, name='pedido_estado'),
    path('api/borrador/', views.api_borrador, name='api_borrador'),
]
