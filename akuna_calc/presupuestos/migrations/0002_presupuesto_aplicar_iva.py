# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('presupuestos', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='presupuesto',
            name='aplicar_iva',
            field=models.BooleanField(default=False, verbose_name='Aplicar IVA 21%'),
        ),
    ]
