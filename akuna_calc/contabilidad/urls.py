from django.urls import path
from . import views

app_name = 'contabilidad'

urlpatterns = [
    path('plan-cuentas/', views.plan_cuentas, name='plan_cuentas'),
    path('libro-diario/', views.libro_diario, name='libro_diario'),
    path('libro-mayor/<int:cuenta_id>/', views.libro_mayor, name='libro_mayor'),
    path('balance-sumas-saldos/', views.balance_sumas_saldos, name='balance_sumas_saldos'),
    path('estado-resultados/', views.estado_resultados, name='estado_resultados'),
    path('balance-general/', views.balance_general, name='balance_general'),
    path('asiento/nuevo/', views.crear_asiento, name='crear_asiento'),
]
