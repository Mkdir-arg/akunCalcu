# Generated manually

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('presupuestos', '0002_presupuesto_aplicar_iva'),
    ]

    operations = [
        migrations.AddField(
            model_name='presupuesto',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Fecha de eliminación'),
        ),
        migrations.AddField(
            model_name='presupuesto',
            name='deleted_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='presupuestos_eliminados', to=settings.AUTH_USER_MODEL, verbose_name='Eliminado por'),
        ),
    ]
