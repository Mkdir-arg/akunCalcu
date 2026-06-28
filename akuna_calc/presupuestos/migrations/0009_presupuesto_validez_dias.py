from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('presupuestos', '0008_presupuesto_incluye_flete_colocacion'),
    ]

    operations = [
        migrations.AddField(
            model_name='presupuesto',
            name='validez_dias',
            field=models.PositiveIntegerField(default=30, verbose_name='Validez (días)'),
        ),
    ]
