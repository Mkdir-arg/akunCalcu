from django.urls import path

from . import views

app_name = 'resumenes'

urlpatterns = [
    path('api/datos/', views.api_datos, name='api_datos'),
    path('api/guardar/', views.api_guardar, name='api_guardar'),
    path('api/ultimo/', views.api_ultimo, name='api_ultimo'),
]
