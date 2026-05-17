from django.urls import path

from . import views

app_name = 'gastos_diarios'

urlpatterns = [
    path('', views.gasto_list, name='lista'),
    path('<int:pk>/aprobar/', views.gasto_aprobar, name='aprobar'),
    path('<int:pk>/rechazar/', views.gasto_rechazar, name='rechazar'),
    path('numeros/', views.numero_list, name='numero_list'),
    path('numeros/crear/', views.numero_create, name='numero_create'),
    path('numeros/<int:pk>/editar/', views.numero_edit, name='numero_edit'),
    path('numeros/<int:pk>/eliminar/', views.numero_delete, name='numero_delete'),
    path('api/crear-borrador/', views.api_crear_borrador, name='api_crear_borrador'),
    path('api/confirmar/', views.api_confirmar, name='api_confirmar'),
]
