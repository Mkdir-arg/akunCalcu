from django.urls import path

from . import views

app_name = 'agenda'

urlpatterns = [
    path('', views.EventoListView.as_view(), name='lista'),
    path('calendario/', views.calendario, name='calendario'),
    path('nuevo/', views.EventoCreateView.as_view(), name='crear'),
    path('<int:pk>/editar/', views.EventoUpdateView.as_view(), name='editar'),
    path('<int:pk>/eliminar/', views.EventoDeleteView.as_view(), name='eliminar'),
    path('cliente/<int:pk>/info/', views.cliente_info, name='cliente_info'),
    path('api/pendientes/', views.api_pendientes, name='api_pendientes'),
    path('api/marcar-enviado/', views.api_marcar_enviado, name='api_marcar_enviado'),
]
