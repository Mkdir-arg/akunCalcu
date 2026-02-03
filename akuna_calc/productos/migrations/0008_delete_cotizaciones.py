# Generated migration to remove Cotizacion and CotizacionItem models

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('productos', '0007_cotizacion_deleted_at'),
    ]

    operations = [
        migrations.DeleteModel(
            name='CotizacionItem',
        ),
        migrations.DeleteModel(
            name='Cotizacion',
        ),
    ]
