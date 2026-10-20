import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comercial', '0023_tipocuenta_caja_chica'),
        ('core', '0002_seed_provincias'),
    ]

    operations = [
        migrations.AddField(
            model_name='cliente',
            name='provincia',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='clientes', to='core.provincia', verbose_name='Provincia'),
        ),
    ]
