from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comercial', '0022_venta_cotizacion_sena_usd_venta_cotizacion_usd_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tipocuenta',
            name='tipo',
            field=models.CharField(
                choices=[
                    ('colocadores', 'Colocadores'),
                    ('colaboradores', 'Colaboradores'),
                    ('fletes', 'Fletes'),
                    ('retiros_propios', 'Retiros Propios'),
                    ('varios', 'Varios'),
                    ('proveedores', 'Proveedores'),
                    ('caja_chica', 'Caja Chica'),
                ],
                max_length=20,
                unique=True,
            ),
        ),
    ]
