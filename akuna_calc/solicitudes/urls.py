from django.urls import path

from . import views

app_name = 'solicitudes'

urlpatterns = [
    path('', views.solicitud_list, name='lista'),
    path('<int:pk>/contestada/', views.solicitud_marcar_contestada, name='marcar_contestada'),
    path('<int:pk>/reasignar/', views.solicitud_reasignar, name='reasignar'),
    path('api/crear/', views.api_crear, name='api_crear'),
    path('api/recordatorios/', views.api_recordatorios, name='api_recordatorios'),
    path('api/marcar-recordatorio/', views.api_marcar_recordatorio, name='api_marcar_recordatorio'),
    path('api/marcar-contestada/', views.api_marcar_contestada, name='api_marcar_contestada'),
]
