"""URL routing for pricing app."""

from django.urls import path

from .views import PricingCalculateView, cotizador_view
from .catalog_views import (
    ExtrusorasListView, LineasListView, ProductosListView,
    MarcosListView, HojasListView, InterioresListView, VidriosListView,
    PerfilesListView, AccesoriosListView, TratamientosListView,
    MosquiterosListView, ContravidriosListView, ContravidriosExteriorListView,
    CrucesListView, VidriosRepartidosListView, OpcionalesListView
)
from .config_views import (
    extrusoras_config, lineas_config, productos_config, marcos_config,
    hojas_config, interiores_config, perfiles_config, accesorios_config,
    vidrios_config, tratamientos_config,
    extrusora_create, extrusora_edit, extrusora_delete,
    linea_create, linea_edit, linea_delete,
    producto_create, producto_edit, producto_delete,
    marco_create, marco_edit, marco_delete, marco_formulas_guardar,
    hoja_create, hoja_edit, hoja_delete,
    interior_create, interior_edit, interior_delete,
    perfil_create, perfil_edit, perfil_delete,
    accesorio_create, accesorio_edit, accesorio_delete,
    vidrio_create, vidrio_edit, vidrio_delete,
    tratamiento_create, tratamiento_edit, tratamiento_delete,
    api_get_producto, api_get_marco, api_get_hoja, api_get_extrusoras, api_get_perfiles,
)

urlpatterns = [
    # Cotizador
    path("cotizador/", cotizador_view, name="pricing-cotizador"),
    
    # API Endpoints
    path("api/pricing/calculate/", PricingCalculateView.as_view(), name="pricing-calculate"),
    path("api/producto/<int:pk>/", api_get_producto, name="api-get-producto"),
    path("api/marco/<int:pk>/", api_get_marco, name="api-get-marco"),
    path("api/hoja/<int:pk>/", api_get_hoja, name="api-get-hoja"),
    path("api/extrusoras/", api_get_extrusoras, name="api-get-extrusoras"),
    path("api/perfiles-simple/", api_get_perfiles, name="api-get-perfiles"),
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
    path("api/pricing/opcionales/", OpcionalesListView.as_view(), name="opcionales-list"),
    
    # Configuración ABMs — listas
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
    # Configuración ABMs — crear
    path("config/extrusoras/nueva/", extrusora_create, name="config-extrusora-create"),
    path("config/lineas/nueva/", linea_create, name="config-linea-create"),
    path("config/productos/nuevo/", producto_create, name="config-producto-create"),
    path("config/marcos/nuevo/", marco_create, name="config-marco-create"),
    path("config/hojas/nueva/", hoja_create, name="config-hoja-create"),
    path("config/interiores/nuevo/", interior_create, name="config-interior-create"),
    path("config/perfiles/nuevo/", perfil_create, name="config-perfil-create"),
    path("config/accesorios/nuevo/", accesorio_create, name="config-accesorio-create"),
    path("config/vidrios/nuevo/", vidrio_create, name="config-vidrio-create"),
    path("config/tratamientos/nuevo/", tratamiento_create, name="config-tratamiento-create"),
    # Configuración ABMs — editar
    path("config/extrusoras/<int:pk>/editar/", extrusora_edit, name="config-extrusora-edit"),
    path("config/lineas/<int:pk>/editar/", linea_edit, name="config-linea-edit"),
    path("config/productos/<int:pk>/editar/", producto_edit, name="config-producto-edit"),
    path("config/marcos/<int:pk>/editar/", marco_edit, name="config-marco-edit"),
    path("config/marcos/<int:pk>/formulas/guardar/", marco_formulas_guardar, name="config-marco-formulas-guardar"),
    path("config/hojas/<int:pk>/editar/", hoja_edit, name="config-hoja-edit"),
    path("config/interiores/<int:pk>/editar/", interior_edit, name="config-interior-edit"),
    path("config/perfiles/<str:pk>/editar/", perfil_edit, name="config-perfil-edit"),
    path("config/accesorios/<str:pk>/editar/", accesorio_edit, name="config-accesorio-edit"),
    path("config/vidrios/<str:pk>/editar/", vidrio_edit, name="config-vidrio-edit"),
    path("config/tratamientos/<int:pk>/editar/", tratamiento_edit, name="config-tratamiento-edit"),
    # Configuración ABMs — eliminar (lógico)
    path("config/extrusoras/<int:pk>/eliminar/", extrusora_delete, name="config-extrusora-delete"),
    path("config/lineas/<int:pk>/eliminar/", linea_delete, name="config-linea-delete"),
    path("config/productos/<int:pk>/eliminar/", producto_delete, name="config-producto-delete"),
    path("config/marcos/<int:pk>/eliminar/", marco_delete, name="config-marco-delete"),
    path("config/hojas/<int:pk>/eliminar/", hoja_delete, name="config-hoja-delete"),
    path("config/interiores/<int:pk>/eliminar/", interior_delete, name="config-interior-delete"),
    path("config/perfiles/<str:pk>/eliminar/", perfil_delete, name="config-perfil-delete"),
    path("config/accesorios/<str:pk>/eliminar/", accesorio_delete, name="config-accesorio-delete"),
    path("config/vidrios/<str:pk>/eliminar/", vidrio_delete, name="config-vidrio-delete"),
    path("config/tratamientos/<int:pk>/eliminar/", tratamiento_delete, name="config-tratamiento-delete"),
]
