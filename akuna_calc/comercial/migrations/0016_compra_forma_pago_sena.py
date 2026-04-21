from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comercial', '0015_add_usd_fields_to_pagoventa'),
    ]

    operations = [
        migrations.AddField(
            model_name='compra',
            name='forma_pago_sena',
            field=models.CharField(blank=True, choices=[('transferencia', 'Transferencia'), ('efectivo', 'Efectivo')], max_length=20, verbose_name='Forma de pago de la seña'),
        ),
    ]