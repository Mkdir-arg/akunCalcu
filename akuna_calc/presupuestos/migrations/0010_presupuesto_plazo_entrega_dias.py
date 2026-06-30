from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('presupuestos', '0009_presupuesto_validez_dias'),
    ]

    operations = [
        migrations.AddField(
            model_name='presupuesto',
            name='plazo_entrega_dias',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='Plazo de entrega (días)'),
        ),
    ]
