from django.urls import path
from . import views

urlpatterns = [
    path('usuarios/', views.user_list, name='user_list'),
    path('usuarios/nuevo/', views.user_create, name='user_create'),
    path('usuarios/<int:pk>/editar/', views.user_update, name='user_update'),
    path('usuarios/<int:pk>/toggle/', views.user_toggle, name='user_toggle'),
]