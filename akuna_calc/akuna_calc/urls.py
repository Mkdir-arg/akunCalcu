from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('productos/', include('productos.urls')),
    path('admin-usuarios/', include('usuarios.urls')),
    path('comercial/', include('comercial.urls')),
    path('facturacion/', include('facturacion.urls')),
    path('security/', include('security.urls')),  # Módulo de seguridad y backups
    path('plantillas/', include('plantillas.urls')),  # Plantillas de despiece
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)