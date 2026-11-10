from django.urls import path

from . import views

app_name = 'novedades'

urlpatterns = [
    path('', views.lista, name='lista'),
    path('leidas/', views.marcar_leidas_view, name='marcar_leidas'),
    path('bandeja/', views.bandeja, name='bandeja'),
    path('bandeja/nueva/', views.crear, name='crear'),
    path('bandeja/<int:pk>/', views.editar, name='editar'),
    path('api/borrador/', views.api_borrador, name='api_borrador'),
]
