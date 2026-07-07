from django.urls import path
from . import views

urlpatterns = [
    path('', views.configuracion_general, name='configuracion-general'),
    path('hora-hombre/', views.editar_valor_hora_hombre, name='configuracion-hora-hombre'),
    path('datos-empresa/', views.editar_datos_empresa, name='configuracion-datos-empresa'),
]
