"""URL routing for pricing app."""

from django.urls import path

from .views import PricingCalculateView, cotizador_view
from .catalog_views import (
    ExtrusorasListView, LineasListView, ProductosListView,
    MarcosListView, HojasListView, InterioresListView, VidriosListView,
    PerfilesListView, AccesoriosListView, TratamientosListView,
    MosquiterosListView, ContravidriosListView, ContravidriosExteriorListView,
    CrucesListView, VidriosRepartidosListView
)
from .config_views import (
    extrusoras_config, lineas_config, productos_config, marcos_config,
    hojas_config, interiores_config, perfiles_config, accesorios_config,
    vidrios_config, tratamientos_config
)

urlpatterns = [
    # Cotizador
    path("cotizador/", cotizador_view, name="pricing-cotizador"),
    
    # API Endpoints
    path("api/pricing/calculate/", PricingCalculateView.as_view(), name="pricing-calculate"),
    path("api/pricing/extrusoras/", ExtrusorasListView.as_view(), name="extrusoras-list"),
    path("api/pricing/lineas/", LineasListView.as_view(), name="lineas-list"),
    path("api/pricing/productos/", ProductosListView.as_view(), name="productos-list"),
    path("api/pricing/marcos/", MarcosListView.as_view(), name="marcos-list"),
    path("api/pricing/hojas/", HojasListView.as_view(), name="hojas-list"),
    path("api/pricing/interiores/", InterioresListView.as_view(), name="interiores-list"),
    path("api/pricing/vidrios/", VidriosListView.as_view(), name="vidrios-list"),
    path("api/pricing/perfiles/", PerfilesListView.as_view(), name="perfiles-list"),
    path("api/pricing/accesorios/", AccesoriosListView.as_view(), name="accesorios-list"),
    path("api/pricing/tratamientos/", TratamientosListView.as_view(), name="tratamientos-list"),
    path("api/pricing/mosquiteros/", MosquiterosListView.as_view(), name="mosquiteros-list"),
    path("api/pricing/contravidrios/", ContravidriosListView.as_view(), name="contravidrios-list"),
    path("api/pricing/contravidrios-exterior/", ContravidriosExteriorListView.as_view(), name="contravidrios-exterior-list"),
    path("api/pricing/cruces/", CrucesListView.as_view(), name="cruces-list"),
    path("api/pricing/vidrios-repartidos/", VidriosRepartidosListView.as_view(), name="vidrios-repartidos-list"),
    
    # Configuración ABMs
    path("config/extrusoras/", extrusoras_config, name="config-extrusoras"),
    path("config/lineas/", lineas_config, name="config-lineas"),
    path("config/productos/", productos_config, name="config-productos"),
    path("config/marcos/", marcos_config, name="config-marcos"),
    path("config/hojas/", hojas_config, name="config-hojas"),
    path("config/interiores/", interiores_config, name="config-interiores"),
    path("config/perfiles/", perfiles_config, name="config-perfiles"),
    path("config/accesorios/", accesorios_config, name="config-accesorios"),
    path("config/vidrios/", vidrios_config, name="config-vidrios"),
    path("config/tratamientos/", tratamientos_config, name="config-tratamientos"),
]
