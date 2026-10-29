from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import live_api, views

urlpatterns = [
    path('health/', views.healthcheck, name='healthcheck'),
    path('login/', views.AkunLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('core/api/live/', live_api.live_poll, name='core_api_live'),
    path('core/api/avisos/leido/', live_api.aviso_leido, name='core_api_aviso_leido'),
    path('home/', views.home, name='home'),
    path('', views.index, name='index'),
]
