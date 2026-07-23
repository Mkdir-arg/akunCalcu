from django.urls import path
from . import views

app_name = 'security'

urlpatterns = [
    # Backups
    path('backups/', views.backup_login, name='backup_login'),
    path('backups/logout/', views.backup_logout, name='backup_logout'),
    path('backups/list/', views.backup_list, name='backup_list'),
    path('backups/create/', views.backup_create, name='backup_create'),
    path('backups/<int:pk>/download/', views.backup_download, name='backup_download'),
    path('backups/<int:pk>/delete/', views.backup_delete, name='backup_delete'),
    path('backups/settings/', views.backup_settings, name='backup_settings'),
    path('backups/api/create/', views.backup_api_create, name='backup_api_create'),
    path('backups/trigger-n8n/', views.backup_trigger_n8n, name='backup_trigger_n8n'),
    path('audit/', views.audit_list, name='audit_list'),
    path('fusionar/', views.fusionar, name='fusionar'),
]
