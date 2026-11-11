from django.contrib import admin

from .models import Resumen


@admin.register(Resumen)
class ResumenAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'periodo', 'hasta', 'created_at')
    list_filter = ('periodo',)
    readonly_fields = ('periodo', 'desde', 'hasta', 'datos', 'texto', 'abierto_por', 'created_at', 'updated_at')

    def has_add_permission(self, request):
        return False
