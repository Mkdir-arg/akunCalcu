from django.urls import path
from . import views

app_name = 'presupuestos'

urlpatterns = [
    path('', views.lista, name='presupuestos-lista'),
    path('nuevo/', views.crear, name='presupuestos-crear'),
    path('<int:pk>/', views.detalle, name='presupuestos-detalle'),
    path('<int:pk>/editar/', views.editar, name='presupuestos-editar'),
    path('<int:pk>/item/agregar/', views.agregar_item, name='presupuestos-item-agregar'),
    path('<int:pk>/item/<int:ipk>/eliminar/', views.eliminar_item, name='presupuestos-item-eliminar'),
    path('<int:pk>/comentar/', views.comentar, name='presupuestos-comentar'),
    path('<int:pk>/estado/', views.cambiar_estado, name='presupuestos-estado'),
    path('<int:pk>/pdf/', views.pdf, name='presupuestos-pdf'),
]
