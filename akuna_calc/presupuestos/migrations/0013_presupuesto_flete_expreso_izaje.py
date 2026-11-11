from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('presupuestos', '0012_presupuesto_solicitud'),
    ]

    operations = [
        migrations.AddField(
            model_name='presupuesto',
            name='flete_expreso_caba',
            field=models.BooleanField(default=False, verbose_name='Flete expreso CABA'),
        ),
        migrations.AddField(
            model_name='presupuesto',
            name='no_incluye_izaje',
            field=models.BooleanField(default=False, verbose_name='No incluye izaje'),
        ),
    ]
