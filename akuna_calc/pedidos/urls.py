from django.urls import path

from . import views

app_name = 'pedidos'

urlpatterns = [
    path('', views.pedidos_list, name='lista'),
    path('api/crear-borrador/', views.api_crear_borrador, name='api_crear_borrador'),
    path('api/confirmar/', views.api_confirmar, name='api_confirmar'),
]
