from django.urls import path

from . import views

app_name = 'optimizador'

urlpatterns = [
    path('', views.nuevo, name='nuevo'),
    path('calcular/', views.calcular, name='calcular'),
    path('guardar/', views.guardar, name='guardar'),
    path('planes/', views.lista, name='lista'),
    path('planes/<int:pk>/', views.detalle, name='detalle'),
    path('planes/<int:pk>/pdf/', views.pdf, name='pdf'),
]
