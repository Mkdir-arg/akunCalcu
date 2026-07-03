from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agenda', '0005_add_tecnico'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventoagenda',
            name='numero_pedido',
            field=models.CharField(blank=True, max_length=50, verbose_name='Número de pedido'),
        ),
    ]
