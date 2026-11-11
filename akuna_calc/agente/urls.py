from django.urls import path

from . import views

app_name = 'agente'

urlpatterns = [
    path('configuracion/', views.configuracion, name='configuracion'),

    path('horario/', views.horario, name='horario'),
    path('horario/franjas/nueva/', views.franja_crear, name='franja_crear'),
    path('horario/franjas/<int:pk>/editar/', views.franja_editar, name='franja_editar'),
    path('horario/franjas/<int:pk>/eliminar/', views.franja_eliminar, name='franja_eliminar'),
    path('horario/cerrados/nuevo/', views.dia_cerrado_crear, name='dia_cerrado_crear'),
    path('horario/cerrados/<int:pk>/eliminar/', views.dia_cerrado_eliminar, name='dia_cerrado_eliminar'),

    path('visitas/', views.TecnicoListView.as_view(), name='tecnicos'),
    path('visitas/nuevo/', views.TecnicoCreateView.as_view(), name='tecnico_crear'),
    path('visitas/<int:pk>/editar/', views.TecnicoUpdateView.as_view(), name='tecnico_editar'),
    path('visitas/<int:pk>/eliminar/', views.TecnicoDeleteView.as_view(), name='tecnico_eliminar'),

    path('conocimiento/', views.ConocimientoListView.as_view(), name='conocimiento'),
    path('conocimiento/nueva/', views.ConocimientoCreateView.as_view(), name='conocimiento_crear'),
    path('conocimiento/<int:pk>/editar/', views.ConocimientoUpdateView.as_view(), name='conocimiento_editar'),
    path('conocimiento/<int:pk>/eliminar/', views.ConocimientoDeleteView.as_view(), name='conocimiento_eliminar'),

    path('simulador/', views.SimuladorListView.as_view(), name='simulador'),
    path('simulador/nueva/', views.simulacion_nueva, name='simulacion_nueva'),
    path('simulador/<int:pk>/', views.simulacion, name='simulacion'),
    path('simulador/<int:pk>/enviar/', views.simulacion_enviar, name='simulacion_enviar'),
]
